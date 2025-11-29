import { useState, useEffect } from 'react';
import { MessageSquare, Edit2, Check, X, ArrowRight, Database, Search, Cpu, Loader2 } from 'lucide-react';
import { ChatWindow } from '../ChatWindow/ChatWindow';
import type { AnalysisResult, ChatMessage, SIPOCDocument, AnalysisSession, ServiceExecutionResult } from '../../types';

interface AnalysisPanelProps {
  analysisResult: AnalysisResult | null;
  messages: ChatMessage[];
  sipocDocument: SIPOCDocument | null;
  workflowSipoc?: SIPOCDocument | null;
  serviceExecutionResult?: ServiceExecutionResult | null;
  isLoading: boolean;
  analysisSessions: AnalysisSession[];
  onToggleSessionCollapse: (sessionId: string) => void;
  onSendMessage: (message: string) => void;
  onActionClick: (actionType: string, optionValue?: string) => void;
  onInputSubmit?: (inputValue: string, placeholder?: string) => void;
  onGenerateSipoc?: (sipoc: SIPOCDocument) => void;
  onCollaborationComplete?: (sessionId: string) => void;
  onAnalysisUpdate?: (updatedIntent: string, updatedAction: string) => void;
  onGoOn?: () => void;
  onReanalyze?: (updatedIntent: string, updatedAction: string) => void;
}

// Update notification for when user edits analysis
interface UpdateNotification {
  type: 'Memory' | 'RAG' | 'Service';
  name: string;
  action: string;
}

