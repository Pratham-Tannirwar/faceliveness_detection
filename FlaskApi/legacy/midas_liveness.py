# miDAS + SolvePnP 5-second liveness check (final result shown & webcam closes)
# Requirements: pip install opencv-python torch torchvision mediapipe timm

import cv2
import numpy as np
import torch
import time
from collections import deque
import logging
import sys
import os

# Add current directory to path to avoid import conflicts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# -------- CONFIG (improved for better accuracy) --------

# Configure logging for systematic output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('liveness_detection.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)
DEPTH_MODEL_NAME   = "MiDaS_small"
FACE_MESH_STATIC   = False
MAX_TRACK_HISTORY  = 150          # store more frames for ~5s
DEPTH_STD_THRESH   = 3.0          # Reduced from 5.0 for better sensitivity
REPROJ_ERR_THRESH  = 12.0         # Increased from 8.0 for better tolerance
MOTION_VAR_THRESH  = 0.2          # Reduced from 0.4 for subtle movements
CHECK_DURATION     = 5.0          # seconds to confirm liveness
SHOW_WINDOWS       = True

# Additional parameters for improved detection
MIN_FACE_SIZE      = 100          # minimum face size in pixels
DEPTH_WINDOW_SIZE  = 5            # frames for depth smoothing
MOTION_WINDOW_SIZE = 10           # frames for motion smoothing
CONFIDENCE_THRESHOLD = 0.7        # confidence for final decision

# -------- Load MiDaS (depth) --------
device = "cuda" if torch.cuda.is_available() else "cpu"
midas = torch.hub.load("intel-isl/MiDaS", DEPTH_MODEL_NAME).to(device).eval()
transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
transform = transforms.small_transform if DEPTH_MODEL_NAME.endswith("small") else transforms.default_transform

# -------- MediaPipe FaceMesh --------
try:
    import mediapipe as mp
except ImportError:
    raise ImportError("mediapipe not installed. Run: pip install mediapipe")

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=FACE_MESH_STATIC,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# -------- 3D model points (for PnP) --------
MODEL_POINTS = np.array([
    (0.0,   0.0,    0.0),     # Nose tip
    (0.0, -63.6,  -12.5),     # Chin
    (-43.3, 32.7, -26.0),     # Left eye outer
    (43.3,  32.7, -26.0),     # Right eye outer
    (-28.9,-28.9, -24.1),     # Mouth left
    (28.9, -28.9, -24.1),     # Mouth right
], dtype=np.float32)

IDX_NOSE_TIP, IDX_CHIN, IDX_LEFT_EYE_O, IDX_RIGHT_EYE_O, IDX_MOUTH_L, IDX_MOUTH_R = 1, 152, 33, 263, 61, 291
SEL_IDX = [IDX_NOSE_TIP, IDX_CHIN, IDX_LEFT_EYE_O, IDX_RIGHT_EYE_O, IDX_MOUTH_L, IDX_MOUTH_R]

# -------- Utils --------
def rotationMatrixToEulerAngles(R):
    sy = np.sqrt(R[0,0]*R[0,0] + R[1,0]*R[1,0])
    singular = sy < 1e-6
    if not singular:
        x = np.arctan2(R[2,1], R[2,2])  # roll
        y = np.arctan2(-R[2,0], sy)     # pitch
        z = np.arctan2(R[1,0], R[0,0])  # yaw
    else:
        x = np.arctan2(-R[1,2], R[1,1])
        y = np.arctan2(-R[2,0], sy)
        z = 0
    return np.degrees([z, y, x])  # yaw, pitch, roll

def draw_axes(img, camera_matrix, dist_coeffs, rvec, tvec, length=60):
    axes = np.float32([[length,0,0], [0,length,0], [0,0,length]]).reshape(-1,3)
    origin = np.float32([[0,0,0]])
    imgpts, _ = cv2.projectPoints(np.vstack([origin, axes]), rvec, tvec, camera_matrix, dist_coeffs)
    o, x, y, z = [tuple(pt.ravel().astype(int)) for pt in imgpts]
    cv2.line(img, o, x, (0,0,255), 2)
    cv2.line(img, o, y, (0,255,0), 2)
    cv2.line(img, o, z, (255,0,0), 2)

# -------- History for 5-sec decision --------
yaw_hist, pitch_hist, roll_hist = deque(maxlen=MAX_TRACK_HISTORY), deque(maxlen=MAX_TRACK_HISTORY), deque(maxlen=MAX_TRACK_HISTORY)
live_votes = deque(maxlen=int(CHECK_DURATION*30))  # ~30fps * 5s
depth_history = deque(maxlen=DEPTH_WINDOW_SIZE)  # for depth smoothing
motion_history = deque(maxlen=MOTION_WINDOW_SIZE)  # for motion smoothing

