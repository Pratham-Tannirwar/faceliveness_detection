import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navbar.css';

const Navbar = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const toggleProfileMenu = () => {
    setShowProfileMenu(!showProfileMenu);
  };

  const handleLogout = () => {
    logout();
    setShowProfileMenu(false);
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo Section */}
        <div className="navbar-logo">
          <Link to="/" className="logo-link">
            <span className="logo-text">Mock</span>
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <div className="mobile-menu-button" onClick={toggleMobileMenu}>
          <span className={`hamburger ${isMobileMenuOpen ? 'active' : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </span>
        </div>

        {/* Navigation Links */}
        <div className={`navbar-menu ${isMobileMenuOpen ? 'active' : ''}`}>
          <ul className="navbar-nav">
            <li className="nav-item">
              <Link 
                to="/" 
                className="nav-link"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Home
              </Link>
            </li>
            {!isAuthenticated ? (
              <>
                <li className="nav-item">
                  <Link 
                    to="/login" 
                    className="nav-link"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    Login
                  </Link>
                </li>
                <li className="nav-item">
                  <Link 
                    to="/signup" 
                    className="nav-link"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    Signup
                  </Link>
                </li>
              </>
            ) : (
              <>
                <li className="nav-item">
                  <Link 
                    to="/kyc" 
                    className="nav-link"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    KYC
                  </Link>
                </li>
                <li className="nav-item">
                  <Link 
                    to="/profile" 
                    className="nav-link"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    Profile
                  </Link>
                </li>
              </>
            )}
          </ul>

          {/* Profile Icon - Only show when logged in */}
          {isAuthenticated && (
            <div className="profile-section">
              <div className="profile-icon" onClick={toggleProfileMenu}>
                <div className="profile-avatar">
                  {user?.fullName ? user.fullName.charAt(0).toUpperCase() : 'U'}
                </div>
                <span className="profile-name">
                  {user?.fullName || 'User'}
                </span>
                <span className="dropdown-arrow">▼</span>
              </div>
              
              {/* Profile Dropdown */}
              {showProfileMenu && (
                <div className="profile-dropdown">
                  <div className="profile-info">
                    <div className="profile-email">{user?.email}</div>
                    <div className="profile-account">Account: {user?.accountNumber}</div>
                  </div>
                  <div className="profile-actions">
                    <Link 
                      to="/profile" 
                      className="profile-action-link"
                      onClick={() => setShowProfileMenu(false)}
                    >
                      👤 View Profile
                    </Link>
                    <Link 
                      to="/kyc" 
                      className="profile-action-link"
                      onClick={() => setShowProfileMenu(false)}
                    >
                      🔐 KYC Verification
                    </Link>
                    <button 
                      className="profile-action-link logout-link"
                      onClick={handleLogout}
                    >
                      🚪 Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
