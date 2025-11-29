import { useState } from 'react';
import { Folder as FolderIcon, FileText, ChevronRight } from 'lucide-react';
import type { Folder } from '../../types';

interface FolderListProps {
  folders: Folder[];
  onFolderClick: (folder: Folder) => void;
}

function FolderItem({
  folder,
  depth = 0,
  onFolderClick,
}: {
  folder: Folder;
  depth?: number;
  onFolderClick: (folder: Folder) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasChildren = folder.children && folder.children.length > 0;

  const handleClick = () => {
    if (hasChildren) {
      setIsExpanded(!isExpanded);
    }
    onFolderClick(folder);
  };

  return (
    <>
      <div
        className={`folder-item ${depth > 0 ? 'subfolder' : ''}`}
        style={{ paddingLeft: `${16 + depth * 24}px` }}
        onClick={handleClick}
      >
        {hasChildren && (
          <ChevronRight
            className={`folder-expand ${isExpanded ? 'expanded' : ''}`}
            size={16}
          />
        )}
        {folder.type === 'folder' ? (
          <FolderIcon className="folder-icon" size={20} />
        ) : (
          <FileText className="folder-icon" size={20} />
        )}
        <span className="folder-name">{folder.name}</span>
      </div>
      {isExpanded && folder.children && (
        <>
          {folder.children.map((child) => (
            <FolderItem
              key={child.id}
              folder={child}
              depth={depth + 1}
              onFolderClick={onFolderClick}
            />
          ))}
        </>
      )}
    </>
  );
}

export function FolderList({ folders, onFolderClick }: FolderListProps) {
  return (
    <div className="list-panel">
      <div className="list-header">
        <h2>Attachments</h2>
      </div>
      <div className="list-content">
        {folders.length === 0 ? (
          <div className="empty-state">
            <FolderIcon size={48} />
            <h3>No attachments</h3>
            <p>Downloaded attachments will appear here</p>
          </div>
        ) : (
          folders.map((folder) => (
            <FolderItem
              key={folder.id}
              folder={folder}
              onFolderClick={onFolderClick}
            />
          ))
        )}
      </div>
    </div>
  );
}
