import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, CheckCircle, ChevronDown, ChevronUp, Users, Bot, Briefcase, Code, Check, Edit2, Brain, Database, Cpu, FileCode, Workflow, Zap, Search } from 'lucide-react';
import { BPMWorkflow } from '../BPMWorkflow/BPMWorkflow';
import type { ChatMessage, SIPOCDocument, AnalysisSession, CollaborationSession, ProcessingStep, ThinkingPoint, AgentThinking, StepDetail } from '../../types';

interface ChatWindowProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  onActionClick: (actionType: string, optionValue?: string, optionLabel?: string) => void;
  onInputSubmit?: (inputValue: string, placeholder?: string) => void;
  sipocDocument: SIPOCDocument | null;
  workflowSipoc?: SIPOCDocument | null;
  isLoading: boolean;
  analysisSessions: AnalysisSession[];
  onToggleSessionCollapse: (sessionId: string) => void;
  onGenerateSipoc?: (sipoc: SIPOCDocument) => void;
  onCollaborationComplete?: (sessionId: string) => void;
}

// Simple markdown parser for bold text
function renderMarkdown(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    // Handle newlines
    return part.split('\n').map((line, lineIndex, arr) => (
      <span key={`${index}-${lineIndex}`}>
        {line}
        {lineIndex < arr.length - 1 && <br />}
      </span>
    ));
  });
}

// Default SIPOC based on framework template (fund_dividend_processing)
const DEFAULT_SIPOC: SIPOCDocument = {
  suppliers: [
    "Fund Company",
    "Custody Bank Database",
    "Investor Account System",
  ],
  inputs: [
    "Dividend Fund List",
    "Distribution Method (Cash/Reinvest)",
    "Record Date",
    "Ex-Dividend Date",
  ],
  process: [
    "1. Retrieve pending dividend fund list",
    "2. Validate fund dividend information",
    "3. Calculate dividend amount per account",
    "4. Execute dividend distribution",
    "5. Update account balances",
    "6. Generate dividend report",
  ],
  outputs: [
    "Dividend Processing Results",
    "Account Balance Change Records",
    "Dividend Report",
  ],
  customers: [
    "Investors",
    "Fund Managers",
    "Regulatory Authorities",
  ],
};

