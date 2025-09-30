import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authAPI, profileAPI, livenessAPI } from '../services/api';
import Webcam from 'react-webcam';
import './KYC.css';

const KYC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  
  const [isVerifying, setIsVerifying] = useState(false);
  const [apiResponse, setApiResponse] = useState(null);
  const [captcha, setCaptcha] = useState(null);
  const [showCaptcha, setShowCaptcha] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [verificationStatus, setVerificationStatus] = useState('idle'); // idle, verifying, completed
  const [result, setResult] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [error, setError] = useState(null);
  const [showOTPPopup, setShowOTPPopup] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingOtp, setVerifyingOtp] = useState(false);
  const [mobileNumber, setMobileNumber] = useState('');
  const [agreeTnC, setAgreeTnC] = useState(false);
  const [currentInstruction, setCurrentInstruction] = useState('');
  // const [instructionTimer, setInstructionTimer] = useState(null); // TODO: Implement instruction timer
  const [showInstructionModal, setShowInstructionModal] = useState(false);
  const [isStartingKYC, setIsStartingKYC] = useState(false);

  // Capture image from webcam
  const capture = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    return imageSrc;
  }, [webcamRef]);

  // Convert image to base64
  const convertToBase64 = (imageSrc) => {
    return imageSrc.split(',')[1]; // Remove data:image/jpeg;base64, prefix
  };

  // Show OTP popup first and send OTP
  const startVerification = async () => {
    setShowOTPPopup(true);
    setError(null);

    try {
      // Fetch user profile for mobile number if not present
      let numberFromProfile = null;
      if (!mobileNumber && user?.id) {
        const profile = await profileAPI.getProfile(user.id);
        numberFromProfile = profile?.data?.mobile_number || null;
        if (numberFromProfile) setMobileNumber(numberFromProfile);
      }

      // Determine number to use immediately (avoid relying on async state update)
      const numberToUse = mobileNumber || numberFromProfile || user?.mobile_number || '';

      // Send OTP to user's mobile number
      if (numberToUse) {
        setSendingOtp(true);
        const response = await authAPI.sendOTP(numberToUse);
        if (response && response.otp) {
          console.log('OTP for testing:', response.otp);
        }
      } else {
        setError('Mobile number is required to send OTP.');
      }
    } catch (e) {
      console.error('Error preparing OTP:', e);
      setError('Failed to send OTP. Please try again.');
    } finally {
      setSendingOtp(false);
    }
  };

  // Handle OTP verification
  const handleOTPVerification = async () => {
    if (!otpCode || otpCode.length !== 6) {
      setError('Enter the 6-digit OTP.');
      return;
    }
    if (!mobileNumber) {
      setError('Mobile number is missing. Please refresh and try again.');
      return;
    }
    try {
      setVerifyingOtp(true);
      const response = await authAPI.verifyOTP(mobileNumber, otpCode);
      if (response && response.success) {
        setOtpVerified(true);
        setError(null);
        // Pre-request microphone permission early
        await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        // Proceed to next step automatically after successful verification
        setTimeout(() => {
          startActualVerification();
        }, 500);
      } else {
        setError(response?.message || 'OTP verification failed. Please try again.');
      }
    } catch (e) {
      console.error('OTP verification failed:', e);
      setError(e.response?.data?.error || 'Invalid or expired OTP. Please try again.');
    } finally {
      setVerifyingOtp(false);
    }
  };
  
  // Resend OTP function
  const resendOTP = async () => {
    if (!mobileNumber) {
      setError('Mobile number is missing. Please refresh and try again.');
      return;
    }
    
    try {
      setSendingOtp(true);
      setError(null);
      const response = await authAPI.sendOTP(mobileNumber);
      if (response && response.otp) {
        console.log('OTP for testing:', response.otp);
        setError('OTP has been resent to your mobile number.');
      } else {
        setError('Failed to resend OTP. Please try again.');
      }
    } catch (e) {
      console.error('Error sending OTP:', e);
      setError('Failed to resend OTP. Please try again.');
    } finally {
      setSendingOtp(false);
    }
  };

  // Start KYC process by calling Flask API endpoint
  const startKYCProcess = async () => {
    try {
      // Check if user is authenticated
      if (!user || !user.token) {
        setError('Please log in to start KYC verification.');
        return;
      }

      setIsStartingKYC(true);
      setError(null);
      
      // Call the Flask API endpoint to start KYC process using the flaskApi interceptor
      const response = await livenessAPI.startKYC(user.id);
      console.log(response)
      
      if (response.data.success) {
        // Proceed directly with verification
        startVerification();
      } else {
        setError(response.data.message || 'Failed to start KYC process. Please try again.');
        setIsStartingKYC(false);
      }
    } catch (err) {
      console.error('Error starting KYC process:', err);
      
      // Handle specific error cases
      if (err.response?.status === 401) {
        setError('Your session has expired. Please log in again.');
        // The interceptor will handle redirecting to login
      } else if (err.response?.status === 403) {
        setError('Access denied. Please contact support.');
      } else {
        setError(err.response?.data?.message || 'Failed to start KYC process. Please try again.');
      }
      setIsStartingKYC(false);
    }
  };
  
  // Start actual verification after OTP
  const startActualVerification = async () => {
    try {
      // Check if webcam is ready
      if (!webcamRef.current || !webcamRef.current.video || webcamRef.current.video.readyState !== 4) {
        console.error('Webcam not ready');
        setError('Webcam not ready. Please ensure camera access is granted.');
        return;
      }

      setShowOTPPopup(false);
      setIsVerifying(true);
      setVerificationStatus('verifying');
      setError(null);
      setApiResponse(null);

      // Start dynamic instructions
      startDynamicInstructions();

      // Add a small delay to ensure webcam is fully initialized
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Capture current frame
      const imageSrc = capture();
      if (!imageSrc) {
        throw new Error('Failed to capture image from webcam');
      }
      const base64Image = convertToBase64(imageSrc);
      
      console.log('Captured image base64:', base64Image);

      // Send to Flask API
      const response = await fetch('http://localhost:5000/api/v1/kyc/liveness-test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: base64Image,
          user_id: user?.id
        })
      });

      const data = await response.json();
      setApiResponse(data);
      console.log('API Response:', data);

      // Start continuous verification process
      startContinuousVerification();

    } catch (err) {
      console.error('Verification error:', err);
      setError('Failed to start verification. Please try again.');
      setIsVerifying(false);
      setVerificationStatus('idle');
    }
  };

  // Start dynamic instructions
  const startDynamicInstructions = () => {
    // Initially: "Look straight into camera"
    setCurrentInstruction('Look straight into camera');
    
    // After 2s: "Blink your Eyes"
    setTimeout(() => {
      setCurrentInstruction('Blink your Eyes');
    }, 2000);
    
    // After 6s: "Say correct answer"
    setTimeout(() => {
      setCurrentInstruction('Say correct answer');
    }, 6000);
  };

  // Start continuous verification process
  const startContinuousVerification = () => {
    // After 6 seconds, show math captcha and start audio recording immediately
    setTimeout(() => {
      const a = Math.floor(10 + Math.random() * 90);
      const b = Math.floor(1 + Math.random() * 9);
      const op = Math.random() > 0.5 ? '+' : '-';
      const expression = `${a} ${op} ${b}`;
      setCaptcha(`Say the answer: ${expression}`);
      setShowCaptcha(true);
      setVerificationStatus('captcha');
      // Record audio locally for 6s and upload to Flask for verification
      startAudioRecording(expression);
    }, 6000);
  };

  // Start audio recording
  const startAudioRecording = async (expression) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true,
        video: false 
      });
      
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        try {
          const uploadResult = await livenessAPI.voiceCaptchaUpload(audioBlob, expression);
          setResult({
            status: uploadResult.liveness ? 'success' : 'failed',
            message: uploadResult.message || (uploadResult.liveness ? 'KYC verification completed successfully' : 'KYC verification failed'),
            confidence: 0.9,
            timestamp: new Date().toISOString()
          });
          setShowResult(true);
          setVerificationStatus('completed');
          setIsVerifying(false);
        } catch (e) {
          console.error('Upload verification failed:', e);
          setError('Voice captcha upload failed. Please retry.');
          setVerificationStatus('idle');
          setIsVerifying(false);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setVerificationStatus('recording');

      // Stop after 6 seconds
      setTimeout(() => {
        if (mediaRecorderRef.current && isRecording) {
          mediaRecorderRef.current.stop();
          setIsRecording(false);
        }
      }, 6000);

    } catch (err) {
      console.error('Audio recording error:', err);
      setError('Failed to start audio recording. Please allow microphone access.');
      setVerificationStatus('idle');
      setIsVerifying(false);
    }
  };

  // Complete verification process
  const completeVerification = () => {
    setTimeout(() => {
      setVerificationStatus('completed');
      setIsRecording(false);
      setIsVerifying(false);
      
      // Simulate API response
      const mockResult = {
        status: 'success',
        message: 'KYC verification completed successfully',
        confidence: 0.95,
        timestamp: new Date().toISOString()
      };
      
      setResult(mockResult);
      setShowResult(true);
    }, 3000);
  };

  // Handle result popup OK button
  const handleResultOk = () => {
    setShowResult(false);
    // Update KYC status in profile (this would be handled by your state management)
    console.log('KYC status updated in profile');
    navigate('/');
  };

  // Stop audio recording
  const stopAudioRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Check authentication on component mount
  useEffect(() => {
    if (!user || !user.token) {
      setError('Please log in to access KYC verification.');
    }
  }, [user]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  return (
    <div className="kyc-page">
      <div className="kyc-container">
        <div className="kyc-header">
          <h1>KYC Verification</h1>
          <p>Complete your identity verification process</p>
        </div>
        
        {/* KYC Instruction Modal */}
        {showInstructionModal && (
          <div className="instruction-modal-overlay">
            <div className="instruction-modal">
              <div className="instruction-modal-header">
                <h2>KYC Verification Process</h2>
              </div>
              <div className="instruction-modal-content">
                <p>Welcome to our secure KYC verification system. Please follow these steps:</p>
                <ol>
                  <li>Ensure you are in a well-lit environment</li>
                  <li>Position your face clearly in the camera frame</li>
                  <li>Follow the on-screen instructions during verification</li>
                  <li>Complete the liveness checks (blinking, speaking)</li>
                  <li>Wait for the verification result</li>
                </ol>
                <p>This process helps us verify your identity and prevent fraud.</p>
              </div>
              <div className="instruction-modal-footer">
                <button 
                  className="start-kyc-button" 
                  onClick={startKYCProcess}
                  disabled={isStartingKYC}
                >
                  {isStartingKYC ? (
                    <>
                      <span className="spinner"></span>
                      Starting...
                    </>
                  ) : (
                    'Start Verification'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="kyc-content">
          {/* Left Column - Webcam */}
          <div className="webcam-section">
            <div className="webcam-container">
              <Webcam
                ref={webcamRef}
                width={640}
                height={480}
                screenshotFormat="image/jpeg"
                videoConstraints={{
                  width: 640,
                  height: 480,
                  facingMode: "user"
                }}
                className="webcam-feed"
              />
              
              {/* Status Overlay */}
              <div className="webcam-overlay">
                <div className={`status-indicator ${verificationStatus}`}>
                  {verificationStatus === 'idle' && 'Ready to verify'}
                  {verificationStatus === 'verifying' && (currentInstruction || 'Verifying...')}
                  {verificationStatus === 'completed' && 'Verification complete'}
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="webcam-controls">
              <button
                className="verify-button"
                onClick={startKYCProcess}
                disabled={isVerifying || isStartingKYC}
              >
                {isVerifying || isStartingKYC ? 'Starting...' : 'Start Verification'}
              </button>
              
              {isRecording && (
                <button
                  className="stop-recording-button"
                  onClick={stopAudioRecording}
                >
                  Stop Recording
                </button>
              )}
            </div>
          </div>

          {/* Right Column - API Response */}
          <div className="response-section">
            <h3>Verification Status</h3>
            
            {/* Captcha Display */}
            {showCaptcha && (
              <div className="captcha-container">
                <h4>Security Captcha</h4>
                <div className="captcha-box">
                  <p>{captcha}</p>
                  <button 
                    className="captcha-solved-btn"
                    onClick={() => setShowCaptcha(false)}
                  >
                    Captcha Solved
                  </button>
                </div>
              </div>
            )}

            {/* API Response */}
            {apiResponse && (
              <div className="api-response">
                <h4>API Response</h4>
                <pre className="response-json">
                  {JSON.stringify(apiResponse, null, 2)}
                </pre>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="error-message">
                <h4>Error</h4>
                <p>{error}</p>
              </div>
            )}

            {/* Verification Progress */}
            <div className="progress-section">
              <h4>Verification Progress</h4>
              <div className="progress-steps">
                <div className={`step ${verificationStatus === 'verifying' ? 'active' : ''}`}>
                  <span className="step-number">1</span>
                  <span className="step-text">Start Verification</span>
                </div>
                <div className={`step ${verificationStatus === 'completed' ? 'active' : ''}`}>
                  <span className="step-number">2</span>
                  <span className="step-text">Complete</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* OTP Verification Popup */}
      {showOTPPopup && (
        <div className="otp-modal">
          <div className="otp-modal-content">
            <div className="otp-header">
              <h2>Mobile Verification Required</h2>
            </div>
            <div className="otp-body">
              {!otpVerified ? (
                <div className="otp-verification">
                  <div className="otp-icon">📱</div>
                  <h3>Verify Your Mobile Number</h3>
                  <p>We'll send an OTP to your registered mobile number for verification.</p>
                  <div className="otp-input-section">
                    <div className="otp-mobile">{mobileNumber ? `OTP sent to ${mobileNumber}` : 'Fetching mobile number...'}</div>
                    <input 
                      type="tel" 
                      placeholder="Enter 6-digit OTP" 
                      className="otp-input"
                      maxLength="6"
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    />
                    <button 
                      className="verify-otp-btn"
                      onClick={handleOTPVerification}
                      disabled={verifyingOtp || !otpCode}
                    >
                      {verifyingOtp ? 'Verifying...' : 'Verify OTP'}
                    </button>
                  </div>
                  <div className="otp-actions">
                    <button 
                      className="resend-otp-btn"
                      disabled={sendingOtp || !mobileNumber}
                      onClick={resendOTP}
                    >
                      {sendingOtp ? 'Resending...' : 'Resend OTP'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="kyc-instructions">
                  <div className="instructions-icon">📋</div>
                  <h3>KYC Verification Instructions</h3>
                  {error && <div className="error-message">{error}</div>}
                  <div className="instructions-list">
                    <div className="instruction-item">
                      <span className="instruction-number">1</span>
                      <span className="instruction-text">Only one person in front of the camera.</span>
                    </div>
                    <div className="instruction-item">
                      <span className="instruction-number">2</span>
                      <span className="instruction-text">Look straight at the camera and blink normally.</span>
                    </div>
                    <div className="instruction-item">
                      <span className="instruction-number">3</span>
                      <span className="instruction-text">When captcha appears → calculate quickly.</span>
                    </div>
                    <div className="instruction-item">
                      <span className="instruction-number">4</span>
                      <span className="instruction-text">Say the answer within 5 seconds.</span>
                    </div>
                  </div>
                  <div className="agreement-section">
                    <label className="agreement-checkbox">
                      <input type="checkbox" checked={agreeTnC} onChange={(e) => setAgreeTnC(e.target.checked)} />
                      <span className="checkmark"></span>
                      I have read and understood the KYC verification instructions
                    </label>
                  </div>
                  <div className="instruction-buttons" style={{ marginTop: '20px' }}>
                    <button 
                      className="start-verification-btn"
                      onClick={() => {
                        try {
                          // Ensure webcam is initialized before proceeding
                          if (webcamRef.current && webcamRef.current.video) {
                            startActualVerification();
                          } else {
                            setError('Webcam not initialized. Please ensure camera access is granted.');
                          }
                        } catch (err) {
                          console.error('Error starting verification:', err);
                          setError('Failed to start verification. Please try again.');
                        }
                      }}
                      disabled={!agreeTnC}
                    >
                      Start KYC Verification
                    </button>
                  </div>
                </div>
              )}
            </div>
            <div className="otp-footer">
              {!otpVerified ? (
                <button 
                  className="cancel-otp-btn"
                  onClick={() => setShowOTPPopup(false)}
                >
                  Cancel
                </button>
              ) : (
                <div className="otp-verified-buttons">
                  <button 
                    className="cancel-otp-btn"
                    onClick={() => setShowOTPPopup(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    className="proceed-btn"
                    onClick={() => {
                      setShowOTPPopup(false);
                      try {
                        // Ensure webcam is initialized before proceeding
                        if (webcamRef.current && webcamRef.current.video) {
                          startActualVerification();
                        } else {
                          setError('Webcam not initialized. Please ensure camera access is granted.');
                        }
                      } catch (err) {
                        console.error('Error starting verification:', err);
                        setError('Failed to start verification. Please try again.');
                      }
                    }}
                  >
                    Proceed to Verification
                  </button>
                </div>
               )}
            </div>
          </div>
        </div>
      )}

      {/* Result Popup */}
      {showResult && (
        <div className="result-modal">
          <div className="result-modal-content">
            <div className="result-header">
              <h2>Verification Complete</h2>
            </div>
            <div className="result-body">
              <div className="result-icon">✅</div>
              <h3>{result?.message}</h3>
              <p>Confidence: {(result?.confidence * 100).toFixed(1)}%</p>
              <p>Your KYC status has been updated successfully.</p>
            </div>
            <div className="result-footer">
              <button 
                className="result-ok-button"
                onClick={handleResultOk}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KYC;
