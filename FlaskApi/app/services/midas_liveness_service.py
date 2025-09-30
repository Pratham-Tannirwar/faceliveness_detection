"""
MiDaS Liveness Service - Wrapper for 2D/3D liveness detection functionality
"""

import cv2
import numpy as np
import logging
import os
import sys
import time
from typing import Dict, Any
from collections import deque

# Add the flask-api directory to the path to import existing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
flask_api_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, flask_api_dir)

logger = logging.getLogger(__name__)

class MidasLivenessService:
    """Service for 2D/3D liveness detection using MiDaS depth estimation"""
    
    def __init__(self):
        self.model_loaded = False
        self.midas = None
        self.transforms = None
        self.transform = None
        self.face_mesh = None
        self.device = None
        self._load_models()
    
    def _load_models(self):
        """Load MiDaS and MediaPipe models"""
        try:
            import torch
            import mediapipe as mp
            
            # MiDaS configuration
            DEPTH_MODEL_NAME = "MiDaS_small"
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load MiDaS model
            self.midas = torch.hub.load("intel-isl/MiDaS", DEPTH_MODEL_NAME).to(self.device).eval()
            self.transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            self.transform = self.transforms.small_transform if DEPTH_MODEL_NAME.endswith("small") else self.transforms.default_transform
            
            # Load MediaPipe FaceMesh
            mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            
            self.model_loaded = True
            logger.info("MiDaS and MediaPipe models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load MiDaS/MediaPipe models: {e}")
            self.model_loaded = False
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model_loaded
    
    def rotation_matrix_to_euler_angles(self, R):
        """Convert rotation matrix to Euler angles"""
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
    
    def draw_axes(self, img, camera_matrix, dist_coeffs, rvec, tvec, length=60):
        """Draw 3D axes on image"""
        axes = np.float32([[length,0,0], [0,length,0], [0,0,length]]).reshape(-1,3)
        origin = np.float32([[0,0,0]])
        imgpts, _ = cv2.projectPoints(np.vstack([origin, axes]), rvec, tvec, camera_matrix, dist_coeffs)
        o, x, y, z = [tuple(pt.ravel().astype(int)) for pt in imgpts]
        cv2.line(img, o, x, (0,0,255), 2)
        cv2.line(img, o, y, (0,255,0), 2)
        cv2.line(img, o, z, (255,0,0), 2)
    
    def improved_depth_analysis(self, depth_roi, face_size):
        """Improved depth analysis with face size normalization"""
        if depth_roi.size == 0 or face_size < 100:  # MIN_FACE_SIZE
            return 0.0, 0.0
        
        # Normalize by face size to account for distance variations
        normalized_std = np.std(depth_roi) * (200.0 / face_size)  # normalize to reference size
        
        # Calculate depth range (max - min) for additional validation
        depth_range = np.max(depth_roi) - np.min(depth_roi)
        
        # Combine both metrics for better discrimination
        combined_score = normalized_std + (depth_range * 0.1)
        
        return combined_score, depth_range
    
    def liveness_decision(self, depth_std_face, reproj_err, yaw, pitch, roll, depth_roi, face_size, 
                         depth_thresh=3.0, motion_thresh=0.2):
        """Enhanced liveness decision with confidence scoring"""
        # Individual condition checks
        cond_depth = depth_std_face > depth_thresh
        cond_pnp = reproj_err < 12.0  # REPROJ_ERR_THRESH
        cond_motion = True  # Simplified for API mode
        
        # Confidence scoring (0-1 range)
        depth_conf = min(1.0, depth_std_face / (depth_thresh * 2))
        pnp_conf = max(0.0, 1.0 - (reproj_err / 12.0))
        motion_conf = 0.5  # Default motion confidence for API mode
        
        # Combined confidence score
        total_confidence = (depth_conf * 0.4 + pnp_conf * 0.3 + motion_conf * 0.3)
        
        # Final decision with confidence threshold
        is_live = (cond_depth and cond_pnp) and (total_confidence > 0.7)
        
        return is_live, cond_depth, cond_pnp, total_confidence
    
    def run_liveness_check(self, camera, duration: int = 5, display: bool = False) -> Dict[str, Any]:
        """
        Run 2D/3D liveness check using MiDaS depth estimation and head pose analysis
        
        Args:
            camera: Camera object with get_frame() method
            duration: Duration to run check in seconds
            display: Whether to show visual feedback
            
        Returns:
            Dict containing liveness check results
        """
        if not self.model_loaded:
            return {
                'success': False,
                'confidence': 0.0,
                'message': 'MiDaS/MediaPipe models not loaded',
                'error': 'Models not available'
            }
        
        try:
            # 3D model points (for PnP)
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
            
            # History for decision
            live_votes = deque(maxlen=int(duration * 30))  # ~30fps * duration
            depth_history = deque(maxlen=5)  # for depth smoothing
            motion_history = deque(maxlen=10)  # for motion smoothing
            
            start_time = time.time()
            frame_count = 0
            confidence_scores = []
            
            logger.info(f"Starting {duration}-second 2D/3D liveness check...")
            
            while time.time() - start_time < duration:
                frame = camera.get_frame()
                if frame is None:
                    continue
                
                frame_count += 1
                h, w = frame.shape[:2]
                
                # Depth estimation (MiDaS)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                inp = self.transform(rgb).to(self.device)
                
                with torch.no_grad():
                    depth = self.midas(inp).squeeze().cpu().numpy()
                
                depth_norm = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                depth_color = cv2.applyColorMap(depth_norm, cv2.COLORMAP_MAGMA)
                
                # Adaptive lighting analysis
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = np.mean(gray)
                contrast = np.std(gray)
                
                # Adjust thresholds based on lighting conditions
                adaptive_depth_thresh = 3.0 * (0.8 + 0.4 * (brightness / 128.0))
                
                # Landmarks (MediaPipe)
                results = self.face_mesh.process(rgb)
                depth_std_face, reproj_err, yaw, pitch, roll = 0.0, 1e9, 0.0, 0.0, 0.0
                depth_roi = np.array([])
                face_size = 0

                if results.multi_face_landmarks:
                    lm = results.multi_face_landmarks[0].landmark
                    pts_2d = np.array([[int(lm[idx].x*w), int(lm[idx].y*h)] for idx in SEL_IDX], dtype=np.float32)

                    cam_mat = np.array([[w,0,w/2],[0,w,h/2],[0,0,1]], dtype=np.float32)
                    dist = np.zeros((4,1), dtype=np.float32)
                    success, rvec, tvec = cv2.solvePnP(MODEL_POINTS, pts_2d, cam_mat, dist, flags=cv2.SOLVEPNP_ITERATIVE)
                    
                    if success:
                        proj, _ = cv2.projectPoints(MODEL_POINTS, rvec, tvec, cam_mat, dist)
                        reproj_err = float(np.linalg.norm(proj.reshape(-1,2) - pts_2d, axis=1).mean())
                        R, _ = cv2.Rodrigues(rvec)
                        yaw, pitch, roll = self.rotation_matrix_to_euler_angles(R)
                        
                        if display:
                            self.draw_axes(frame, cam_mat, dist, rvec, tvec, 70)

                    # Enhanced face region detection
                    xs, ys = [int(l.x*w) for l in lm], [int(l.y*h) for l in lm]
                    x1,y1 = max(min(xs)-20,0), max(min(ys)-20,0)
                    x2,y2 = min(max(xs)+20,w-1), min(max(ys)+20,h-1)
                    
                    face_size = max(x2-x1, y2-y1)
                    
                    # Extract depth ROI
                    if face_size >= 100:  # MIN_FACE_SIZE
                        center_x, center_y = (x1+x2)//2, (y1+y2)//2
                        roi_size = min(face_size//2, min(w,h)//4)
                        roi_x1 = max(center_x - roi_size//2, 0)
                        roi_y1 = max(center_y - roi_size//2, 0)
                        roi_x2 = min(center_x + roi_size//2, w-1)
                        roi_y2 = min(center_y + roi_size//2, h-1)
                        
                        depth_roi = depth[roi_y1:roi_y2, roi_x1:roi_x2]
                        if depth_roi.size > 0:
                            depth_std_face = float(np.std(depth_roi))
                        
                        if display:
                            cv2.rectangle(frame, (roi_x1, roi_y1), (roi_x2, roi_y2), (255,100,100), 2)
                    else:
                        roi = depth[y1:y2, x1:x2]
                        if roi.size > 0:
                            depth_std_face = float(np.std(roi))
                        depth_roi = roi

                    if display:
                        for (x,y) in pts_2d.astype(int):
                            cv2.circle(frame, (x,y), 2, (0,255,255), -1)
                        cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,0), 1)

                # Decision vote
                live, ok_depth, ok_pnp, confidence = self.liveness_decision(
                    depth_std_face, reproj_err, yaw, pitch, roll, depth_roi, face_size,
                    depth_thresh=adaptive_depth_thresh
                )
                live_votes.append(live)
                confidence_scores.append(confidence)
                
                if display:
                    status = "CHECKING ⏳" if len(live_votes) < 30 else ("LIVE ✅" if live else "SPOOF ❌")
                    color = (0,255,255) if len(live_votes) < 30 else ((0,255,0) if live else (0,0,255))
                    cv2.putText(frame, status, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                    cv2.putText(frame, f"DepthStd: {depth_std_face:.2f}", (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)
                    cv2.putText(frame, f"ReprojErr: {reproj_err:.2f}px", (10,85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)
                    cv2.putText(frame, f"Confidence: {confidence:.2f}", (10,110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
                    
                    cv2.imshow("Liveness: MiDaS + PnP", frame)
                    cv2.imshow("Depth Map", depth_color)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            if display:
                cv2.destroyAllWindows()
            
            # Calculate final results
            if len(live_votes) == 0:
                final_live = False
                final_confidence = 0.0
            else:
                final_live = (sum(live_votes) / len(live_votes)) > 0.6
                final_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
            
            logger.info(f"2D/3D liveness check completed - Live vote ratio: {sum(live_votes)}/{len(live_votes)} ({(sum(live_votes)/len(live_votes)*100):.1f}%)")
            
            return {
                'success': final_live,
                'confidence': float(final_confidence),
                'live_votes': sum(live_votes),
                'total_votes': len(live_votes),
                'frames_processed': frame_count,
                'avg_depth_std': float(np.mean([d for d in [depth_std_face] if d > 0])) if 'depth_std_face' in locals() else 0.0,
                'avg_reproj_err': float(np.mean([r for r in [reproj_err] if r < 1e8])) if 'reproj_err' in locals() else 0.0,
                'message': '2D/3D liveness check completed successfully' if final_live else '2D/3D liveness check failed'
            }
            
        except Exception as e:
            logger.error(f"2D/3D liveness check failed: {e}")
            return {
                'success': False,
                'confidence': 0.0,
                'message': f'2D/3D liveness check failed: {str(e)}',
                'error': str(e)
            }
