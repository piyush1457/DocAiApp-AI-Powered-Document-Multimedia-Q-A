import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/useAuthStore';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { FileLibrary } from './pages/FileLibrary';
import { ChatView } from './pages/ChatView';

import { Navbar } from './components/layout/Navbar';

// Protected Route wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar />
      <main className="flex-1 overflow-auto bg-background">
        {children}
      </main>
    </div>
  );
};

// Public Route wrapper (redirects to / if already logged in)
const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return <main className="min-h-screen bg-background">{children}</main>;
};

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
      
      <Route path="/" element={<ProtectedRoute><FileLibrary /></ProtectedRoute>} />
      <Route path="/chat/:fileId" element={<ProtectedRoute><ChatView /></ProtectedRoute>} />
      
      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
