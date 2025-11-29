import { Server, FolderSync, CheckCircle2, ArrowRight } from 'lucide-react';
import './PermissionModal.css';

export interface ServicePermission {
  id: string;
  name: string;
  description: string;
}

export interface SharedFolder {
  id: string;
  name: string;
  emailCount: number;
}

interface PermissionModalProps {
  isOpen: boolean;
  department: string;
  services: ServicePermission[];
  sharedFolders: SharedFolder[];
  onContinue: () => void;
}

export function PermissionModal({
  isOpen,
  department,
  services,
  sharedFolders,
  onContinue,
}: PermissionModalProps) {
  if (!isOpen) return null;

  return (
    <div className="permission-modal-overlay">
      <div className="permission-modal">
        <div className="permission-header">
          <CheckCircle2 size={32} className="permission-check-icon" />
          <h2>Access Permissions Loaded</h2>
          <p className="permission-subtitle">
            Based on your <strong>{department}</strong> department permissions
          </p>
        </div>

        <div className="permission-content">
          {/* Connected Services Section */}
          <div className="permission-section">
            <div className="section-header">
              <Server size={20} />
              <h3>Connected Services</h3>
            </div>
            <div className="section-list">
              {services.map((service) => (
                <div key={service.id} className="permission-item service-item">
                  <div className="item-indicator"></div>
                  <div className="item-content">
                    <span className="item-name">{service.name}</span>
                    <span className="item-description">{service.description}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Shared Folders Section */}
          <div className="permission-section">
            <div className="section-header">
              <FolderSync size={20} />
              <h3>Monitored Folders</h3>
            </div>
            <div className="section-list">
              {sharedFolders.map((folder) => (
                <div key={folder.id} className="permission-item folder-item">
                  <div className="item-indicator"></div>
                  <div className="item-content">
                    <span className="item-name">{folder.name}</span>
                    <span className="item-count">{folder.emailCount} emails</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <button className="btn btn-primary btn-continue" onClick={onContinue}>
          Continue to Email
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}