def improved_depth_analysis(depth_roi, face_size):
    """Improved depth analysis with face size normalization"""
    if depth_roi.size == 0 or face_size < MIN_FACE_SIZE:
        return 0.0, 0.0
    
    # Normalize by face size to account for distance variations
    normalized_std = np.std(depth_roi) * (200.0 / face_size)  # normalize to reference size
    
    # Calculate depth range (max - min) for additional validation
    depth_range = np.max(depth_roi) - np.min(depth_roi)
    
    # Combine both metrics for better discrimination
    combined_score = normalized_std + (depth_range * 0.1)
    
    return combined_score, depth_range

def liveness_decision(depth_std_face, reproj_err, yaw, pitch, roll, depth_roi, face_size, 
                     depth_thresh=DEPTH_STD_THRESH, motion_thresh=MOTION_VAR_THRESH):
    """Enhanced liveness decision with confidence scoring and adaptive thresholds"""
    yaw_hist.append(yaw); pitch_hist.append(pitch); roll_hist.append(roll)
    
    # Improved motion detection with smoothing
    if len(yaw_hist) >= 3:
        # Calculate motion variance with recent history
        recent_yaw = list(yaw_hist)[-MOTION_WINDOW_SIZE:]
        recent_pitch = list(pitch_hist)[-MOTION_WINDOW_SIZE:]
        recent_roll = list(roll_hist)[-MOTION_WINDOW_SIZE:]
        
        motion_var = (np.var(recent_yaw) + np.var(recent_pitch) + np.var(recent_roll))
        motion_history.append(motion_var)
        
        # Use smoothed motion variance
        if len(motion_history) >= 3:
            motion_var = np.mean(list(motion_history))
    else:
        motion_var = 0.0
    
    # Improved depth analysis
    improved_depth, depth_range = improved_depth_analysis(depth_roi, face_size)
    depth_history.append(improved_depth)
    
    # Smooth depth values
    if len(depth_history) >= 3:
        smoothed_depth = np.mean(list(depth_history))
    else:
        smoothed_depth = improved_depth
    
    # Individual condition checks with adaptive thresholds
    cond_depth  = smoothed_depth > depth_thresh
    cond_pnp    = reproj_err < REPROJ_ERR_THRESH
    cond_motion = motion_var > motion_thresh
    
    # Confidence scoring (0-1 range)
    depth_conf = min(1.0, smoothed_depth / (depth_thresh * 2))
    pnp_conf = max(0.0, 1.0 - (reproj_err / REPROJ_ERR_THRESH))
    motion_conf = min(1.0, motion_var / (motion_thresh * 2))
    
    # Combined confidence score
    total_confidence = (depth_conf * 0.4 + pnp_conf * 0.3 + motion_conf * 0.3)
    
    # Final decision with confidence threshold
    is_live = (cond_depth and cond_pnp and cond_motion) and (total_confidence > CONFIDENCE_THRESHOLD)
    
    return is_live, cond_depth, cond_pnp, motion_var, total_confidence