// Interactive Collaboration Panel Component - Shows agents collaborating with editable thinking points
function CollaborationPanel({
  collaboration,
  onGenerate,
  onCollaborationComplete,
}: {
  collaboration: CollaborationSession;
  onGenerate?: (sipoc: SIPOCDocument) => void;
  onCollaborationComplete?: (sipoc: SIPOCDocument) => void;
}) {
  // Local state for interactive editing
  const [currentAgentIndex, setCurrentAgentIndex] = useState(0);
  const [agentThinkings, setAgentThinkings] = useState<AgentThinking[]>(() => {
    // Initialize with default thinking points for each agent
    const agents = ['ai', 'ba', 'tech'];
    return agents.map(agentId => ({
      agentId,
      thinkingPoints: getInitialThinkingPoints(agentId),
      isComplete: false,
    }));
  });
  const [isCollaborationComplete, setIsCollaborationComplete] = useState(false);
  const inputRefs = useRef<{ [key: string]: HTMLInputElement | null }>({});

  // Get the SIPOC to display - use backend data if available, otherwise use default
  const generatedSipoc = collaboration.generatedSipoc || DEFAULT_SIPOC;

  // Get initial thinking points for each agent
  function getInitialThinkingPoints(agentId: string): ThinkingPoint[] {
    switch (agentId) {
      case 'ai':
        return [
          { id: 'ai-1', content: 'This request involves dividend distribution processing for fund operations' },
          { id: 'ai-2', content: 'Key stakeholders include: Fund Company, Custody Bank, and Investors' },
          { id: 'ai-3', content: 'The process requires compliance with regulatory requirements' },
          { id: 'ai-4', content: 'Output should include distribution records and audit trails' },
        ];
      case 'ba':
        return [
          { id: 'ba-1', content: 'Business process flow: Receive request → Validate → Calculate → Distribute → Report' },
          { id: 'ba-2', content: 'Suppliers: Fund Company, Custody Bank Database, Investor Account System' },
          { id: 'ba-3', content: 'Compliance requirements: Must follow CSRC regulations for fund distribution' },
        ];
      case 'tech':
        return [
          { id: 'tech-1', content: 'Integration points: Account Management API, Transaction Processing System' },
          { id: 'tech-2', content: 'Data validation required at each step to ensure accuracy' },
          { id: 'tech-3', content: 'Audit logging must be implemented for all transactions' },
        ];
      default:
        return [];
    }
  }

  const getRoleIcon = (role: 'AI' | 'BA' | 'Tech') => {
    switch (role) {
      case 'AI': return <Bot size={20} />;
      case 'BA': return <Briefcase size={20} />;
      case 'Tech': return <Code size={20} />;
    }
  };

  const getRoleColor = (role: 'AI' | 'BA' | 'Tech') => {
    switch (role) {
      case 'AI': return '#6366f1';
      case 'BA': return '#10b981';
      case 'Tech': return '#f59e0b';
    }
  };

  const getAgentName = (agentId: string) => {
    switch (agentId) {
      case 'ai': return 'Claude AI';
      case 'ba': return 'BA Agent';
      case 'tech': return 'Tech Agent';
      default: return agentId;
    }
  };

  const getAgentRole = (agentId: string): 'AI' | 'BA' | 'Tech' => {
    switch (agentId) {
      case 'ai': return 'AI';
      case 'ba': return 'BA';
      case 'tech': return 'Tech';
      default: return 'AI';
    }
  };

  // Handle clicking on a thinking point to edit
  const handlePointClick = (agentId: string, pointId: string) => {
    setAgentThinkings(prev => prev.map(at => {
      if (at.agentId !== agentId) return at;
      return {
        ...at,
        thinkingPoints: at.thinkingPoints.map(tp =>
          tp.id === pointId
            ? { ...tp, isEditing: true, editedContent: tp.content }
            : tp
        ),
      };
    }));
    // Focus the input after state update
    setTimeout(() => {
      inputRefs.current[pointId]?.focus();
    }, 50);
  };

  // Handle saving edited content
  const handleSaveEdit = (agentId: string, pointId: string) => {
    setAgentThinkings(prev => prev.map(at => {
      if (at.agentId !== agentId) return at;
      return {
        ...at,
        thinkingPoints: at.thinkingPoints.map(tp =>
          tp.id === pointId
            ? { ...tp, content: tp.editedContent || tp.content, isEditing: false, editedContent: undefined }
            : tp
        ),
      };
    }));
  };

  // Handle input change
  const handleInputChange = (agentId: string, pointId: string, value: string) => {
    setAgentThinkings(prev => prev.map(at => {
      if (at.agentId !== agentId) return at;
      return {
        ...at,
        thinkingPoints: at.thinkingPoints.map(tp =>
          tp.id === pointId
            ? { ...tp, editedContent: value }
            : tp
        ),
      };
    }));
  };

  // Handle key press (Enter to save)
  const handleKeyPress = (e: React.KeyboardEvent, agentId: string, pointId: string) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveEdit(agentId, pointId);
    }
  };

  // Handle Go On button - move to next agent
  const handleGoOn = () => {
    console.log('[DEBUG CollaborationPanel] handleGoOn called, currentAgentIndex:', currentAgentIndex);
    // Mark current agent as complete
    setAgentThinkings(prev => prev.map((at, idx) =>
      idx === currentAgentIndex ? { ...at, isComplete: true } : at
    ));

    // Move to next agent or complete collaboration
    if (currentAgentIndex < 2) {
      setCurrentAgentIndex(prev => prev + 1);
      console.log('[DEBUG CollaborationPanel] Moving to next agent');
    } else {
      console.log('[DEBUG CollaborationPanel] All agents complete, calling onCollaborationComplete');
      setIsCollaborationComplete(true);
      // Notify parent that collaboration is complete with the SIPOC data
      onCollaborationComplete?.(generatedSipoc);
    }
  };

  const currentAgent = agentThinkings[currentAgentIndex];
  const currentAgentId = currentAgent?.agentId;
  const currentRole = getAgentRole(currentAgentId);

  return (
    <div className="collaboration-panel">
      <div className="collaboration-header">
        <Users size={18} />
        <span>Multi-Role Collaboration</span>
      </div>

      <div className="collaboration-intro">
        <p>
          <strong>Generating SIPOC requires specialized domain knowledge.</strong>
          We've invited BA Agent and Tech Agent to collaborate
          with Claude AI to ensure the SIPOC document accurately captures business processes
          and technical requirements.
        </p>
      </div>

      {/* Role cards */}
      <div className="collaboration-roles">
        {['ai', 'ba', 'tech'].map((agentId) => {
          const role = getAgentRole(agentId);
          const isActive = currentAgentId === agentId && !isCollaborationComplete;
          const isCompleted = agentThinkings.find(at => at.agentId === agentId)?.isComplete;
          return (
            <div
              key={agentId}
              className={`role-card ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
              style={{ borderLeftColor: getRoleColor(role) }}
            >
              <div className="role-avatar" style={{ backgroundColor: getRoleColor(role) }}>
                {isCompleted ? <CheckCircle size={20} /> : getRoleIcon(role)}
              </div>
              <div className="role-info">
                <div className="role-name">{getAgentName(agentId)}</div>
                <div className="role-title">
                  {agentId === 'ai' ? 'AI Assistant' : agentId === 'ba' ? 'Business Analyst' : 'Technical Expert'}
                </div>
                {isActive && <div className="role-status active">Currently Thinking...</div>}
                {isCompleted && <div className="role-status completed">Completed</div>}
              </div>
            </div>
          );
        })}
      </div>

      {/* Interactive thinking process */}
      {!isCollaborationComplete && currentAgent && (
        <div className="collaboration-thinking">
          <div className="thinking-header" style={{ borderLeftColor: getRoleColor(currentRole) }}>
            <span className="thinking-agent-badge" style={{ backgroundColor: getRoleColor(currentRole) }}>
              {getRoleIcon(currentRole)}
              {getAgentName(currentAgentId)}
            </span>
            <span className="thinking-label">is analyzing...</span>
          </div>

          <div className="thinking-points-list">
            <p className="thinking-instruction">
              Review the points below. Click on any point to edit it:
            </p>
            {currentAgent.thinkingPoints.map((point) => (
              <div key={point.id} className="thinking-point-item">
                {point.isEditing ? (
                  <div className="thinking-point-edit">
                    <input
                      ref={el => inputRefs.current[point.id] = el}
                      type="text"
                      className="thinking-point-input"
                      value={point.editedContent || ''}
                      onChange={(e) => handleInputChange(currentAgentId, point.id, e.target.value)}
                      onKeyPress={(e) => handleKeyPress(e, currentAgentId, point.id)}
                    />
                    <button
                      className="thinking-point-save-btn"
                      onClick={() => handleSaveEdit(currentAgentId, point.id)}
                    >
                      <Check size={16} />
                    </button>
                  </div>
                ) : (
                  <div
                    className="thinking-point-content"
                    onClick={() => handlePointClick(currentAgentId, point.id)}
                  >
                    <span className="thinking-point-text">{point.content}</span>
                    <Edit2 size={14} className="thinking-point-edit-icon" />
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="thinking-actions">
            <button className="btn btn-go-on" onClick={handleGoOn}>
              Go On
            </button>
          </div>
        </div>
      )}

      {/* Show collaboration complete - button will be shown below via onCollaborationComplete */}
      {isCollaborationComplete && (
        <div className="collaboration-complete">
          <CheckCircle size={16} style={{ color: '#22c55e', marginRight: '8px' }} />
          <span>Multi-role collaboration completed. SIPOC document ready for review.</span>
        </div>
      )}
    </div>
  );
}

// Helper function to get icon for detail type
function getDetailIcon(type: StepDetail['type']) {
  switch (type) {
    case 'module': return <FileCode size={12} />;
    case 'memory': return <Database size={12} />;
    case 'agent': return <Bot size={12} />;
    case 'rag': return <Search size={12} />;
    case 'service': return <Cpu size={12} />;
    case 'crew': return <Users size={12} />;
    case 'action': return <Zap size={12} />;
    case 'result': return <CheckCircle size={12} />;
    default: return <Code size={12} />;
  }
}

// Helper function to get color for detail type
function getDetailColor(type: StepDetail['type']) {
  switch (type) {
    case 'module': return '#8b5cf6';  // purple
    case 'memory': return '#06b6d4';  // cyan
    case 'agent': return '#6366f1';   // indigo
    case 'rag': return '#f59e0b';     // amber
    case 'service': return '#10b981'; // emerald
    case 'crew': return '#ec4899';    // pink
    case 'action': return '#3b82f6';  // blue
    case 'result': return '#22c55e';  // green
    default: return '#64748b';        // slate
  }
}

// Analysis Session Display Component
function AnalysisSessionDisplay({
  session,
  isCurrentlyLoading,
  onToggleCollapse,
  onGenerateSipoc,
  onSessionCollaborationComplete,
}: {
  session: AnalysisSession;
  isCurrentlyLoading: boolean;
  onToggleCollapse: () => void;
  onGenerateSipoc?: (sipoc: SIPOCDocument) => void;
  onSessionCollaborationComplete?: () => void;
}) {
  const totalSteps = session.steps.length > 0 ? Math.max(session.steps.length, session.isComplete ? session.steps.length : session.steps.length + 1) : 0;
  const currentStep = session.steps.length;

  // State to track collaboration completion and generated SIPOC
  const [collaborationComplete, setCollaborationComplete] = useState(false);
  const [completedSipoc, setCompletedSipoc] = useState<SIPOCDocument | null>(null);

  // Handle collaboration completion from CollaborationPanel
  const handleCollaborationComplete = (sipoc: SIPOCDocument) => {
    console.log('[DEBUG AnalysisSessionDisplay] handleCollaborationComplete called with sipoc');
    setCollaborationComplete(true);
    setCompletedSipoc(sipoc);
    // Notify parent that collaboration is complete for this session
    console.log('[DEBUG AnalysisSessionDisplay] calling onSessionCollaborationComplete');
    onSessionCollaborationComplete?.();
  };

  // Debug: Log steps to see collaboration data
  console.log('[DEBUG AnalysisSessionDisplay] session.steps:', session.steps);
  console.log('[DEBUG AnalysisSessionDisplay] collaborationComplete:', collaborationComplete);

  return (
    <div className={`analysis-steps-display ${session.isCollapsed ? 'collapsed' : ''}`}>
      <div className="steps-header" onClick={onToggleCollapse}>
        <div className="steps-header-left">
          <div className={`thinking-avatar ${!session.isComplete ? 'thinking' : ''}`}>
            <Brain size={20} />
          </div>
          <span className="steps-title">AI Analysis Process</span>
        </div>
        <div className="steps-header-right">
          <div className="progress-bar-mini">
            <div
              className="progress-fill"
              style={{ width: `${session.isComplete ? 100 : (currentStep / Math.max(totalSteps, 1)) * 100}%` }}
            />
          </div>
          <span className="progress-text-mini">
            {session.isComplete ? 'Complete' : `${currentStep}/${totalSteps || '?'}`}
          </span>
          <button className="collapse-btn" type="button">
            {session.isCollapsed ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            <span>{session.isCollapsed ? 'Expand' : 'Collapse'}</span>
          </button>
        </div>
      </div>
      {!session.isCollapsed && (
        <div className="steps-list">
          {session.steps.map((step, index) => {
            // Check if this is Step 4 (Preparing Review) and collaboration is complete
            const isReviewStep = step.title.toLowerCase().includes('review') || step.title.toLowerCase().includes('preparing');
            const showSipocInStep = isReviewStep && collaborationComplete && completedSipoc;

            return (
              <div
                key={step.step}
                className={`step-item ${index === session.steps.length - 1 && !session.isComplete && isCurrentlyLoading ? 'current' : 'completed'} ${step.showCollaboration ? 'has-collaboration' : ''} ${showSipocInStep ? 'has-sipoc-review' : ''}`}
              >
                <div className="step-header">
                  {index === session.steps.length - 1 && !session.isComplete && isCurrentlyLoading ? (
                    <Loader2 className="spinner-icon-small" size={16} />
                  ) : (
                    <CheckCircle className="check-icon" size={16} />
                  )}
                  <span className="step-number">Step {step.step}:</span>
                  <strong className="step-title">{step.title}</strong>
                </div>
                <div className="step-thinking">{step.thinking}</div>
                {/* Show step details if available */}
                {step.details && step.details.length > 0 && (
                  <div className="step-details">
                    {step.details.map((detail, detailIndex) => (
                      <div
                        key={detailIndex}
                        className="step-detail-item"
                        style={{ borderLeftColor: getDetailColor(detail.type) }}
                      >
                        <span className="detail-icon" style={{ color: getDetailColor(detail.type) }}>
                          {getDetailIcon(detail.type)}
                        </span>
                        <span className="detail-type">{detail.type.toUpperCase()}</span>
                        {detail.name && <span className="detail-name">{detail.name}</span>}
                        {detail.description && <span className="detail-description">{detail.description}</span>}
                      </div>
                    ))}
                  </div>
                )}
                {/* Show collaboration panel for SIPOC generation step */}
                {step.showCollaboration && step.collaboration && (
                  <CollaborationPanel
                    collaboration={step.collaboration}
                    onGenerate={onGenerateSipoc}
                    onCollaborationComplete={handleCollaborationComplete}
                  />
                )}
                {/* Show SIPOC display in Step 4 when collaboration is complete */}
                {showSipocInStep && (
                  <div className="sipoc-review-in-step">
                    <div className="sipoc-review-header">
                      <CheckCircle size={18} style={{ color: '#22c55e' }} />
                      <span>SIPOC Document Generated Successfully</span>
                    </div>
                    <div className="generated-sipoc-horizontal">
                      <div className="sipoc-column-h">
                        <div className="sipoc-column-header">
                          <span className="sipoc-letter">S</span>
                          <span>Suppliers</span>
                        </div>
                        <ul>
                          {completedSipoc.suppliers.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="sipoc-column-h">
                        <div className="sipoc-column-header">
                          <span className="sipoc-letter">I</span>
                          <span>Inputs</span>
                        </div>
                        <ul>
                          {completedSipoc.inputs.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="sipoc-column-h">
                        <div className="sipoc-column-header">
                          <span className="sipoc-letter">P</span>
                          <span>Process</span>
                        </div>
                        <ul>
                          {completedSipoc.process.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="sipoc-column-h">
                        <div className="sipoc-column-header">
                          <span className="sipoc-letter">O</span>
                          <span>Outputs</span>
                        </div>
                        <ul>
                          {completedSipoc.outputs.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="sipoc-column-h">
                        <div className="sipoc-column-header">
                          <span className="sipoc-letter">C</span>
                          <span>Customers</span>
                        </div>
                        <ul>
                          {completedSipoc.customers.map((item, i) => (
                            <li key={i}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function SIPOCDisplay({
  sipoc,
  onCorrect,
  onWrong,
}: {
  sipoc: SIPOCDocument;
  onCorrect: () => void;
  onWrong: () => void;
}) {
  return (
    <div className="sipoc-container">
      <div className="sipoc-header">SIPOC Document</div>
      <div className="sipoc-grid">
        <div className="sipoc-column">
          <h4>Suppliers</h4>
          <ul>
            {sipoc.suppliers.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="sipoc-column">
          <h4>Inputs</h4>
          <ul>
            {sipoc.inputs.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="sipoc-column">
          <h4>Process</h4>
          <ul>
            {sipoc.process.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="sipoc-column">
          <h4>Outputs</h4>
          <ul>
            {sipoc.outputs.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="sipoc-column">
          <h4>Customers</h4>
          <ul>
            {sipoc.customers.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
      <div className="sipoc-actions">
        <button className="btn btn-confirm" onClick={onCorrect}>
          Looks Good!
        </button>
        <button className="btn btn-reject" onClick={onWrong}>
          Needs Changes
        </button>
      </div>
    </div>
  );
}

// Message bubble component
function MessageBubble({
  message,
  isVerticalOptions,
  onActionClick,
  onInputSubmit,
}: {
  message: ChatMessage;
  isVerticalOptions: boolean;
  onActionClick: (actionType: string, optionValue?: string, optionLabel?: string) => void;
  onInputSubmit?: (inputValue: string, placeholder?: string) => void;
}) {
  const [inputValues, setInputValues] = useState<{ [key: string]: string }>({});
  const [showInputFor, setShowInputFor] = useState<string | null>(null);

  const handleInputChange = (actionId: string, value: string) => {
    setInputValues(prev => ({ ...prev, [actionId]: value }));
  };

  const handleInputSubmit = (action: ChatMessage['actions'][0]) => {
    const inputValue = inputValues[action.id] || '';
    if (inputValue.trim()) {
      onInputSubmit?.(inputValue.trim(), action.placeholder);
      setInputValues(prev => ({ ...prev, [action.id]: '' }));
      setShowInputFor(null);
    }
  };

  const handleInputKeyPress = (e: React.KeyboardEvent, action: ChatMessage['actions'][0]) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleInputSubmit(action);
    }
  };

  const getButtonClass = (actionType: string) => {
    switch (actionType) {
      case 'option':
      case 'reanalyze':
      case 'input':
        return 'btn-option-list';
      case 'confirm':
        return 'btn-confirm';
      case 'generate':
      case 'generateWorkflow':
        return 'btn-generate';
      default:
        return 'btn-reject';
    }
  };

  return (
    <div className={`chat-message ${message.role}`}>
      <div className="message-bubble">
        <div className="message-content">{renderMarkdown(message.content)}</div>
        {message.actions && message.actions.length > 0 && (
          <div className={`message-actions ${isVerticalOptions ? 'vertical' : ''}`}>
            {message.actions.map((action) => (
              <div key={action.id} className="action-item">
                {action.type === 'input' && showInputFor === action.id ? (
                  <div className="input-action-container">
                    <textarea
                      className="feedback-input"
                      placeholder={action.placeholder || 'Please provide details...'}
                      value={inputValues[action.id] || ''}
                      onChange={(e) => handleInputChange(action.id, e.target.value)}
                      onKeyPress={(e) => handleInputKeyPress(e, action)}
                      rows={3}
                      autoFocus
                    />
                    <div className="input-action-buttons">
                      <button
                        className="btn btn-confirm btn-sm"
                        onClick={() => handleInputSubmit(action)}
                        disabled={!inputValues[action.id]?.trim()}
                      >
                        Submit
                      </button>
                      <button
                        className="btn btn-reject btn-sm"
                        onClick={() => setShowInputFor(null)}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    className={`btn ${getButtonClass(action.type)}`}
                    onClick={() => {
                      if (action.type === 'input') {
                        setShowInputFor(action.id);
                      } else {
                        onActionClick(action.type, action.value, action.label);
                      }
                    }}
                  >
                    {action.label}
                  </button>
                )}
              </div>
            ))}
            {isVerticalOptions && !showInputFor && (
              <p className="custom-input-hint">
                Or type your own response in the input below
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function ChatWindow({
  messages,
  onSendMessage,
  onActionClick,
  onInputSubmit,
  sipocDocument,
  workflowSipoc,
  isLoading,
  analysisSessions,
  onToggleSessionCollapse,
  onGenerateSipoc,
  onCollaborationComplete,
}: ChatWindowProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // Track which sessions have collaboration completed
  const [sessionsWithCollaborationComplete, setSessionsWithCollaborationComplete] = useState<Set<string>>(new Set());

  // Callback when a session's collaboration completes
  const handleSessionCollaborationComplete = (sessionId: string) => {
    console.log('[DEBUG ChatWindow] handleSessionCollaborationComplete called for session:', sessionId);
    setSessionsWithCollaborationComplete(prev => {
      const newSet = new Set(prev).add(sessionId);
      console.log('[DEBUG ChatWindow] sessionsWithCollaborationComplete updated:', Array.from(newSet));
      return newSet;
    });
    // Notify parent to show pending steps
    onCollaborationComplete?.(sessionId);
  };

  // Debug: Log messages with actions
  useEffect(() => {
    const messagesWithActions = messages.filter(m => m.actions && m.actions.length > 0);
    console.log('[DEBUG ChatWindow] Messages with actions:', messagesWithActions);
  }, [messages]);

  useEffect(() => {
    // Add a small delay to ensure the DOM has updated before scrolling
    const timer = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    return () => clearTimeout(timer);
  }, [messages, analysisSessions, sipocDocument, workflowSipoc]);

  // Debug: Log sipocDocument changes
  useEffect(() => {
    console.log('[DEBUG ChatWindow] sipocDocument prop:', sipocDocument ? 'present' : 'null');
    if (sipocDocument) {
      console.log('[DEBUG ChatWindow] sipocDocument data:', sipocDocument);
    }
  }, [sipocDocument]);

  // Debug: Log workflowSipoc changes
  useEffect(() => {
    console.log('[DEBUG ChatWindow] workflowSipoc prop:', workflowSipoc ? 'present' : 'null');
    if (workflowSipoc) {
      console.log('[DEBUG ChatWindow] workflowSipoc data:', workflowSipoc);
    }
  }, [workflowSipoc]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Check if actions are vertical options (more than 2 items)
  const isVerticalOptions = (actions: ChatMessage['actions']) => {
    return actions && actions.length > 2;
  };

  // Get messages for a specific session (from startMessageIndex to next session's startMessageIndex)
  const getSessionMessages = (sessionIndex: number) => {
    const session = analysisSessions[sessionIndex];
    const nextSession = analysisSessions[sessionIndex + 1];
    const startIdx = session.startMessageIndex;
    const endIdx = nextSession ? nextSession.startMessageIndex : messages.length;
    return messages.slice(startIdx, endIdx);
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {/* If we have sessions, render sessions with their associated messages */}
        {analysisSessions.length > 0 ? (
          <>
            {analysisSessions.map((session, sessionIndex) => {
              const sessionMessages = getSessionMessages(sessionIndex);
              const isLastSession = sessionIndex === analysisSessions.length - 1;
              const showLoading = isLoading && isLastSession && !session.isComplete;

              // Check if this session has collaboration complete
              const isCollaborationComplete = sessionsWithCollaborationComplete.has(session.id);
              // Check if this session has collaboration (has a step with showCollaboration)
              const hasCollaboration = session.steps.some(step => step.showCollaboration);
              // Check if session is waiting for collaboration (more reliable flag from parent)
              const isWaitingForCollaboration = session.waitingForCollaboration === true;

              console.log(`[DEBUG ChatWindow render] Session ${session.id}: isCollaborationComplete=${isCollaborationComplete}, hasCollaboration=${hasCollaboration}, isWaitingForCollaboration=${isWaitingForCollaboration}, sessionMessages=${sessionMessages.length}`);

              return (
                <div key={session.id}>
                  {/* Show Analysis Progress if there are steps */}
                  {session.steps.length > 0 && (
                    <AnalysisSessionDisplay
                      session={session}
                      isCurrentlyLoading={showLoading}
                      onToggleCollapse={() => onToggleSessionCollapse(session.id)}
                      onGenerateSipoc={onGenerateSipoc}
                      onSessionCollaborationComplete={() => handleSessionCollaborationComplete(session.id)}
                    />
                  )}

                  {/* Show messages associated with this session */}
                  {/* For messages with generate action: only show after collaboration completes */}
                  {sessionMessages
                    .filter(msg => {
                      const hasGenerateAction = msg.actions?.some(a => a.type === 'generate' || a.type === 'generateWorkflow');
                      // If message has generate action and session has collaboration or is waiting, only show after collaboration completes
                      if (hasGenerateAction && (hasCollaboration || isWaitingForCollaboration)) {
                        console.log(`[DEBUG ChatWindow filter] Message ${msg.id} has generate action, hasCollaboration=${hasCollaboration}, isWaitingForCollaboration=${isWaitingForCollaboration}, isCollaborationComplete=${isCollaborationComplete}, showing=${isCollaborationComplete}`);
                        return isCollaborationComplete;
                      }
                      return true;
                    })
                    .map((msg) => (
                    <MessageBubble
                      key={msg.id}
                      message={msg}
                      isVerticalOptions={isVerticalOptions(msg.actions)}
                      onActionClick={onActionClick}
                      onInputSubmit={onInputSubmit}
                    />
                  ))}
                </div>
              );
            })}
          </>
        ) : (
          /* If no sessions, render all messages directly */
          messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isVerticalOptions={isVerticalOptions(msg.actions)}
              onActionClick={onActionClick}
              onInputSubmit={onInputSubmit}
            />
          ))
        )}

        {sipocDocument && (
          <SIPOCDisplay
            sipoc={sipocDocument}
            onCorrect={() => onActionClick('correct')}
            onWrong={() => onActionClick('wrong')}
          />
        )}

        {/* Show BPM Workflow diagram */}
        {workflowSipoc && (
          <>
            {console.log('[DEBUG ChatWindow render] Rendering BPMWorkflow with sipoc:', workflowSipoc)}
            <BPMWorkflow
              sipoc={workflowSipoc}
              title="Dividend Distribution Process - BPMN 2.0"
            />
          </>
        )}

        {/* Show loading indicator only if no sessions or if the last session has no steps yet */}
        {isLoading && (analysisSessions.length === 0 || (analysisSessions.length > 0 && analysisSessions[analysisSessions.length - 1].steps.length === 0)) && (
          <div className="chat-message assistant">
            <div className="message-bubble loading-bubble">
              <div className="loading-content">
                <Loader2 className="spinner-icon" size={20} />
                <span>Processing...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-container" onSubmit={handleSubmit}>
        <textarea
          className="chat-input"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          rows={1}
          disabled={isLoading}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={!inputValue.trim() || isLoading}
        >
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}
