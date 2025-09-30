import cv2
import dlib
import numpy as np
import time
import queue
import sounddevice as sd
import vosk
import json
import random
import os
from imutils import face_utils
from word2number import w2n   # to handle "fifteen" -> 15


# =======================
# CAPTCHA VERIFICATION MODULE
# =======================
def mouth_captcha_verification(camera, vosk_model_path, dlib_model_path, duration=5, display=True):
    """
    Run mouth-movement + spoken captcha verification.
    Returns True if passed, False otherwise.
    """

    # -----------------------
    # Model Setup
    # -----------------------
    if not os.path.exists(vosk_model_path):
        raise FileNotFoundError(f"Vosk model not found at {vosk_model_path}")
    if not os.path.exists(dlib_model_path):
        raise FileNotFoundError(f"Dlib model not found at {dlib_model_path}")

    model = vosk.Model(vosk_model_path)
    q = queue.Queue()

    def audio_callback(indata, frames, time_, status):
        if status:
            print(status)
        q.put(bytes(indata))

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(dlib_model_path)

    # -----------------------
    # Generate Captcha
    # -----------------------
    a = random.randint(20, 90)
    b = random.randint(0, 10)
    op = random.choice(["+", "-"])

    if op == "+":
        answer = a + b
    else:
        answer = a - b

    if answer < 0:
        answer = abs(answer)
    if answer > 99:
        answer = answer % 100

    CAPTCHA_QUESTION = f"{a} {op} {b} = ?"
    CAPTCHA_ANSWER = str(answer)

    print("Captcha Question:", CAPTCHA_QUESTION)

    # -----------------------
    # Audio Stream
    # -----------------------
    device_info = sd.query_devices(kind="input")
    samplerate = int(device_info["default_samplerate"])
    rec = vosk.KaldiRecognizer(model, samplerate)
    stream = sd.InputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                            channels=1, callback=audio_callback)
    stream.start()

    start_time = time.time()
    mar_movement = []
    spoken_text = ""

    print(f"Please say your answer (you have {duration} seconds)...")

    # -----------------------
    # Main Loop
    # -----------------------
    while True:
        frame = camera.get_frame()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detector(gray, 0)
        for face in faces:
            shape = predictor(gray, face)
            shape = face_utils.shape_to_np(shape)
            mouth = shape[48:68]

            # Mouth Aspect Ratio (MAR)
            A = np.linalg.norm(mouth[2] - mouth[10])
            B = np.linalg.norm(mouth[4] - mouth[8])
            C = np.linalg.norm(mouth[0] - mouth[6])
            mar = (A + B) / (2.0 * C)
            mar_movement.append(mar)

            cv2.drawContours(frame, [cv2.convexHull(mouth)], -1, (0, 255, 0), 1)

        cv2.putText(frame, CAPTCHA_QUESTION, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        if display:
            cv2.imshow("Unified Verification", frame)

        # process speech
        try:
            data = q.get_nowait()
        except queue.Empty:
            data = None
        if data is not None:
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if result.get("text"):
                    spoken_text += " " + result["text"]

        if time.time() - start_time > duration:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # cleanup
    stream.stop()
    cv2.destroyAllWindows()

    # -----------------------
    # Decision
    # -----------------------
    avg_mar_change = np.std(mar_movement)
    print("\n===== CAPTCHA RESULT =====")
    print("Spoken Text:", spoken_text.strip())
    print("Expected Answer:", CAPTCHA_ANSWER)
    print("MAR variation:", avg_mar_change)

    recognized_number = None
    try:
        recognized_number = str(w2n.word_to_num(spoken_text.strip()))
    except:
        for token in spoken_text.split():
            if token.isdigit():
                recognized_number = token

    if avg_mar_change > 0.01 and recognized_number == CAPTCHA_ANSWER:
        print("Verification Passed (Mouth moved + Correct answer)")
        return True
    else:
        print("Verification Failed")
        return False