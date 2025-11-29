import { MessageSquare } from 'lucide-react';
import { ChatWindow } from '../ChatWindow/ChatWindow';
import type { AnalysisResult, ChatMessage, SIPOCDocument, AnalysisSession } from '../../types';

interface AnalysisPanelProps {
  analysisResult: AnalysisResult | null;
  messages: ChatMessage[];
  sipocDocument: SIPOCDocument | null;
  workflowSipoc?: SIPOCDocument | null;
  isLoading: boolean;
  analysisSessions: AnalysisSession[];
  onToggleSessionCollapse: (sessionId: string) => void;
  onSendMessage: (message: string) => void;
  onActionClick: (actionType: string, optionValue?: string) => void;
  onInputSubmit?: (inputValue: string, placeholder?: string) => void;
  onGenerateSipoc?: (sipoc: SIPOCDocument) => void;
  onCollaborationComplete?: (sessionId: string) => void;
}

export function AnalysisPanel({
  analysisResult,
  messages,
  sipocDocument,
  workflowSipoc,
  isLoading,
  analysisSessions,
  onToggleSessionCollapse,
  onSendMessage,
  onActionClick,
  onInputSubmit,
  onGenerateSipoc,
  onCollaborationComplete,
}: AnalysisPanelProps) {
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
          <p>
            <span className="label">Detected Intent:</span> {analysisResult.userIntent}
          </p>
          <p>
            <span className="label">Suggested Action:</span> {analysisResult.suggestedAction}
          </p>
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
