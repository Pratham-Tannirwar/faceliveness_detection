const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { query } = require('../db');
const router = express.Router();

// POST /send-otp - Send OTP to mobile number
router.post('/send-otp', async (req, res) => {
  try {
    const { mobile_number, email } = req.body;

    // Validate required fields
    if (!mobile_number) {
      return res.status(400).json({
        success: false,
        error: 'Mobile number is required'
      });
    }

    // Validate mobile number format (basic validation)
    const mobileRegex = /^\+?[1-9]\d{1,14}$/;
    if (!mobileRegex.test(mobile_number)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid mobile number format'
      });
    }

    // Generate 6-digit OTP
    const otpCode = Math.floor(100000 + Math.random() * 900000).toString();
    const expiresAt = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes from now

    // Store OTP in database
    await query(
      'INSERT INTO otp_verifications (mobile_number, email, otp_code, purpose, expires_at) VALUES ($1, $2, $3, $4, $5)',
      [mobile_number, email || null, otpCode, 'signup', expiresAt]
    );

    // In a real application, you would send SMS here
    // For development, we'll return the OTP in the response
    console.log(`OTP for ${mobile_number}: ${otpCode}`);

    res.json({
      success: true,
      message: 'OTP sent successfully',
      // Remove this in production
      otp: otpCode
    });

  } catch (error) {
    console.error('Send OTP error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error while sending OTP'
    });
  }
});

// POST /verify-otp - Verify OTP
router.post('/verify-otp', async (req, res) => {
  try {
    const { mobile_number, otp_code } = req.body;

    // Validate required fields
    if (!mobile_number || !otp_code) {
      return res.status(400).json({
        success: false,
        error: 'Mobile number and OTP code are required'
      });
    }

    // Find valid OTP
    const result = await query(
      'SELECT id, expires_at FROM otp_verifications WHERE mobile_number = $1 AND otp_code = $2 AND is_verified = FALSE AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1',
      [mobile_number, otp_code]
    );

    if (result.rows.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid or expired OTP'
      });
    }

    // Mark OTP as verified
    await query(
      'UPDATE otp_verifications SET is_verified = TRUE WHERE id = $1',
      [result.rows[0].id]
    );

    res.json({
      success: true,
      message: 'OTP verified successfully'
    });

  } catch (error) {
    console.error('Verify OTP error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error while verifying OTP'
    });
  }
});

// POST /signup - Register a new user
router.post('/signup', async (req, res) => {
  try {
    const { fullname, email, mobile_number, password, confirm_password, otp_code } = req.body;

    // Validate required fields
    if (!fullname || !email || !mobile_number || !password || !confirm_password || !otp_code) {
      return res.status(400).json({
        success: false,
        error: 'All fields are required'
      });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid email format'
      });
    }

    // Validate mobile number format
    const mobileRegex = /^\+?[1-9]\d{1,14}$/;
    if (!mobileRegex.test(mobile_number)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid mobile number format'
      });
    }

    // Validate password length
    if (password.length < 6) {
      return res.status(400).json({
        success: false,
        error: 'Password must be at least 6 characters long'
      });
    }

    // Validate password confirmation
    if (password !== confirm_password) {
      return res.status(400).json({
        success: false,
        error: 'Passwords do not match'
      });
    }

    // Verify OTP
    const otpResult = await query(
      'SELECT id FROM otp_verifications WHERE mobile_number = $1 AND otp_code = $2 AND is_verified = TRUE AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1',
      [mobile_number, otp_code]
    );

    if (otpResult.rows.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid or expired OTP. Please request a new OTP.'
      });
    }

    // Check if user already exists
    const existingUser = await query(
      'SELECT id FROM users WHERE email = $1 OR mobile_number = $2',
      [email, mobile_number]
    );

    if (existingUser.rows.length > 0) {
      return res.status(409).json({
        success: false,
        error: 'User with this email or mobile number already exists'
      });
    }

    // Hash the password
    const saltRounds = 10;
    const passwordHash = await bcrypt.hash(password, saltRounds);

    // Generate account number
    const accountNumber = 'ACC' + Date.now().toString().slice(-8);

    // Insert new user into database
    const result = await query(
      'INSERT INTO users (fullname, email, mobile_number, password_hash, account_number, created_at) VALUES ($1, $2, $3, $4, $5, NOW()) RETURNING id, fullname, email, mobile_number, account_number, created_at',
      [fullname, email, mobile_number, passwordHash, accountNumber]
    );

    const newUser = result.rows[0];

    res.status(201).json({
      success: true,
      message: 'User created successfully',
      user: {
        id: newUser.id,
        fullname: newUser.fullname,
        email: newUser.email,
        mobile_number: newUser.mobile_number,
        account_number: newUser.account_number,
        created_at: newUser.created_at
      }
    });

  } catch (error) {
    console.error('Signup error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error during signup'
    });
  }
});

// POST /login - Authenticate user
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    // Validate required fields
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        error: 'Email and password are required'
      });
    }

    // Find user by email
    const result = await query(
      'SELECT id, fullname, email, password_hash FROM users WHERE email = $1',
      [email]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'Account not found'
      });
    }

    const user = result.rows[0];

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.password_hash);

    if (!isValidPassword) {
      return res.status(401).json({
        success: false,
        error: 'Invalid email or password'
      });
    }

    // Generate JWT token
    const token = jwt.sign(
      { userId: user.id, email: user.email },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '24h' }
    );

    // Return success response with token
    res.json({
      success: true,
      userId: user.id,
      fullname: user.fullname,
      email: user.email,
      token: token
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error during login'
    });
  }
});

module.exports = router;


