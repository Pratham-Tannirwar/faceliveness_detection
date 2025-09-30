const express = require('express');
const { query } = require('../db');
const router = express.Router();

// GET /profile/:userId - Get user profile with KYC status
router.get('/profile/:userId', async (req, res) => {
  try {
    const { userId } = req.params;

    // Validate userId parameter
    if (!userId || isNaN(parseInt(userId))) {
      return res.status(400).json({
        success: false,
        error: 'Valid user ID is required'
      });
    }

    // Query user information
    const userResult = await query(
      `SELECT fullname, email, mobile_number, account_number, account_type, balance 
       FROM users 
       WHERE id = $1`,
      [userId]
    );

    if (userResult.rows.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }

    const user = userResult.rows[0];

    // Query latest KYC submission
    const kycResult = await query(
      `SELECT liveness_result, status 
       FROM kyc_submissions 
       WHERE user_id = $1 
       ORDER BY submitted_at DESC 
       LIMIT 1`,
      [userId]
    );

    // Determine KYC status
    let kycStatus = 'not_submitted';
    if (kycResult.rows.length > 0) {
      const kyc = kycResult.rows[0];
      kycStatus = kyc.status;
    }

    // Prepare response
    const profileData = {
      fullname: user.fullname,
      email: user.email,
      mobile_number: user.mobile_number,
      account_number: user.account_number,
      account_type: user.account_type,
      balance: parseFloat(user.balance),
      kyc_status: kycStatus
    };

    res.json({
      success: true,
      data: profileData
    });

  } catch (error) {
    console.error('Profile fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error while fetching profile'
    });
  }
});

// GET /profile/:userId/kyc - Get detailed KYC information
router.get('/profile/:userId/kyc', async (req, res) => {
  try {
    const { userId } = req.params;

    // Validate userId parameter
    if (!userId || isNaN(parseInt(userId))) {
      return res.status(400).json({
        success: false,
        error: 'Valid user ID is required'
      });
    }

    // Query latest KYC submission with full details
    const kycResult = await query(
      `SELECT id, liveness_result, status, submitted_at, reviewed_at, notes
       FROM kyc_submissions 
       WHERE user_id = $1 
       ORDER BY submitted_at DESC 
       LIMIT 1`,
      [userId]
    );

    if (kycResult.rows.length === 0) {
      return res.json({
        success: true,
        data: {
          kyc_status: 'not_submitted',
          message: 'No KYC submission found'
        }
      });
    }

    const kyc = kycResult.rows[0];

    res.json({
      success: true,
      data: {
        kyc_status: kyc.status,
        liveness_result: kyc.liveness_result,
        submitted_at: kyc.submitted_at,
        reviewed_at: kyc.reviewed_at,
        notes: kyc.notes
      }
    });

  } catch (error) {
    console.error('KYC fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error while fetching KYC data'
    });
  }
});

module.exports = router;
