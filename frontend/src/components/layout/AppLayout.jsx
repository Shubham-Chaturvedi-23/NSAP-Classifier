import React, { useState, useEffect } from "react";
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../app/providers';
import { ROLES } from '../../utils/constants';
import LangSwitcher from '../feedback/LangSwitcher';
import './AppLayout.css';

const NAV = {
  [ROLES.CITIZEN]: [
    { to: '/citizen/applications', icon: '📋', label: 'My Applications' },
    { to: '/citizen/apply',        icon: '✏️',  label: 'New Application' },
    { to: '/citizen/notifications',icon: '🔔',  label: 'Notifications' },
  ],
  [ROLES.OFFICER]: [
    { to: '/officer/queue',        icon: '⚡',  label: 'Review Queue' },
    { to: '/officer/applications', icon: '📂',  label: 'All Applications' },
  ],
  [ROLES.ADMIN]: [
    { to: '/admin/dashboard',   icon: '📊', label: 'Dashboard' },
    { to: '/admin/applications',icon: '📂', label: 'Applications' },
    { to: '/admin/model',       icon: '🤖', label: 'Model Metrics' },
    { to: '/admin/users',       icon: '👥', label: 'Users' },
  ],
};

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const navItems = NAV[user?.role] || [];

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">⚖️</span>
          <div>
            <div className="brand-name">NSAP</div>
            <div className="brand-sub">Scheme System</div>
          </div>
        </div>

        <div className="sidebar-role">
          <span className={`role-badge role-${user?.role}`}>{user?.role?.toUpperCase()}</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <NavLink to="/profile" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">👤</span>
            <span>Profile</span>
          </NavLink>
          <button className="nav-item logout-btn" onClick={handleLogout}>
            <span className="nav-icon">🚪</span>
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div />
          <div className="topbar-user">
            <LangSwitcher />
            <span className="user-name">{user?.name || user?.email}</span>
          </div>
        </header>
        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}