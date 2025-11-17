import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Upload from './pages/Upload'
import Analysis from './pages/Analysis'
import './styles.css'

export default function App(){
  return (
    <div>
      <header className="app-header">
        <div className="page" style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <div className="brand">Attrition Analysis</div>
          <nav className="nav">
            <Link to="/">Home</Link>
            <Link to="/analysis" style={{marginLeft:12}}>Analysis</Link>
          </nav>
        </div>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<Upload/>} />
          <Route path="/analysis" element={<Analysis/>} />
          <Route path="/analysis/:id" element={<Analysis/>} />
        </Routes>
      </main>
      <div className="page footer">Built with care • Attrition Analysis</div>
    </div>
  )
}
