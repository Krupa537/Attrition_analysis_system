import React, { useState, useEffect } from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import Upload from './pages/Upload'
import Analysis from './pages/Analysis'
import Login from './pages/Login'
import Signup from './pages/Signup'
import './styles.css'

export default function App(){
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is logged in
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('user');
        setUser(null);
      }
    }
  }, []);

  // Listen for storage changes from login/logout
  useEffect(() => {
    const handleStorageChange = () => {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {
          setUser(null);
        }
      } else {
        setUser(null);
      }
    };

    const handleUserLoggedIn = () => {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {
          setUser(null);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('userLoggedIn', handleUserLoggedIn);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('userLoggedIn', handleUserLoggedIn);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('user_id');
    setUser(null);
    navigate('/login');
  };

  // If user is not logged in, show login/signup pages
  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  return (
    <div>
      <header className="app-header">
        <div className="page" style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <div className="brand">Attrition Analysis - HR Portal</div>
          <nav className="nav">
            <Link to="/">Home</Link>
            <Link to="/analysis" style={{marginLeft:12}}>Analysis</Link>
            <div style={{marginLeft: 20, display: 'flex', alignItems: 'center', gap: '10px'}}>
              <span style={{color: '#666', fontSize: '14px'}}>Welcome, {user.full_name}</span>
              <button 
                onClick={handleLogout}
                style={{
                  background: '#667eea',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '5px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Logout
              </button>
            </div>
          </nav>
        </div>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<Upload/>} />
          <Route path="/analysis" element={<Analysis/>} />
          <Route path="/analysis/:id" element={<Analysis/>} />
          <Route path="/dashboard" element={<Upload/>} />
        </Routes>
      </main>
      <div className="page footer">Built with care • Attrition Analysis | Logged in as: {user.email}</div>
    </div>
  )
}
/* ui_styling_layout - at-risk employee list */
/*full_dockerfile*/