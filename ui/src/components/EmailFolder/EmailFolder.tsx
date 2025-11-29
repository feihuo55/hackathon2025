import { Folder, FolderOpen, Inbox, Send, Archive, Trash2, Star, AlertCircle } from 'lucide-react';
import './EmailFolder.css';

export interface EmailFolderItem {
  id: string;
  name: string;
  icon: 'inbox' | 'sent' | 'archive' | 'trash' | 'starred' | 'important' | 'folder';
  count: number;
  isSelected?: boolean;
}

interface EmailFolderProps {
  folders: EmailFolderItem[];
  selectedFolderId: string | null;
  onFolderSelect: (folderId: string) => void;
}

export function EmailFolder({ folders, selectedFolderId, onFolderSelect }: EmailFolderProps) {
  const getIcon = (iconType: EmailFolderItem['icon'], isSelected: boolean) => {
    const size = 18;
    switch (iconType) {
      case 'inbox':
        return <Inbox size={size} />;
      case 'sent':
        return <Send size={size} />;
      case 'archive':
        return <Archive size={size} />;
      case 'trash':
        return <Trash2 size={size} />;
      case 'starred':
        return <Star size={size} />;
      case 'important':
        return <AlertCircle size={size} />;
      case 'folder':
      default:
        return isSelected ? <FolderOpen size={size} /> : <Folder size={size} />;
    }
  };

  return (
    <div className="email-folder-list">
      <div className="folder-header">
        <h3>Email Folders</h3>
      </div>
      <div className="folder-items">
        {folders.map((folder) => (
          <div
            key={folder.id}
            className={`folder-item ${selectedFolderId === folder.id ? 'selected' : ''}`}
            onClick={() => onFolderSelect(folder.id)}
          >
            <span className="folder-icon">
              {getIcon(folder.icon, selectedFolderId === folder.id)}
            </span>
            <span className="folder-name">{folder.name}</span>
            {folder.count > 0 && (
              <span className="folder-count">{folder.count}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
