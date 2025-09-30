import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';
import './Login.css';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

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
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = validateForm();
    
    if (Object.keys(newErrors).length === 0) {
      setIsLoading(true);
      setErrors({});
      
      try {
        const response = await authAPI.login(formData.email, formData.password);
        
        if (response.success) {
          // Create user data object for context
          const userData = {
            id: response.userId,
            fullName: response.fullname,
            email: response.email,
            mobile_number: response.mobile_number,
            token: response.token, // Use access_token from response
            // Add other fields as needed
          };

          // Login user
          const success = login(userData);
          
          if (success) {
            console.log('Login successful:', formData);
            navigate('/');
          } else {
            setErrors({ general: 'Login failed. Please try again.' });
          }
        } else {
          setErrors({ general: response.error || 'Login failed. Please try again.' });
        }
      } catch (error) {
        if (error.response?.status === 404) {
          setErrors({
            general: 'No account found with this email. Please sign up.',
            email: 'Account not found',
          });
        } else if (error.response?.status === 401) {
          setErrors({
            general: 'Incorrect email or password.',
            password: 'Invalid password',
          });
        } else {
        console.error('Login error:', error);
        setErrors({ 
          general: error.response?.data?.error || 'Login failed. Please try again.' 
        });
        }
      } finally {
        setIsLoading(false);
      }
    } else {
      setErrors(newErrors);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          {/* Header */}
          <div className="login-header">
            <h1 className="login-title">Welcome Back</h1>
            <p className="login-subtitle">Sign in to your Mock account</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="login-form">
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
                placeholder="Enter your password"
                required
              />
              {errors.password && <span className="error-message">{errors.password}</span>}
            </div>

            {/* Forgot Password Link */}
            <div className="forgot-password">
              <Link to="/forgot-password" className="forgot-link">
                Forgot your password?
              </Link>
            </div>

            {/* General Error Message */}
            {errors.general && (
              <div className="error-message general-error">
                {errors.general}
              </div>
            )}

            {/* Login Button */}
            <button 
              type="submit" 
              className="login-button"
              disabled={isLoading}
            >
              {isLoading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          {/* Signup Link */}
          <div className="signup-section">
            <p className="signup-text">
              Don't have an account? 
              <Link to="/signup" className="signup-link">
                Sign up
              </Link>
            </p>
          </div>

          {/* Additional Info */}
          <div className="login-footer">
            <p className="security-note">
              🔒 Your data is protected with bank-level security
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
