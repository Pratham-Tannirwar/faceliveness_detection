"""
Mouth Captcha Service - Wrapper for voice captcha verification functionality
"""

import cv2
import numpy as np
import logging
import os
import sys
import time
import queue
import json
import random
from typing import Dict, Any

# Add the flask-api directory to the path to import existing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
flask_api_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, flask_api_dir)

logger = logging.getLogger(__name__)

class MouthCaptchaService:
    """Service for mouth movement and voice captcha verification"""
    
    def __init__(self):
        self.model_loaded = False
        self.detector = None
        self.predictor = None
        self.vosk_model = None
        self._load_models()
    
    def _load_models(self):
        """Load required models for mouth captcha verification"""
        try:
            import dlib
            import vosk
            import sounddevice as sd
            from imutils import face_utils
            from word2number import w2n
            
            # Check for dlib model
            dlib_model_path = os.path.join(flask_api_dir, "models", "shape_predictor_68_face_landmarks.dat")
            if not os.path.exists(dlib_model_path):
                logger.warning("Dlib facial landmark model not found")
                return
            
            # Check for Vosk model
            vosk_model_path = os.path.join(flask_api_dir, "models", "vosk-model-small-en-us-0.15")
            if not os.path.exists(vosk_model_path):
                logger.warning("Vosk speech recognition model not found")
                return
            
            # Load models
            self.detector = dlib.get_frontal_face_detector()
            self.predictor = dlib.shape_predictor(dlib_model_path)
            self.vosk_model = vosk.Model(vosk_model_path)
            self.face_utils = face_utils
            self.w2n = w2n
            self.sd = sd
            self.vosk = vosk
            
            self.model_loaded = True
            logger.info("Mouth captcha models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load mouth captcha models: {e}")
            self.model_loaded = False
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model_loaded
    
    def run_captcha_verification(self, camera, duration: int = 7, display: bool = False) -> Dict[str, Any]:
        """
        Run mouth-movement + spoken captcha verification
        
        Args:
            camera: Camera object with get_frame() method
            duration: Duration to run verification in seconds
            display: Whether to show visual feedback
            
        Returns:
            Dict containing verification results
        """
        if not self.model_loaded:
            return {
                'success': False,
                'confidence': 0.0,
                'message': 'Mouth captcha models not loaded',
                'error': 'Models not available'
            }
        
        try:
            # Generate captcha question
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

            captcha_question = f"{a} {op} {b} = ?"
            captcha_answer = str(answer)
            
            logger.info(f"Generated captcha: {captcha_question} (Answer: {captcha_answer})")
            
            # Setup audio stream
            q = queue.Queue()
            
            def audio_callback(indata, frames, time_, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                q.put(bytes(indata))
            
            device_info = self.sd.query_devices(kind="input")
            samplerate = int(device_info["default_samplerate"])
            rec = self.vosk.KaldiRecognizer(self.vosk_model, samplerate)
            stream = self.sd.InputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                                        channels=1, callback=audio_callback)
            stream.start()
            
            start_time = time.time()
            mar_movement = []
            spoken_text = ""
            frame_count = 0
            
            logger.info(f"Starting captcha verification for {duration} seconds...")
            
            # Main loop
            while time.time() - start_time < duration:
                frame = camera.get_frame()
                if frame is None:
                    continue
                
                frame_count += 1
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                faces = self.detector(gray, 0)
                for face in faces:
                    shape = self.predictor(gray, face)
                    shape = self.face_utils.shape_to_np(shape)
                    mouth = shape[48:68]

                    # Mouth Aspect Ratio (MAR)
                    A = np.linalg.norm(mouth[2] - mouth[10])
                    B = np.linalg.norm(mouth[4] - mouth[8])
                    C = np.linalg.norm(mouth[0] - mouth[6])
                    mar = (A + B) / (2.0 * C)
                    mar_movement.append(mar)

                    if display:
                        cv2.drawContours(frame, [cv2.convexHull(mouth)], -1, (0, 255, 0), 1)

                if display:
                    cv2.putText(frame, captcha_question, (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    cv2.imshow("Unified Verification", frame)

                # Process speech
                try:
                    data = q.get_nowait()
                except queue.Empty:
                    data = None
                
                if data is not None:
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        if result.get("text"):
                            spoken_text += " " + result["text"]

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Cleanup
            stream.stop()
            if display:
                cv2.destroyAllWindows()
            
            # Analyze results
            avg_mar_change = np.std(mar_movement) if mar_movement else 0.0
            spoken_text = spoken_text.strip()
            
            logger.info(f"Captcha results - Spoken: '{spoken_text}', Expected: '{captcha_answer}', MAR variation: {avg_mar_change:.4f}")
            
            # Try to extract number from spoken text
            recognized_number = None
            try:
                recognized_number = str(self.w2n.word_to_num(spoken_text))
            except:
                for token in spoken_text.split():
                    if token.isdigit():
                        recognized_number = token
                        break
            
            # Calculate confidence
            mar_score = min(1.0, avg_mar_change / 0.02)  # Normalize MAR variation
            answer_score = 1.0 if recognized_number == captcha_answer else 0.0
            confidence = (mar_score + answer_score) / 2.0
            
            # Success criteria
            success = avg_mar_change > 0.01 and recognized_number == captcha_answer
            
            return {
                'success': success,
                'confidence': float(confidence),
                'question': captcha_question,
                'answer': captcha_answer,
                'spoken_text': spoken_text,
                'recognized_number': recognized_number,
                'mar_variation': float(avg_mar_change),
                'frames_processed': frame_count,
                'message': 'Voice captcha verification completed successfully' if success else 'Voice captcha verification failed'
            }
            
        except Exception as e:
            logger.error(f"Mouth captcha verification failed: {e}")
            return {
                'success': False,
                'confidence': 0.0,
                'message': f'Mouth captcha verification failed: {str(e)}',
                'error': str(e)
            }

    def verify_uploaded_audio(self, audio_bytes: bytes, expression: str | None = None) -> Dict[str, Any]:
        """
        Verify mouth captcha using uploaded audio only. If expression is provided, use its answer; otherwise,
        generate a captcha expression just to compare spoken number presence.
        """
        if not self.model_loaded:
            return {
                'success': False,
                'confidence': 0.0,
                'message': 'Mouth captcha models not loaded',
                'error': 'Models not available'
            }

        try:
            # Determine expected answer
            if expression:
                try:
                    tokens = expression.replace('=', '').split()
                    a = int(tokens[0])
                    op = tokens[1]
                    b = int(tokens[2])
                    answer = a + b if op == '+' else a - b
                except Exception:
                    answer = None
            else:
                # Fallback: random answer just to check recognition quality
                a = random.randint(10, 99)
                b = random.randint(1, 9)
                op = random.choice(['+', '-'])
                answer = a + b if op == '+' else a - b
                expression = f"{a} {op} {b}"

            expected = str(abs(answer)) if answer is not None else None

            # Recognize speech with Vosk from audio bytes
            import soundfile as sf
            import io

            audio_io = io.BytesIO(audio_bytes)
            data, samplerate = sf.read(audio_io, dtype='int16')
            rec = self.vosk.KaldiRecognizer(self.vosk_model, samplerate)

            spoken_text = ""
            if len(data.shape) > 1:
                # Take mono channel
                data = data[:, 0]

            chunk_size = 4000
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                rec.AcceptWaveform(chunk.tobytes())
                partial = json.loads(rec.PartialResult()).get('partial')
                if partial:
                    spoken_text += ' ' + partial

            final = json.loads(rec.FinalResult()).get('text', '')
            spoken_text = (spoken_text + ' ' + final).strip()

            # Extract recognized number
            recognized_number = None
            try:
                recognized_number = str(self.w2n.word_to_num(spoken_text))
            except:
                for token in spoken_text.split():
                    if token.isdigit():
                        recognized_number = token
                        break

            # Confidence is 1.0 if matches expected, else 0.5 if a number was recognized, else 0.0
            if expected is not None:
                success = recognized_number == expected
                confidence = 1.0 if success else (0.5 if recognized_number else 0.0)
            else:
                success = bool(recognized_number)
                confidence = 0.5 if success else 0.0

            return {
                'success': success,
                'confidence': float(confidence),
                'question': f"{expression} = ?" if expression else None,
                'answer': expected,
                'spoken_text': spoken_text,
                'recognized_number': recognized_number,
                'message': 'Voice captcha (upload) completed successfully' if success else 'Voice captcha (upload) failed'
            }

        except Exception as e:
            logger.error(f"Voice captcha upload verification failed: {e}")
            return {
                'success': False,
                'confidence': 0.0,
                'message': f'Voice captcha upload verification failed: {str(e)}',
                'error': str(e)
            }