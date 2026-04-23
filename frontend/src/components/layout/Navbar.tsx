import React from 'react';
import { useAuthStore } from '../../store/useAuthStore';
import { Button } from '../ui/Button';
import { LogOut, FileBox } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';

export const Navbar = () => {
  const { logout, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!isAuthenticated) return null;

  return (
    <nav className="h-14 border-b border-border bg-panel flex items-center justify-between px-6 shrink-0">
      <Link to="/" className="flex items-center gap-2 text-textPrimary hover:text-accent transition-colors">
        <FileBox className="w-5 h-5 text-accent" />
        <span className="font-bold tracking-tight">DocAiApp</span>
      </Link>
      
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={handleLogout} className="text-textSecondary">
          <LogOut className="w-4 h-4 mr-2" />
          Logout
        </Button>
      </div>
    </nav>
  );
};
