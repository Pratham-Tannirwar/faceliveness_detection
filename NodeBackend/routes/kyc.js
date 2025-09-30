const express = require('express');
const { query } = require('../db');
const router = express.Router();

// POST /kyc/liveness-check - Process liveness check
router.post('/liveness-check', async (req, res) => {
  try {
    const { image_base64, user_id } = req.body;

    // Validate required fields
    if (!image_base64) {
      return res.status(400).json({
        liveness: false,
        message: 'Image data is required'
      });
    }

    // In a real implementation, you would:
    // 1. Process the image with face detection/liveness detection
    // 2. Use face-api.js or similar library
    // 3. Return actual liveness detection results

    // For demo purposes, simulate processing
    const mockResult = {
      liveness_score: Math.random() * 0.4 + 0.6,
      face_detected: true,
      is_live: Math.random() > 0.2,
      confidence: Math.random() * 0.3 + 0.7,
      timestamp: new Date().toISOString()
    };

    // Update user verification status on users table if user_id provided
    if (user_id) {
      await query(
        'UPDATE users SET is_verified = $1, updated_at = NOW() WHERE id = $2',
        [mockResult.is_live, user_id]
      );
    }

    res.json({
      liveness: mockResult.is_live,
      message: mockResult.is_live ? 'Liveness verified' : 'Liveness check failed'
    });

  } catch (error) {
    console.error('Liveness check error:', error);
    res.status(500).json({
      liveness: false,
      message: 'Internal server error during liveness check'
    });
  }
});

// POST /kyc/submit - Submit KYC for review
router.post('/submit', async (req, res) => {
  try {
    const { user_id, liveness_result, additional_data } = req.body;

    // Validate required fields
    if (!user_id) {
      return res.status(400).json({
        success: false,
        error: 'User ID is required'
      });
    }

    // Insert KYC submission
    const result = await query(
      'INSERT INTO kyc_submissions (user_id, liveness_result, status, submitted_at) VALUES ($1, $2, $3, NOW()) RETURNING id',
      [user_id, liveness_result || 'pending', 'pending']
    );

    res.json({
      success: true,
      message: 'KYC submitted successfully',
      submission_id: result.rows[0].id
    });

  } catch (error) {
    console.error('KYC submission error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error during KYC submission'
    });
  }
});

// GET /kyc/status/:userId - Get KYC status for user
router.get('/status/:userId', async (req, res) => {
  try {
    const { userId } = req.params;

    // Validate userId parameter
    if (!userId || isNaN(parseInt(userId))) {
      return res.status(400).json({
        success: false,
        error: 'Valid user ID is required'
      });
    }

    // Query latest KYC submission
    const result = await query(
      'SELECT liveness_result, status, submitted_at, reviewed_at FROM kyc_submissions WHERE user_id = $1 ORDER BY submitted_at DESC LIMIT 1',
      [userId]
    );

    if (result.rows.length === 0) {
      return res.json({
        success: true,
        data: {
          kyc_status: 'not_submitted',
          message: 'No KYC submission found'
        }
      });
    }

    const kyc = result.rows[0];

    res.json({
      success: true,
      data: {
        kyc_status: kyc.status,
        liveness_result: kyc.liveness_result,
        submitted_at: kyc.submitted_at,
        reviewed_at: kyc.reviewed_at
      }
    });

  } catch (error) {
    console.error('KYC status fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error while fetching KYC status'
    });
  }
});

module.exports = router;
