
import { useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";

import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Documents from "./pages/Documents";
import Chat from "./pages/Chat";
import Reminders from "./pages/Reminders";
import Account from "./pages/Account";
import Settings from "./pages/Settings";

import "./index.css";
import "./AppShell.css";

function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="auth-loading">
        Loading ProofPocket...
      </div>
    );
  }

  return user ? <Navigate to="/" replace /> : children;
}

function Placeholder({ title }) {
  return (
    <div className="placeholder-page">
      <h1>{title}</h1>
      <p>This feature will be connected to your backend next.</p>
    </div>
  );
}

function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="pp-app-layout">
      <Sidebar
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />

      <main className="pp-main-area">
        <Navbar
          onMenuClick={() => setMobileOpen(true)}
        />

        <div className="pp-page-content">
          <Routes>
            {/* Dashboard */}
            <Route
              path="/"
              element={<Dashboard />}
            />

            {/* Document Management */}
            <Route
              path="/documents"
              element={<Documents />}
            />

            {/* AI Document Chat */}
            <Route
              path="/chat"
              element={<Chat />}
            />

            {/* Reminders */}
            <Route path="/reminders"
             element={<Reminders />} 
            />

            {/* Account */}
            <Route path="/account" 
            element={<Account />} 
            />

            {/* Settings */}
            <Route path="/settings" 
            element={<Settings />} 
            />

            {/* Unknown application route */}
            <Route
              path="*"
              element={<Navigate to="/" replace />}
            />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      {/* Login */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />

      {/* Registration */}
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />

      {/* Protected Application */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
