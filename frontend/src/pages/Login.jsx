import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Auth.css';
import API from '../api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(API.login, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Login failed');
        return;
      }

      // Store user info in localStorage
      localStorage.setItem('user', JSON.stringify(data));
      localStorage.setItem('user_id', data.user_id);

      // Trigger a custom event so App component knows to update
      window.dispatchEvent(new Event('userLoggedIn'));

      // Redirect to main app after a short delay
      setTimeout(() => {
        navigate('/');
      }, 100);
    } catch (err) {
      setError('Error connecting to server: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Preflight: check backend health once when page loads
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(API.health);
        if (!res.ok) throw new Error('Backend unhealthy');
      } catch (err) {
        setError('Backend unreachable. Is server running on port 8000?');
      }
    };
    checkHealth();
  }, []);

  return (
    <div className="auth-container">
      <div className="auth-box">
        <h1>HR Portal Login</h1>
        <p className="subtitle">Employee Attrition Analysis System</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button type="submit" disabled={loading} className="login-btn">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="signup-link">
          Don't have an account?{' '}
          <button 
            type="button" 
            onClick={() => navigate('/signup')}
            className="create-account-btn"
          >
            Create Account
          </button>
        </div>
      </div>
    </div>
  );
}
     /*login*/