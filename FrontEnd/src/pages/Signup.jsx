import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import Webcam from 'react-webcam';
import './Signup.css';

const Signup = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    mobile: '',
    otp: '',
    password: '',
    confirmPassword: '',
    profileImage: null
  });

  const [errors, setErrors] = useState({});
  const [otpSent, setOtpSent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const webcamRef = useRef(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    } else if (formData.fullName.trim().length < 2) {
      newErrors.fullName = 'Full name must be at least 2 characters';
    }
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.mobile) {
      newErrors.mobile = 'Mobile number is required';
    } else if (!/^\d{10}$/.test(formData.mobile.replace(/\D/g, ''))) {
      newErrors.mobile = 'Mobile number must be 10 digits';
    }
    
    if (!formData.otp) {
      newErrors.otp = 'OTP is required';
    } else if (!/^\d{6}$/.test(formData.otp)) {
      newErrors.otp = 'OTP must be 6 digits';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Confirm password is required';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    // Profile image optional for now; enable this to enforce:
    // if (!formData.profileImage) {
    //   newErrors.profileImage = 'Profile image is required';
    // }
    
    return newErrors;
  };

  const handleSendOTP = async () => {
    if (!formData.mobile) {
      setErrors(prev => ({ ...prev, mobile: 'Mobile number is required' }));
      return;
    }
    
    if (!/^\d{10}$/.test(formData.mobile.replace(/\D/g, ''))) {
      setErrors(prev => ({ ...prev, mobile: 'Mobile number must be 10 digits' }));
      return;
    }

    setIsLoading(true);
    setErrors(prev => ({ ...prev, mobile: '', general: '' }));
    
    try {
      const response = await authAPI.sendOTP(formData.mobile, formData.email);
      
      if (response.success) {
        setOtpSent(true);
        alert(`OTP sent to your mobile number! ${response.otp ? `(Demo: Use ${response.otp})` : ''}`);
      } else {
        setErrors(prev => ({ ...prev, general: response.error || 'Failed to send OTP' }));
      }
    } catch (error) {
      console.error('Send OTP error:', error);
      setErrors(prev => ({ 
        ...prev, 
        general: error.response?.data?.error || 'Failed to send OTP' 
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageCapture = () => {
    setShowCamera(true);
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
        setFormData(prev => ({
          ...prev,
          profileImage: file
        }));
        // Clear any existing error
        if (errors.profileImage) {
          setErrors(prev => ({
            ...prev,
            profileImage: ''
          }));
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const captureFromCamera = async () => {
    try {
      const imageSrc = webcamRef.current?.getScreenshot();
      if (!imageSrc) {
        setErrors(prev => ({ ...prev, profileImage: 'Unable to capture image. Please allow camera access.' }));
        return;
      }

      const blob = await (await fetch(imageSrc)).blob();
      const file = new File([blob], 'profile.jpg', { type: blob.type || 'image/jpeg' });

      setFormData(prev => ({
        ...prev,
        profileImage: file
      }));
      setImagePreview(imageSrc);
      setShowCamera(false);

      if (errors.profileImage) {
        setErrors(prev => ({
          ...prev,
          profileImage: ''
        }));
      }
    } catch (e) {
      console.error('Camera capture error:', e);
      setErrors(prev => ({ ...prev, profileImage: 'Camera capture failed. Try again.' }));
    }
  };

  const removeImage = () => {
    setImagePreview(null);
    setFormData(prev => ({
      ...prev,
      profileImage: null
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = validateForm();
    
    if (Object.keys(newErrors).length === 0) {
      setIsLoading(true);
      setErrors({});
      
      try {
        // 1) Verify OTP before signup (backend requires verified OTP)
        const verify = await authAPI.verifyOTP(formData.mobile, formData.otp);
        if (!verify.success) {
          setErrors({ general: verify.error || 'OTP verification failed' });
          setIsLoading(false);
          return;
        }

        // 2) Proceed with signup
        const response = await authAPI.signup(formData);
        
        if (response.success) {
          alert('Account created successfully! Please login to continue.');
          navigate('/login');
        } else {
          setErrors({ general: response.error || 'Account creation failed' });
        }
      } catch (error) {
        console.error('Signup error:', error);
        setErrors({ 
          general: error.response?.data?.error || 'Account creation failed' 
        });
      } finally {
        setIsLoading(false);
      }
    } else {
      setErrors(newErrors);
    }
  };

  return (
    <div className="signup-page">
      <div className="signup-container">
        <div className="signup-card">
          {/* Header */}
          <div className="signup-header">
            <h1 className="signup-title">Create Account</h1>
            <p className="signup-subtitle">Join Mock Bank today</p>
          </div>

          {/* Signup Form */}
          <form onSubmit={handleSubmit} className="signup-form">
            {/* Full Name Field */}
            <div className="form-group">
              <label htmlFor="fullName" className="form-label">Full Name</label>
              <input
                type="text"
                id="fullName"
                name="fullName"
                value={formData.fullName}
                onChange={handleChange}
                className={`form-input ${errors.fullName ? 'error' : ''}`}
                placeholder="Enter your full name"
                required
              />
              {errors.fullName && <span className="error-message">{errors.fullName}</span>}
            </div>

            {/* Email Field */}
            <div className="form-group">
              <label htmlFor="email" className="form-label">Email Address</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`form-input ${errors.email ? 'error' : ''}`}
                placeholder="Enter your email address"
                required
              />
              {errors.email && <span className="error-message">{errors.email}</span>}
            </div>

            {/* Mobile Number Field */}
            <div className="form-group">
              <label htmlFor="mobile" className="form-label">Mobile Number</label>
              <div className="mobile-input-group">
                <input
                  type="tel"
                  id="mobile"
                  name="mobile"
                  value={formData.mobile}
                  onChange={handleChange}
                  className={`form-input mobile-input ${errors.mobile ? 'error' : ''}`}
                  placeholder="Enter 10-digit mobile number"
                  maxLength="10"
                  required
                />
                <button
                  type="button"
                  className="otp-button"
                  onClick={handleSendOTP}
                  disabled={isLoading || otpSent}
                >
                  {isLoading ? 'Sending...' : otpSent ? 'Sent' : 'Send OTP'}
                </button>
              </div>
              {errors.mobile && <span className="error-message">{errors.mobile}</span>}
            </div>

            {/* OTP Field */}
            {otpSent && (
              <div className="form-group">
                <label htmlFor="otp" className="form-label">OTP Verification</label>
                <input
                  type="text"
                  id="otp"
                  name="otp"
                  value={formData.otp}
                  onChange={handleChange}
                  className={`form-input ${errors.otp ? 'error' : ''}`}
                  placeholder="Enter 6-digit OTP"
                  maxLength="6"
                  required
                />
                {errors.otp && <span className="error-message">{errors.otp}</span>}
              </div>
            )}

            {/* Password Field */}
            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={`form-input ${errors.password ? 'error' : ''}`}
                placeholder="Create a strong password"
                required
              />
              {errors.password && <span className="error-message">{errors.password}</span>}
            </div>

            {/* Confirm Password Field */}
            <div className="form-group">
              <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
                placeholder="Confirm your password"
                required
              />
              {errors.confirmPassword && <span className="error-message">{errors.confirmPassword}</span>}
            </div>

            {/* Profile Image Field */}
            <div className="form-group">
              <label className="form-label">Profile Image</label>
              <div className="image-upload-section">
                {imagePreview ? (
                  <div className="image-preview-container">
                    <img src={imagePreview} alt="Profile preview" className="image-preview" />
                    <button
                      type="button"
                      className="remove-image-btn"
                      onClick={removeImage}
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <div className="image-upload-options">
                    <div className="upload-buttons">
                      <label htmlFor="image-upload" className="upload-btn">
                        📁 Upload Photo
                      </label>
                      <input
                        type="file"
                        id="image-upload"
                        accept="image/*"
                        onChange={handleImageUpload}
                        style={{ display: 'none' }}
                      />
                      <button
                        type="button"
                        className="camera-btn"
                        onClick={handleImageCapture}
                      >
                        📷 Take Photo
                      </button>
                    </div>
                    <p className="upload-hint">Upload a clear photo of yourself</p>
                  </div>
                )}
                {errors.profileImage && <span className="error-message">{errors.profileImage}</span>}
              </div>
            </div>

            {/* General Error Message */}
            {errors.general && (
              <div className="error-message general-error">
                {errors.general}
              </div>
            )}

            {/* Terms and Conditions */}
            <div className="terms-section">
              <label className="terms-checkbox">
                <input type="checkbox" required />
                <span className="checkmark"></span>
                I agree to the <Link to="/terms" className="terms-link">Terms & Conditions</Link> and <Link to="/privacy" className="terms-link">Privacy Policy</Link>
              </label>
            </div>

            {/* Submit Button */}
            <button 
              type="submit" 
              className="submit-button"
              disabled={isLoading}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          {/* Login Link */}
          <div className="login-section">
            <p className="login-text">
              Already have an account? 
              <Link to="/login" className="login-link">
                Login
              </Link>
            </p>
          </div>

          {/* Additional Info */}
          <div className="signup-footer">
            <p className="security-note">
              🔒 Your data is protected with bank-level security
            </p>
          </div>
        </div>
      </div>

      {/* Camera Modal */}
      {showCamera && (
        <div className="camera-modal">
          <div className="camera-modal-content">
            <div className="camera-header">
              <h3>Take Profile Photo</h3>
              <button 
                className="close-camera-btn"
                onClick={() => setShowCamera(false)}
              >
                ✕
              </button>
            </div>
            <div className="camera-preview">
              <Webcam
                ref={webcamRef}
                audio={false}
                screenshotFormat="image/jpeg"
                videoConstraints={{
                  width: 640,
                  height: 480,
                  facingMode: 'user'
                }}
                className="webcam-feed"
              />
            </div>
            <div className="camera-controls">
              <button 
                className="capture-btn"
                onClick={captureFromCamera}
              >
                📸 Capture Photo
              </button>
              <button 
                className="cancel-camera-btn"
                onClick={() => setShowCamera(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Signup;
