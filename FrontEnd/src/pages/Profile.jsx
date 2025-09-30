import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { profileAPI } from '../services/api';
import './Profile.css';

const Profile = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  const [userData, setUserData] = useState(null);
  // const [kycData, setKycData] = useState(null); // TODO: Implement KYC data fetching
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch user profile data
  useEffect(() => {
    const fetchProfileData = async () => {
      if (!user?.id) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const [profileResponse, kycResponse] = await Promise.all([
          profileAPI.getProfile(user.id),
          profileAPI.getKYC(user.id)
        ]);

        if (profileResponse.success) {
          setUserData(profileResponse.data);
        }

        if (kycResponse.success) {
          // setKycData(kycResponse.data); // TODO: Implement KYC data handling
          console.log('KYC data received:', kycResponse.data);
        }
      } catch (err) {
        console.error('Error fetching profile data:', err);
        setError('Failed to load profile data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfileData();
  }, [user?.id]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getKYCStatusBadge = (status) => {
    const statusConfig = {
      'pending': { color: '#ffc107', bgColor: '#fff3cd', text: 'Pending' },
      'verified': { color: '#28a745', bgColor: '#d4edda', text: 'Verified' },
      'rejected': { color: '#dc3545', bgColor: '#f8d7da', text: 'Rejected' },
      'not_submitted': { color: '#6c757d', bgColor: '#e9ecef', text: 'Not Submitted' }
    };
    
    const config = statusConfig[status] || statusConfig['not_submitted'];
    
    return (
      <span 
        className="kyc-badge"
        style={{
          color: config.color,
          backgroundColor: config.bgColor,
          borderColor: config.color
        }}
      >
        {config.text}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="profile-page">
        <div className="profile-container">
          <div className="profile-card">
            <div className="loading-message">Loading profile...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-page">
        <div className="profile-container">
          <div className="profile-card">
            <div className="error-message">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  if (!userData) {
    return (
      <div className="profile-page">
        <div className="profile-container">
          <div className="profile-card">
            <div className="error-message">No profile data available</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-container">
        <div className="profile-card">
          {/* Header */}
          <div className="profile-header">
            <h1>Account Summary</h1>
            <p>Your banking profile and account details</p>
          </div>

          {/* Profile Content */}
          <div className="profile-content">
            {/* Personal Information */}
            <div className="profile-section">
              <h3>Personal Information</h3>
              <div className="profile-grid">
                <div className="profile-field">
                  <label>Full Name</label>
                  <div className="field-value">{userData.fullname}</div>
                </div>
                <div className="profile-field">
                  <label>Email Address</label>
                  <div className="field-value">{userData.email}</div>
                </div>
                <div className="profile-field">
                  <label>Phone Number</label>
                  <div className="field-value">{userData.mobile_number}</div>
                </div>
                <div className="profile-field">
                  <label>Account Number</label>
                  <div className="field-value">{userData.account_number}</div>
                </div>
              </div>
            </div>

            {/* Account Information */}
            <div className="profile-section">
              <h3>Account Information</h3>
              <div className="profile-grid">
                <div className="profile-field">
                  <label>Account Type</label>
                  <div className="field-value">{userData.account_type || 'Standard'}</div>
                </div>
                <div className="profile-field">
                  <label>Current Balance</label>
                  <div className="field-value balance">₹{userData.balance?.toLocaleString() || '0.00'}</div>
                </div>
                <div className="profile-field">
                  <label>KYC Status</label>
                  <div className="field-value">
                    {getKYCStatusBadge(userData.kyc_status)}
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="profile-section">
              <h3>Quick Actions</h3>
              <div className="quick-actions">
                <button className="action-btn primary">
                  📊 View Statements
                </button>
                <button className="action-btn secondary">
                  💳 Manage Cards
                </button>
                <button className="action-btn secondary">
                  ⚙️ Account Settings
                </button>
                <button className="action-btn secondary">
                  🔒 Security Settings
                </button>
              </div>
            </div>
          </div>

          {/* Footer with Logout */}
          <div className="profile-footer">
            <button 
              className="logout-button"
              onClick={handleLogout}
            >
              🚪 Log Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
