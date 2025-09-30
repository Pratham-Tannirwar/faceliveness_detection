import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Home.css';

const Home = () => {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <h1 className="hero-title">
              {isAuthenticated ? `Welcome back, ${user?.fullName || 'User'}!` : 'Welcome to Mock Bank'}
            </h1>
            <p className="hero-subtitle">
              {isAuthenticated 
                ? 'Manage your account and explore our banking services.'
                : 'Your trusted banking partner for all financial needs. Experience secure, reliable, and innovative banking solutions.'
              }
            </p>
            {!isAuthenticated && (
              <button className="cta-button">
                Get Started
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Quick Links Section */}
      <section className="quick-links-section">
        <div className="quick-links-container">
          <h2 className="section-title">Quick Access</h2>
          <div className="cards-grid">
            {/* Show Login/Signup only for guests */}
            {!isAuthenticated && (
              <>
                {/* Login Card */}
                <div className="quick-link-card">
                  <div className="card-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M20.59 22C20.59 18.13 16.74 15 12 15C7.26 15 3.41 18.13 3.41 22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <h3 className="card-title">Login</h3>
                  <p className="card-description">
                    Access your account securely with your credentials
                  </p>
                  <Link to="/login" className="card-link">
                    Login Now →
                  </Link>
                </div>

                {/* Signup Card */}
                <div className="quick-link-card">
                  <div className="card-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M16 21V19C16 17.9391 15.5786 16.9217 14.8284 16.1716C14.0783 15.4214 13.0609 15 12 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <circle cx="8.5" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M20 8V14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M17 11H23" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <h3 className="card-title">Sign Up</h3>
                  <p className="card-description">
                    Create a new account and start your banking journey
                  </p>
                  <Link to="/signup" className="card-link">
                    Sign Up Now →
                  </Link>
                </div>
              </>
            )}

            {/* KYC Card - Show for both authenticated and guest users */}
            <div className="quick-link-card">
              <div className="card-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M8 21H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M12 17V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M9 9H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M9 13H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3 className="card-title">KYC Verification</h3>
              <p className="card-description">
                Complete your Know Your Customer verification process
              </p>
              <Link to="/kyc" className="card-link">
                Verify Now →
              </Link>
            </div>

            {/* Additional cards for authenticated users */}
            {isAuthenticated && (
              <>
                {/* Profile Card */}
                <div className="quick-link-card">
                  <div className="card-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <h3 className="card-title">Profile</h3>
                  <p className="card-description">
                    View and manage your account information
                  </p>
                  <Link to="/profile" className="card-link">
                    View Profile →
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
