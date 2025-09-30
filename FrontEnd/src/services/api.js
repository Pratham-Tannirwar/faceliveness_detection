import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const FLASK_API_BASE_URL = process.env.REACT_APP_FLASK_API_URL || 'http://localhost:5000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token if available
api.interceptors.request.use(
  (config) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.token) {
      config.headers.Authorization = `Bearer ${user.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear user data on unauthorized
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  // Send OTP to mobile number
  sendOTP: async (mobileNumber, email = null) => {
    try {
      // Use the actual endpoint instead of test endpoint
      const response = await api.post('/auth/send-otp', {
        mobile_number: mobileNumber,
        email: email,
        purpose: 'login'
      });
      return response.data;
    } catch (error) {
      console.error('Error sending OTP:', error);
      throw error; // Let the calling code handle the error
    }
  },

  // Verify OTP
  verifyOTP: async (mobileNumber, otpCode) => {
    try {
      // Use the actual endpoint instead of test endpoint
      const response = await api.post('/auth/verify-otp', {
        mobile_number: mobileNumber,
        otp_code: otpCode,
        purpose: 'login'
      });
      return response.data;
    } catch (error) {
      console.error('Error verifying OTP:', error);
      throw error; // Let the calling code handle the error
    }
  },

  // User signup
  signup: async (userData) => {
    const response = await api.post('/auth/signup', {
      fullname: userData.fullName,
      email: userData.email,
      mobile_number: userData.mobile,
      password: userData.password,
      confirm_password: userData.confirmPassword,
      otp_code: userData.otp,
    });
    return response.data;
  },

  // User login
  login: async (email, password) => {
    const response = await api.post('/auth/login', {
      email: email,
      password: password,
    });
    return response.data;
  },
};

export const profileAPI = {
  // Get user profile
  getProfile: async (userId) => {
    const response = await api.get(`/profile/${userId}`);
    return response.data;
  },

  // Get KYC details
  getKYC: async (userId) => {
    const response = await api.get(`/profile/${userId}/kyc`);
    return response.data;
  },
};

// Separate Axios instance for Flask API
const flaskApi = axios.create({
  baseURL: FLASK_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token if available (expects user.token in localStorage)
flaskApi.interceptors.request.use(
  (config) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.token) {
      config.headers.Authorization = `Bearer ${user.token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for Flask API error handling
flaskApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear user data on unauthorized
      localStorage.removeItem('user');
      // Redirect to login page
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      // Handle forbidden access
      console.error('Access forbidden:', error.response.data);
    }
    return Promise.reject(error);
  }
);

export const livenessAPI = {
  // Start KYC process
  startKYC: async (userId) => {
    try {
      const response = await flaskApi.post('/kyc/start_kyc', { user_id: userId });
      return response;
    } catch (error) {
      console.error('Error starting KYC:', error);
      throw error; // Let the calling code handle the error
    }
  },
  // Voice captcha step
  voiceCaptcha: async ({ duration = 6, enable_display = false } = {}) => {
    try {
      const response = await flaskApi.post('/kyc/voice-captcha', {
        duration,
        enable_display,
      });
      return response.data; // { success, captcha, expected_answer, message }
    } catch (error) {
      console.error('Error getting voice captcha:', error);
      throw error; // Let the calling code handle the error
    }
  },
  // Upload client-recorded audio for verification
  voiceCaptchaUpload: async (audioBlob, expression) => {
    try {
      const form = new FormData();
      form.append('audio', audioBlob, 'voice.wav');
      if (expression) form.append('expression', expression);
      
      const response = await flaskApi.post('/kyc/voice-captcha-upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading voice captcha:', error);
      throw error;
    }
  },
  // Optional: run complete liveness flow on Flask
  complete: async ({ reference_image = null, enable_display = false } = {}) => {
    try {
      const response = await flaskApi.post('/kyc/complete', {
        reference_image,
        enable_display,
      });
      return response.data;
    } catch (error) {
      console.error('Error completing liveness verification:', error);
      throw error;
    }
  },
};

export default api;
