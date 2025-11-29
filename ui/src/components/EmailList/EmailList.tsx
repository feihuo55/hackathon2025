import { useState, useMemo } from 'react';
import { Paperclip, Check, Search, ArrowUpDown } from 'lucide-react';
import type { Email, SelectionState } from '../../types';

interface EmailListProps {
  emails: Email[];
  selection: SelectionState;
  onSelectionChange: (emailId: string, selected: boolean) => void;
  onEmailClick: (email: Email) => void;
  onAnalyze: () => void;
}

type SortOrder = 'newest' | 'oldest';

export function EmailList({
  emails,
  selection,
  onSelectionChange,
  onEmailClick,
  onAnalyze,
}: EmailListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState<SortOrder>('newest');
  const [hoveredEmailId, setHoveredEmailId] = useState<string | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const selectedCount = selection.selectedEmails.length;
  const attachmentCount = selection.selectedAttachments.length;

  // Filter and sort emails
  const filteredEmails = useMemo(() => {
    let result = emails;

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (email) =>
          email.from.toLowerCase().includes(query) ||
          email.subject.toLowerCase().includes(query) ||
          email.summary.toLowerCase().includes(query)
      );
    }

    // Sort by date
    result = [...result].sort((a, b) => {
      // Parse dates (assuming format like "Nov 26")
      const dateA = new Date(a.date + ', 2024');
      const dateB = new Date(b.date + ', 2024');
      return sortOrder === 'newest'
        ? dateB.getTime() - dateA.getTime()
        : dateA.getTime() - dateB.getTime();
    });

    return result;
  }, [emails, searchQuery, sortOrder]);

  const toggleSortOrder = () => {
    setSortOrder((prev) => (prev === 'newest' ? 'oldest' : 'newest'));
  };

  const handleMouseEnter = (email: Email, e: React.MouseEvent) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setTooltipPosition({
      x: rect.right + 10,
      y: rect.top,
    });
    setHoveredEmailId(email.id);
  };

  const handleMouseLeave = () => {
    setHoveredEmailId(null);
  };

  const hoveredEmail = hoveredEmailId ? filteredEmails.find(e => e.id === hoveredEmailId) : null;

  return (
    <div className="list-panel">
      <div className="list-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h2>Emails</h2>
          <button
            className="btn btn-primary btn-sm"
            onClick={onAnalyze}
            disabled={selectedCount === 0}
          >
            Analyze Selected
          </button>
        </div>

        {/* Search and Sort Controls */}
        <div className="email-controls">
          <div className="search-box">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Search emails..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
          <button
            className="sort-btn"
            onClick={toggleSortOrder}
            title={`Sort by date: ${sortOrder === 'newest' ? 'Newest first' : 'Oldest first'}`}
          >
            <ArrowUpDown size={16} />
            <span>{sortOrder === 'newest' ? 'Newest' : 'Oldest'}</span>
          </button>
        </div>

      </div>
      <div className="list-content">
        {filteredEmails.length === 0 ? (
          <div className="empty-list">
            {searchQuery ? 'No emails match your search.' : 'No emails available.'}
          </div>
        ) : (
          filteredEmails.map((email) => {
            const isSelected = selection.selectedEmails.includes(email.id);
            const hasSelection = selectedCount > 0;
            const isDisabled = hasSelection && !isSelected;

            return (
              <div
                key={email.id}
                className={`email-item ${isSelected ? 'selected' : ''} ${isDisabled ? 'disabled' : ''}`}
                onClick={() => onEmailClick(email)}
                onMouseEnter={(e) => handleMouseEnter(email, e)}
                onMouseLeave={handleMouseLeave}
              >
                <div className="email-checkbox" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    disabled={isDisabled}
                    onChange={(e) => onSelectionChange(email.id, e.target.checked)}
                  />
                </div>
              <div className="email-content">
                <div className="email-from">{email.from}</div>
                <div className="email-subject">{email.subject}</div>
                <div className="email-summary">{email.summary}</div>
              </div>
              <div className="email-meta">
                <span className="email-date">{email.date}</span>
                {email.hasAttachment && (
                  <span className="email-attachment">
                    <Paperclip size={14} />
                    <Check size={12} />
                  </span>
                )}
              </div>
            </div>
            );
          })
        )}
      </div>

      {/* Email Content Tooltip */}
      {hoveredEmail && (
        <div
          className="email-tooltip"
          style={{
            position: 'fixed',
            left: tooltipPosition.x,
            top: tooltipPosition.y,
            zIndex: 1000,
          }}
        >
          <div className="email-tooltip-header">
            <span className="email-tooltip-from">{hoveredEmail.from}</span>
            <span className="email-tooltip-date">{hoveredEmail.date}</span>
          </div>
          <div className="email-tooltip-subject">{hoveredEmail.subject}</div>
          <div className="email-tooltip-body">
            {hoveredEmail.body || hoveredEmail.summary}
          </div>
          {hoveredEmail.hasAttachment && hoveredEmail.attachments.length > 0 && (
            <div className="email-tooltip-attachments">
              <Paperclip size={12} />
              <span>{hoveredEmail.attachments.length} attachment(s): {hoveredEmail.attachments.map(a => a.name).join(', ')}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
