import { useState } from 'react';
import { User, Lock, LogIn, Building2, CheckCircle } from 'lucide-react';
import './AuthModal.css';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (username: string, password: string) => Promise<{ success: boolean; department?: string; error?: string }>;
}

export function AuthModal({ isOpen, onClose, onLogin }: AuthModalProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDepartmentPopup, setShowDepartmentPopup] = useState(false);
  const [department, setDepartment] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const result = await onLogin(username, password);
      if (result.success && result.department) {
        setDepartment(result.department);
        setShowDepartmentPopup(true);
      } else {
        setError(result.error || 'Login failed. Please try again.');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDepartmentAcknowledge = () => {
    setShowDepartmentPopup(false);
    onClose();
  };

  if (!isOpen) return null;

  // Department recognition popup
  if (showDepartmentPopup && department) {
    return (
      <div className="auth-modal-overlay">
        <div className="auth-modal department-popup">
          <div className="department-popup-content">
            <div className="department-icon-wrapper">
              <CheckCircle size={48} className="department-check-icon" />
            </div>
            <h2>Welcome!</h2>
            <div className="department-info">
              <Building2 size={24} />
              <div className="department-details">
                <span className="department-label">Department Identified</span>
                <span className="department-name">{department}</span>
              </div>
            </div>
            <p className="department-message">
              You have been recognized as a member of the <strong>{department}</strong> department.
              Your email access has been configured accordingly.
            </p>
            <button className="btn btn-primary btn-continue" onClick={handleDepartmentAcknowledge}>
              Continue to Email
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Login form
  return (
    <div className="auth-modal-overlay">
      <div className="auth-modal">
        <div className="auth-modal-header">
          <h2>
            <LogIn size={24} />
            Sign In
          </h2>
          {/* Remove close button - user must login to access the app */}
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <p className="auth-description">
            Please sign in to access your email inbox
          </p>

          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">
              <User size={16} />
              Username
            </label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">
              <Lock size={16} />
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-login"
            disabled={isLoading || !username || !password}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>

          <p className="auth-hint">
            Demo credentials: <code>demo</code> / <code>demo123</code>
          </p>
        </form>
      </div>
    </div>
  );
}
