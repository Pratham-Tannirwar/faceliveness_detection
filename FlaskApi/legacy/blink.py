import cv2
import dlib
import bz2
import os
import urllib.request
import numpy as np
import time
from scipy.spatial import distance as dist
from imutils import face_utils


def eye_aspect_ratio(eye):
    """Compute EAR for one eye"""
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)


def get_gaze_ratio(eye_points, facial_landmarks, gray):
    """Compute gaze ratio (left/right)"""
    eye_region = np.array([(facial_landmarks.part(point).x, facial_landmarks.part(point).y)
                           for point in eye_points])
    min_x = np.min(eye_region[:, 0])
    max_x = np.max(eye_region[:, 0])
    min_y = np.min(eye_region[:, 1])
    max_y = np.max(eye_region[:, 1])

    gray_eye = gray[min_y:max_y, min_x:max_x]
    _, threshold_eye = cv2.threshold(gray_eye, 70, 255, cv2.THRESH_BINARY)

    height, width = threshold_eye.shape
    left_side = threshold_eye[:, 0:int(width / 2)]
    right_side = threshold_eye[:, int(width / 2):width]

    left_white = cv2.countNonZero(left_side)
    right_white = cv2.countNonZero(right_side)

    if right_white == 0:
        gaze_ratio = 1
    elif left_white == 0:
        gaze_ratio = 5
    else:
        gaze_ratio = left_white / right_white
    return gaze_ratio


def blink(camera, duration=4, display=True):
    """
    Detects natural blinks and gaze movements for liveness.
    Returns True if liveness cues are found, else False.
    """

    # -----------------------
    # Download predictor if missing
    # -----------------------
    predictor_path = "shape_predictor_68_face_landmarks.dat"
    if not os.path.exists(predictor_path):
        print("⬇ Downloading facial landmark predictor...")
        url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
        urllib.request.urlretrieve(url, "sp.dat.bz2")
        with bz2.open("sp.dat.bz2") as f_in, open(predictor_path, "wb") as f_out:
            f_out.write(f_in.read())
        os.remove("sp.dat.bz2")
        print("shape_predictor_68_face_landmarks.dat downloaded")

    # -----------------------
    # Setup dlib
    # -----------------------
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    # -----------------------
    # Thresholds
    # -----------------------
    EYE_AR_THRESH = 0.22
    EYE_AR_CONSEC_FRAMES = 2

    COUNTER = 0
    TOTAL_BLINKS = 0
    GAZE_MOVEMENTS = 0

    start_time = time.time()

    # -----------------------
    # Main loop
    # -----------------------
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 0)

        for rect in rects:
            shape = predictor(gray, rect)
            shape_np = face_utils.shape_to_np(shape)

            leftEye = shape_np[lStart:lEnd]
            rightEye = shape_np[rStart:rEnd]
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0

            # Blink detection
            if ear < EYE_AR_THRESH:
                COUNTER += 1
            else:
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    TOTAL_BLINKS += 1
                COUNTER = 0

            # Draw eyes
            cv2.drawContours(frame, [cv2.convexHull(leftEye)], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [cv2.convexHull(rightEye)], -1, (0, 255, 0), 1)

            # -----------------------
            # Gaze movement
            # -----------------------
            gaze_left = get_gaze_ratio([36, 37, 38, 39, 40, 41], shape, gray)
            gaze_right = get_gaze_ratio([42, 43, 44, 45, 46, 47], shape, gray)
            gaze_avg = (gaze_left + gaze_right) / 2

            if gaze_avg <= 0.8 or gaze_avg >= 1.5:
                GAZE_MOVEMENTS += 1

            # Overlay info
            cv2.putText(frame, f"Blinks: {TOTAL_BLINKS}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Gaze Movements: {GAZE_MOVEMENTS}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.putText(frame, f"EAR: {ear:.2f}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Display
        if display:
            cv2.imshow("Blink + Gaze Liveness", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        # Stop after duration
        if time.time() - start_time > duration:
            break

    # -----------------------
    # Cleanup
    # -----------------------
    if display:
        cv2.destroyAllWindows()

    # -----------------------
    # Decision
    # -----------------------
    if TOTAL_BLINKS >= 1 and GAZE_MOVEMENTS >= 2:
        return True
    else:
        return False