# -------- Main (5-second verification) --------
def run_liveness_check_5s():
    logger.info("Initializing Face Liveness Detection System v2.0")
    logger.info("Loading MiDaS depth estimation model...")
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        logger.error("Webcam not accessible - please check camera connection")
        raise RuntimeError("Webcam not accessible.")

    logger.info("Webcam initialized successfully")
    logger.info(f"Detection parameters: Depth Threshold={DEPTH_STD_THRESH}, Motion Threshold={MOTION_VAR_THRESH}, Reproj Error Threshold={REPROJ_ERR_THRESH}")
    
    prev, fps, start_time = time.time(), 0.0, time.time()
    final_live = None
    last_frame_for_show = None

    logger.info("Starting 5-second liveness detection sequence...")

    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        h, w = frame.shape[:2]
        last_frame_for_show = frame.copy()

        # FPS calc
        now = time.time(); dt = now - prev; prev = now
        fps = (0.9*fps + 0.1*(1.0/dt)) if dt > 0 else fps

        # Depth (MiDaS) — correct call shape (no extra unsqueeze)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        inp = transform(rgb).to(device)                  # [1,3,H,W]
        with torch.no_grad():
            depth = midas(inp).squeeze().cpu().numpy()   # [H,W]
        depth_norm = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        depth_color = cv2.applyColorMap(depth_norm, cv2.COLORMAP_MAGMA)
        
        # Adaptive lighting analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Adjust thresholds based on lighting conditions
        adaptive_depth_thresh = DEPTH_STD_THRESH * (0.8 + 0.4 * (brightness / 128.0))
        adaptive_motion_thresh = MOTION_VAR_THRESH * (0.7 + 0.6 * (contrast / 64.0))

        # Landmarks (MediaPipe) - Enhanced face detection
        results = face_mesh.process(rgb)
        depth_std_face, reproj_err, yaw, pitch, roll = 0.0, 1e9, 0.0, 0.0, 0.0
        depth_roi = np.array([])
        face_size = 0

        if results.multi_face_landmarks:
            logger.debug("Face detected - processing landmarks")
            lm = results.multi_face_landmarks[0].landmark
            pts_2d = np.array([[int(lm[idx].x*w), int(lm[idx].y*h)] for idx in SEL_IDX], dtype=np.float32)

            cam_mat = np.array([[w,0,w/2],[0,w,h/2],[0,0,1]], dtype=np.float32)
            dist = np.zeros((4,1), dtype=np.float32)
            success, rvec, tvec = cv2.solvePnP(MODEL_POINTS, pts_2d, cam_mat, dist, flags=cv2.SOLVEPNP_ITERATIVE)
            if success:
                proj, _ = cv2.projectPoints(MODEL_POINTS, rvec, tvec, cam_mat, dist)
                reproj_err = float(np.linalg.norm(proj.reshape(-1,2) - pts_2d, axis=1).mean())
                R, _ = cv2.Rodrigues(rvec)
                yaw, pitch, roll = rotationMatrixToEulerAngles(R)
                draw_axes(frame, cam_mat, dist, rvec, tvec, 70)

            # Enhanced face region detection
            xs, ys = [int(l.x*w) for l in lm], [int(l.y*h) for l in lm]
            x1,y1 = max(min(xs)-20,0), max(min(ys)-20,0)  # Increased margin
            x2,y2 = min(max(xs)+20,w-1), min(max(ys)+20,h-1)
            
            # Calculate face size for normalization
            face_size = max(x2-x1, y2-y1)
            
            # Extract depth ROI with better region selection
            if face_size >= MIN_FACE_SIZE:
                # Focus on central face area (more reliable for depth)
                center_x, center_y = (x1+x2)//2, (y1+y2)//2
                roi_size = min(face_size//2, min(w,h)//4)
                roi_x1 = max(center_x - roi_size//2, 0)
                roi_y1 = max(center_y - roi_size//2, 0)
                roi_x2 = min(center_x + roi_size//2, w-1)
                roi_y2 = min(center_y + roi_size//2, h-1)
                
                depth_roi = depth[roi_y1:roi_y2, roi_x1:roi_x2]
                if depth_roi.size > 0:
                    depth_std_face = float(np.std(depth_roi))
                
                # Draw enhanced face region
                cv2.rectangle(frame, (roi_x1, roi_y1), (roi_x2, roi_y2), (255,100,100), 2)
            else:
                # Fallback to basic region if face too small
                roi = depth[y1:y2, x1:x2]
                if roi.size > 0:
                    depth_std_face = float(np.std(roi))
                depth_roi = roi

            for (x,y) in pts_2d.astype(int):
                cv2.circle(frame, (x,y), 2, (0,255,255), -1)
            cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,0), 1)

        # Decision vote with improved function and adaptive thresholds
        live, ok_depth, ok_pnp, motion_var, confidence = liveness_decision(
            depth_std_face, reproj_err, yaw, pitch, roll, depth_roi, face_size,
            depth_thresh=adaptive_depth_thresh, motion_thresh=adaptive_motion_thresh
        )
        live_votes.append(live)
        
        # Detailed frame analysis logging (every 30 frames ~1 second)
        if len(live_votes) % 30 == 0 and results.multi_face_landmarks:
            logger.debug(f"Frame {len(live_votes)}: Face={face_size}px, Depth={depth_std_face:.2f}, "
                        f"Motion={motion_var:.2f}, Reproj={reproj_err:.1f}, "
                        f"Light={brightness:.0f}, Live={live}, Conf={confidence:.2f}")

        elapsed = time.time() - start_time
        
        # Progress logging every second
        if int(elapsed) > int(elapsed - dt) and int(elapsed) <= CHECK_DURATION:
            logger.info(f"Progress: {int(elapsed)}/{int(CHECK_DURATION)} seconds - Current votes: {sum(live_votes)}/{len(live_votes)}")
        
        # Decide after exactly CHECK_DURATION seconds
        if elapsed >= CHECK_DURATION and final_live is None:
            if len(live_votes) == 0:
                final_live = False
                logger.warning("No valid frames collected - marking as spoof")
            else:
                final_live = (sum(live_votes) / len(live_votes)) > 0.6
                logger.info(f"Analysis complete - Live vote ratio: {sum(live_votes)}/{len(live_votes)} ({(sum(live_votes)/len(live_votes)*100):.1f}%)")

        # Enhanced HUD with confidence and face size
        status = "CHECKING " if final_live is None else ("LIVE" if final_live else "SPOOF ")
        color  = (0,255,255) if final_live is None else ((0,255,0) if final_live else (0,0,255))
        cv2.putText(frame, status, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv2.putText(frame, f"FPS: {fps:5.1f}", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        cv2.putText(frame, f"Face Size: {face_size}px", (10,85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)
        cv2.putText(frame, f"Light: {brightness:.0f} Cont: {contrast:.0f}", (10,110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)
        cv2.putText(frame, f"DepthStd: {depth_std_face:5.2f} ({'OK' if depth_std_face>adaptive_depth_thresh else 'LOW'})", (10,135),  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)
        cv2.putText(frame, f"ReprojErr: {reproj_err:5.2f}px ({'OK' if reproj_err<REPROJ_ERR_THRESH else 'HIGH'})", (10,160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)
        cv2.putText(frame, f"Yaw/Pitch/Roll: {yaw:5.1f}/{pitch:5.1f}/{roll:5.1f}", (10,185), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)
        cv2.putText(frame, f"MotionVar: {motion_var:4.2f} (thr: {adaptive_motion_thresh:.2f})", (10,210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)
        cv2.putText(frame, f"Confidence: {confidence:.2f}", (10,235), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        if SHOW_WINDOWS:
            cv2.imshow("Liveness: MiDaS + PnP", frame)
            cv2.imshow("Depth Map", depth_color)

        # Stop immediately once decision made & one frame displayed with final label
        if final_live is not None:
            last_frame_for_show = frame.copy()
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            final_live = False
            break

    # Show final result briefly, then clean up
    if SHOW_WINDOWS and last_frame_for_show is not None:
        final_text = "LIVE" if final_live else "SPOOF"
        final_color = (0,255,0) if final_live else (0,0,255)
        cv2.putText(last_frame_for_show, f"FINAL: {final_text}", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, final_color, 3)
        cv2.imshow("Liveness: MiDaS + PnP (FINAL)", last_frame_for_show)
        cv2.waitKey(1200)  # show for ~1.2s

    cap.release()
    face_mesh.close()
    cv2.destroyAllWindows()
    
    total_elapsed = time.time() - start_time
    
    # Get final confidence from last frame
    final_confidence = confidence if 'confidence' in locals() else 0.0
    
    # Print systematic summary
    logger.info("="*60)
    logger.info("FACE LIVENESS DETECTION SUMMARY")
    logger.info("="*60)
    
    if final_live is not None:
        result = "LIVE PERSON DETECTED" if final_live else "SPOOF ATTEMPT DETECTED"
        status = "SUCCESS" if final_live else "ALERT"
        
        logger.info(f"Detection Result: {result}")
        logger.info(f"Status: {status}")
        logger.info(f"Confidence Level: {final_confidence:.2f}/1.00 ({final_confidence*100:.1f}%)")
        logger.info(f"Analysis Duration: {total_elapsed:.1f} seconds")
        logger.info(f"Frames Processed: {len(live_votes)}")
        logger.info(f"Live Vote Ratio: {sum(live_votes)}/{len(live_votes)} ({(sum(live_votes)/len(live_votes)*100):.1f}%)")
        
        logger.info("-" * 40)
        logger.info("Thresholds Used:")
        logger.info(f"  Depth Standard Deviation: >{DEPTH_STD_THRESH:.1f}")
        logger.info(f"  Motion Variance: >{MOTION_VAR_THRESH:.2f}")
        logger.info(f"  Reprojection Error: <{REPROJ_ERR_THRESH:.1f}")
        logger.info(f"  Confidence Threshold: >{CONFIDENCE_THRESHOLD:.2f}")
        
        logger.info("-" * 40)
        logger.info("Detection Criteria:")
        logger.info("  [+] Depth variation analysis (MiDaS)")
        logger.info("  [+] Head pose estimation (SolvePnP)")
        logger.info("  [+] Motion variance tracking")
        logger.info("  [+] Adaptive lighting compensation")
        logger.info("  [+] Confidence scoring system")
        
        logger.info("="*60)
    else:
        logger.warning("Detection incomplete - insufficient data collected")
        logger.info("="*60)
    
    logger.info("Detection complete - Results saved to liveness_detection.log")
    
    return final_live if final_live is not None else False

if __name__ == "__main__":
    result = run_liveness_check_5s()
    print(f"Liveness check result: {'LIVE' if result else 'SPOOF'}")