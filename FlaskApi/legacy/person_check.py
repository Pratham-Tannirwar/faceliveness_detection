import cv2
import time
import insightface
import numpy as np

# Load ArcFace model once (global)
MODEL_NAME = "buffalo_l"
face_app = insightface.app.FaceAnalysis(name=MODEL_NAME, providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))


class PersonVerificationAndMonitor:
    def __init__(self, reference_image_path):
        # Load reference embedding
        ref_img = cv2.imread(reference_image_path)
        if ref_img is None:
            raise ValueError(f"Reference image not found: {reference_image_path}")

        ref_faces = face_app.get(ref_img)
        if len(ref_faces) != 1:
            raise ValueError("Reference image must contain exactly ONE face")

        self.ref_emb = ref_faces[0].embedding / np.linalg.norm(ref_faces[0].embedding)

    def verify_face(self, frame):
        """Return True if same person, False otherwise"""
        faces = face_app.get(frame)
        if len(faces) != 1:
            return None   # either 0 or >1 faces

        test_emb = faces[0].embedding / np.linalg.norm(faces[0].embedding)
        sim = np.dot(self.ref_emb, test_emb)
        return sim > 0.5  # threshold for same person

    def run(self, camera, duration=2, display=False):
        """
        Run verification for duration seconds
        - Exit if wrong person OR multiple faces
        - Continue otherwise
        """
        start_time = time.time()
        verified = False
        frame_out = None

        while time.time() - start_time < duration:
            frame = camera.get_frame()
            frame_out = frame.copy()

            result = self.verify_face(frame)

            if result is None:
                cv2.putText(frame_out, "❌ Wrong number of faces", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                return False, frame_out

            if result:
                verified = True
                cv2.putText(frame_out, "Same person", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            else:
                cv2.putText(frame_out, "Wrong person", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                return False, frame_out

            if display:
                cv2.imshow("Verification", frame_out)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        return verified, frame_out