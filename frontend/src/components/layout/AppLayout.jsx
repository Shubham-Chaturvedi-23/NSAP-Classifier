import React, { useState, useEffect } from "react";
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../app/providers';
import { useTranslation } from 'react-i18next';
import { ROLES } from '../../utils/constants';
import LangSwitcher from '../feedback/LangSwitcher';
import './AppLayout.css';

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const NAV = {
    [ROLES.CITIZEN]: [
      { to: '/citizen/applications', icon: '📋', label: t('nav.applications') },
      { to: '/citizen/apply',        icon: '✏️',  label: t('nav.apply') },
      { to: '/citizen/notifications',icon: '🔔',  label: t('nav.notifications') },
    ],
    [ROLES.OFFICER]: [
      { to: '/officer/queue',        icon: '⚡',  label: t('nav.queue') },
      { to: '/officer/applications', icon: '📂',  label: t('nav.all_apps') },
    ],
    [ROLES.ADMIN]: [
      { to: '/admin/dashboard',   icon: '📊', label: t('nav.dashboard') },
      { to: '/admin/applications',icon: '📂', label: t('nav.all_apps') },
      { to: '/admin/model',       icon: '🤖', label: t('nav.model') },
      { to: '/admin/users',       icon: '👥', label: t('nav.users') },
    ],
  };

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
            <span>{t('nav.profile')}</span>
          </NavLink>
          <button className="nav-item logout-btn" onClick={handleLogout}>
            <span className="nav-icon">🚪</span>
            <span>{t('nav.logout')}</span>
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