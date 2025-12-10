import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import ConfigPage from './pages/ConfigPage'
import LivePage from './pages/LivePage'
import SessionsPage from './pages/SessionsPage'
import './styles.css'

function Layout() {
  return (
    <div className="app">
      <header className="topbar">
        <h1>Charger Simulator Admin</h1>
        <nav>
          <NavLink to="/admin/config" className={({isActive}) => isActive ? 'active' : ''}>Config</NavLink>
          <NavLink to="/admin/live" className={({isActive}) => isActive ? 'active' : ''}>Live</NavLink>
          <NavLink to="/admin/sessions" className={({isActive}) => isActive ? 'active' : ''}>Sessions</NavLink>
        </nav>
      </header>
      <main className="content">
        <Routes>
          <Route path="/admin/config" element={<ConfigPage />} />
          <Route path="/admin/live" element={<LivePage />} />
          <Route path="/admin/sessions" element={<SessionsPage />} />
          <Route path="/admin" element={<Navigate to="/admin/config" replace />} />
        </Routes>
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  </React.StrictMode>
)