export function AnalysisPanel({
  analysisResult,
  messages,
  sipocDocument,
  workflowSipoc,
  serviceExecutionResult,
  isLoading,
  analysisSessions,
  onToggleSessionCollapse,
  onSendMessage,
  onActionClick,
  onInputSubmit,
  onGenerateSipoc,
  onCollaborationComplete,
  onAnalysisUpdate,
  onGoOn,
  onReanalyze,
}: AnalysisPanelProps) {
  // Editable fields state
  const [isEditingIntent, setIsEditingIntent] = useState(false);
  const [isEditingAction, setIsEditingAction] = useState(false);
  const [editedIntent, setEditedIntent] = useState('');
  const [editedAction, setEditedAction] = useState('');
  const [intentModified, setIntentModified] = useState(false);
  const [actionModified, setActionModified] = useState(false);
  const [isProcessingUpdate, setIsProcessingUpdate] = useState(false);
  const [updateNotifications, setUpdateNotifications] = useState<UpdateNotification[]>([]);
  const [updateComplete, setUpdateComplete] = useState(false);

  // Initialize edited values when analysisResult changes
  useEffect(() => {
    if (analysisResult) {
      setEditedIntent(analysisResult.userIntent);
      setEditedAction(analysisResult.suggestedAction);
      setIntentModified(false);
      setActionModified(false);
      setUpdateNotifications([]);
      setUpdateComplete(false);
    }
  }, [analysisResult]);

  // Handle intent edit confirmation - just save the edit, don't process yet
  const handleIntentConfirm = () => {
    if (editedIntent !== analysisResult?.userIntent) {
      setIntentModified(true);
    }
    setIsEditingIntent(false);
  };

  // Handle action edit confirmation - just save the edit, don't process yet
  const handleActionConfirm = () => {
    if (editedAction !== analysisResult?.suggestedAction) {
      setActionModified(true);
    }
    setIsEditingAction(false);
  };

  // Handle key press for input fields
  const handleIntentKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleIntentConfirm();
    } else if (e.key === 'Escape') {
      setEditedIntent(analysisResult?.userIntent || '');
      setIsEditingIntent(false);
    }
  };

  const handleActionKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleActionConfirm();
    } else if (e.key === 'Escape') {
      setEditedAction(analysisResult?.suggestedAction || '');
      setIsEditingAction(false);
    }
  };

  // Handle Go On button click
  const handleGoOn = async () => {
    const hasModifications = intentModified || actionModified;

    if (hasModifications) {
      // User made modifications - process updates and reanalyze
      setIsProcessingUpdate(true);

      // Simulate AI processing
      await new Promise(resolve => setTimeout(resolve, 800));

      // Generate update notifications based on what was modified
      const updates: UpdateNotification[] = [];

      if (intentModified) {
        updates.push(
          { type: 'Memory', name: 'IntentRecognitionMemory', action: 'Updated intent patterns' },
          { type: 'RAG', name: 'EmailIntentRAG', action: 'Recalibrated intent vectors' }
        );
      }

      if (actionModified) {
        updates.push(
          { type: 'Service', name: 'ActionRecommendationService', action: 'Updated action mappings' },
          { type: 'Memory', name: 'WorkflowActionMemory', action: 'Adjusted action suggestions' }
        );
      }

      setUpdateNotifications(updates);
      setIsProcessingUpdate(false);
      setUpdateComplete(true);

      // After showing updates, trigger reanalysis
      setTimeout(() => {
        if (onAnalysisUpdate) {
          onAnalysisUpdate(editedIntent, editedAction);
        }
        if (onReanalyze) {
          onReanalyze(editedIntent, editedAction);
        }
      }, 1500); // Give user time to see the updates

    } else {
      // No modifications - continue to next step
      if (onAnalysisUpdate) {
        onAnalysisUpdate(editedIntent, editedAction);
      }
      if (onGoOn) {
        onGoOn();
      }
    }
  };

  // Check if any field has been modified
  const hasModifications = intentModified || actionModified;

  return (
    <div className="analysis-panel">
      <div className="analysis-header">
        <h2>
          <MessageSquare size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          AI Analysis & Chat
        </h2>
      </div>

      {analysisResult && (
        <div className="analysis-result">
          <h3>Analysis Result</h3>
          <p>
            <span className="label">Subject:</span> {analysisResult.emailSubject}
          </p>
          <p>
            <span className="label">Summary:</span> {analysisResult.summary}
          </p>
          {analysisResult.attachments.length > 0 && (
            <p>
              <span className="label">Attachments:</span>{' '}
              {analysisResult.attachments.join(', ')}
            </p>
          )}

          {/* Editable Detected Intent - looks like normal text, click to edit */}
          {isEditingIntent ? (
            <div className="editable-field-editing">
              <span className="label">Detected Intent:</span>
              <div className="edit-input-container">
                <input
                  type="text"
                  className="edit-input"
                  value={editedIntent}
                  onChange={(e) => setEditedIntent(e.target.value)}
                  onKeyDown={handleIntentKeyPress}
                  autoFocus
                />
                <button className="edit-confirm-btn" onClick={handleIntentConfirm} title="Confirm (Enter)">
                  <Check size={14} />
                </button>
                <button className="edit-cancel-btn" onClick={() => {
                  setEditedIntent(analysisResult.userIntent);
                  setIsEditingIntent(false);
                }} title="Cancel (Esc)">
                  <X size={14} />
                </button>
              </div>
            </div>
          ) : (
            <p className={`editable-text ${intentModified ? 'modified' : ''}`} onClick={() => setIsEditingIntent(true)}>
              <span className="label">Detected Intent:</span> {editedIntent}
              <Edit2 size={12} className="edit-hint-icon" />
              {intentModified && <span className="modified-badge">Modified</span>}
            </p>
          )}

          {/* Editable Suggested Action - looks like normal text, click to edit */}
          {isEditingAction ? (
            <div className="editable-field-editing">
              <span className="label">Suggested Action:</span>
              <div className="edit-input-container">
                <input
                  type="text"
                  className="edit-input"
                  value={editedAction}
                  onChange={(e) => setEditedAction(e.target.value)}
                  onKeyDown={handleActionKeyPress}
                  autoFocus
                />
                <button className="edit-confirm-btn" onClick={handleActionConfirm} title="Confirm (Enter)">
                  <Check size={14} />
                </button>
                <button className="edit-cancel-btn" onClick={() => {
                  setEditedAction(analysisResult.suggestedAction);
                  setIsEditingAction(false);
                }} title="Cancel (Esc)">
                  <X size={14} />
                </button>
              </div>
            </div>
          ) : (
            <p className={`editable-text ${actionModified ? 'modified' : ''}`} onClick={() => setIsEditingAction(true)}>
              <span className="label">Suggested Action:</span> {editedAction}
              <Edit2 size={12} className="edit-hint-icon" />
              {actionModified && <span className="modified-badge">Modified</span>}
            </p>
          )}

          {/* Update notifications when Go On is clicked */}
          {isProcessingUpdate && (
            <div className="analysis-update-processing">
              <Loader2 size={14} className="spinner-icon" />
              <span>AI updating related components...</span>
            </div>
          )}

          {updateNotifications.length > 0 && !isProcessingUpdate && (
            <div className="analysis-updates">
              <div className="analysis-updates-header">
                <span>AI Updated Components:</span>
              </div>
              <div className="analysis-updates-list">
                {updateNotifications.map((update, index) => (
                  <div key={index} className="analysis-update-item">
                    <span className={`update-type ${update.type.toLowerCase()}`}>
                      {update.type === 'Service' && <Cpu size={12} />}
                      {update.type === 'Memory' && <Database size={12} />}
                      {update.type === 'RAG' && <Search size={12} />}
                      {update.type}
                    </span>
                    <span className="update-name">{update.name}</span>
                    <span className="update-action">{update.action}</span>
                  </div>
                ))}
              </div>
              {updateComplete && (
                <div className="analysis-reanalyzing">
                  <Loader2 size={14} className="spinner-icon" />
                  <span>Reanalyzing email with updated components...</span>
                </div>
              )}
            </div>
          )}

          {/* Go On button - changes behavior based on modifications */}
          {!updateComplete && (
            <div className="analysis-result-actions">
              <button
                className={`btn btn-go-on-analysis ${hasModifications ? 'has-modifications' : ''}`}
                onClick={handleGoOn}
                disabled={isEditingIntent || isEditingAction || isProcessingUpdate}
              >
                {hasModifications ? 'Update & Reanalyze' : 'Go On'}
                <ArrowRight size={16} />
              </button>
              {hasModifications && (
                <p className="modification-hint">Your changes will be saved and email will be reanalyzed</p>
              )}
            </div>
          )}
        </div>
      )}

      {!analysisResult && messages.length === 0 && !isLoading && analysisSessions.length === 0 && (
        <div className="empty-state" style={{ flex: 1 }}>
          <MessageSquare size={64} />
          <h3>No Analysis Yet</h3>
          <p>Select emails and click "Analyze" to start AI analysis</p>
        </div>
      )}

      {(analysisResult || messages.length > 0 || isLoading || analysisSessions.length > 0) && (
        <ChatWindow
          messages={messages}
          onSendMessage={onSendMessage}
          onActionClick={onActionClick}
          onInputSubmit={onInputSubmit}
          sipocDocument={sipocDocument}
          workflowSipoc={workflowSipoc}
          serviceExecutionResult={serviceExecutionResult}
          isLoading={isLoading}
          analysisSessions={analysisSessions}
          onToggleSessionCollapse={onToggleSessionCollapse}
          onGenerateSipoc={onGenerateSipoc}
          onCollaborationComplete={onCollaborationComplete}
        />
      )}
    </div>
  );
}
