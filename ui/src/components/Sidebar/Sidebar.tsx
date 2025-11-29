import { Mail } from 'lucide-react';

interface SidebarProps {
  activeTab: 'email' | null;
  onTabChange: (tab: 'email' | null) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const handleTabClick = () => {
    // Toggle: if clicking active tab, deselect it
    if (activeTab === 'email') {
      onTabChange(null);
    } else {
      onTabChange('email');
    }
  };

  return (
    <div className="sidebar">
      <div
        className={`sidebar-tab ${activeTab === 'email' ? 'active' : ''}`}
        onClick={handleTabClick}
      >
        <Mail className="sidebar-tab-icon" />
        <span className="sidebar-tab-label">Email</span>
      </div>
    </div>
  );
}
