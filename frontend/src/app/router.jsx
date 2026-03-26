import React, { useState, useEffect } from "react";
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './providers';
import { ROLES } from '../utils/constants';
import { getRoleHomePath } from '../utils/guards';

// Layout
import AppLayout from '../components/layout/AppLayout';

// Auth pages
import LoginPage from '../features/auth/LoginPage';
import RegisterPage from '../features/auth/RegisterPage';
import ProfilePage from '../features/auth/ProfilePage';

// Citizen pages
import CitizenApplicationsPage from '../features/citizen/ApplicationsPage';
import CitizenApplyPage from '../features/citizen/ApplyPage';
import CitizenApplicationDetail from '../features/citizen/ApplicationDetail';
import CitizenNotificationsPage from '../features/citizen/NotificationsPage';

// Officer pages
import OfficerQueuePage from '../features/officer/QueuePage';
import OfficerApplicationsPage from '../features/officer/ApplicationsPage';
import OfficerReviewPage from '../features/officer/ReviewPage';

// Admin pages
import AdminDashboard from '../features/admin/DashboardPage';
import AdminApplicationsPage from '../features/admin/ApplicationsPage';
import AdminModelPage from '../features/admin/ModelPage';
import AdminUsersPage from '../features/admin/UsersPage';

const RequireAuth = ({ children, roles }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading"><div className="spinner" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={getRoleHomePath(user.role)} replace />;
  return children;
};

const PublicOnly = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading"><div className="spinner" /></div>;
  if (user) return <Navigate to={getRoleHomePath(user.role)} replace />;
  return children;
};

export default function AppRouter() {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Public */}
      <Route path="/login"    element={<PublicOnly><LoginPage /></PublicOnly>} />
      <Route path="/register" element={<PublicOnly><RegisterPage /></PublicOnly>} />

      {/* Protected */}
      <Route element={<RequireAuth><AppLayout /></RequireAuth>}>
        <Route path="/profile" element={<ProfilePage />} />

        {/* Citizen */}
        <Route path="/citizen/applications"      element={<RequireAuth roles={[ROLES.CITIZEN]}><CitizenApplicationsPage /></RequireAuth>} />
        <Route path="/citizen/apply"             element={<RequireAuth roles={[ROLES.CITIZEN]}><CitizenApplyPage /></RequireAuth>} />
        <Route path="/citizen/applications/:id"  element={<RequireAuth roles={[ROLES.CITIZEN]}><CitizenApplicationDetail /></RequireAuth>} />
        <Route path="/citizen/notifications"     element={<RequireAuth roles={[ROLES.CITIZEN]}><CitizenNotificationsPage /></RequireAuth>} />

        {/* Officer */}
        <Route path="/officer/queue"             element={<RequireAuth roles={[ROLES.OFFICER]}><OfficerQueuePage /></RequireAuth>} />
        <Route path="/officer/applications"      element={<RequireAuth roles={[ROLES.OFFICER]}><OfficerApplicationsPage /></RequireAuth>} />
        <Route path="/officer/applications/:id"  element={<RequireAuth roles={[ROLES.OFFICER]}><OfficerReviewPage /></RequireAuth>} />

        {/* Admin */}
        <Route path="/admin/dashboard"   element={<RequireAuth roles={[ROLES.ADMIN]}><AdminDashboard /></RequireAuth>} />
        <Route path="/admin/applications" element={<RequireAuth roles={[ROLES.ADMIN]}><AdminApplicationsPage /></RequireAuth>} />
        <Route path="/admin/model"       element={<RequireAuth roles={[ROLES.ADMIN]}><AdminModelPage /></RequireAuth>} />
        <Route path="/admin/users"       element={<RequireAuth roles={[ROLES.ADMIN]}><AdminUsersPage /></RequireAuth>} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={
        user ? <Navigate to={getRoleHomePath(user.role)} replace /> : <Navigate to="/login" replace />
      } />
    </Routes>
  );
}