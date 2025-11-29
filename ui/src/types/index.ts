// Email types
export interface Email {
  id: string;
  from: string;
  subject: string;
  summary: string;
  body?: string;  // Full email content for tooltip display
  date: string;
  hasAttachment: boolean;
  attachments: Attachment[];
  isSelected: boolean;
}

// Attachment types
export interface Attachment {
  id: string;
  name: string;
  size: string;
  type: string;
  emailId: string;
  isSelected: boolean;
}

// Folder types
export interface Folder {
  id: string;
  name: string;
  type: 'folder' | 'file';
  children?: Folder[];
  attachment?: Attachment;
  isExpanded?: boolean;
}

// Feedback types
export type FeedbackType = 'positive' | 'negative' | null;

export interface FeedbackData {
  messageId: string;
  feedbackType: FeedbackType;
  targetType: 'memory' | 'service';
  targetName: string;
  timestamp: Date;
}

// Chat message types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  actions?: ChatAction[];
  feedback?: FeedbackType; // User's feedback on this message
  canFeedback?: boolean; // Whether this message can receive feedback
}

export interface ChatAction {
  id: string;
  label: string;
  type: 'confirm' | 'reject' | 'correct' | 'wrong' | 'option' | 'generate' | 'input' | 'reanalyze' | 'generateWorkflow' | 'generateService' | 'returnData' | 'done';
  value?: string; // Used for option type to send as message
  placeholder?: string; // Used for input type to show placeholder text
}

// Workflow step execution result
export interface WorkflowStepResult {
  stepNumber: number;
  stepName: string;
  status: 'completed' | 'in_progress' | 'pending' | 'error';
  data: Record<string, unknown>;
  message: string;
  timestamp: string;
}

// Service execution result
export interface ServiceExecutionResult {
  success: boolean;
  workflowType: string;
  totalSteps: number;
  completedSteps: number;
  stepResults: WorkflowStepResult[];
  summary: Record<string, unknown>;
  executionData: Record<string, unknown>;
  timestamp: string;
}

// Collaboration role type
export interface CollaborationRole {
  id: string;
  name: string;
  role: 'AI' | 'BA' | 'Tech';
  avatar: string;
  contribution: string;
}

// Thinking point for interactive collaboration
export interface ThinkingPoint {
  id: string;
  content: string;
  isEditing?: boolean;
  editedContent?: string;
}

// Agent thinking state for interactive collaboration
export interface AgentThinking {
  agentId: string;
  thinkingPoints: ThinkingPoint[];
  isComplete: boolean;
}

// Collaboration session for multi-role SIPOC generation
export interface CollaborationSession {
  isActive: boolean;
  roles: CollaborationRole[];
  messages: CollaborationMessage[];
  generatedSipoc?: SIPOCDocument;
  // New fields for interactive collaboration
  currentAgentId?: string;  // Which agent is currently thinking
  agentThinkings?: AgentThinking[];  // Thinking state for each agent
}

export interface CollaborationMessage {
  roleId: string;
  content: string;
  timestamp?: Date;
}

// Detail item for processing step
export interface StepDetail {
  type: 'module' | 'memory' | 'agent' | 'rag' | 'service' | 'crew' | 'action' | 'result';
  name?: string;
  path?: string;
  description?: string;
}

// Processing step type
export interface ProcessingStep {
  step: number;
  title: string;
  thinking: string;
  details?: StepDetail[];  // Detailed information about what modules/agents are used
  showCollaboration?: boolean;  // Flag to show collaboration panel
  collaboration?: CollaborationSession;  // Collaboration data for this step
}

// Analysis session for tracking multiple analysis progress sections
export interface AnalysisSession {
  id: string;
  steps: ProcessingStep[];
  isCollapsed: boolean;
  isComplete: boolean;
  startMessageIndex: number; // Index of first message after this session starts
  pendingSteps?: ProcessingStep[]; // Steps to show after collaboration completes
  waitingForCollaboration?: boolean; // Flag indicating collaboration is in progress
  pendingMessage?: ChatMessage; // Message to show after collaboration completes
  pendingSipoc?: SIPOCDocument; // SIPOC document to use for workflow generation
}

// Analysis result types
export interface AnalysisResult {
  emailSubject: string;
  summary: string;
  attachments: string[];
  userIntent: string;
  suggestedAction: string;
  processingSteps?: ProcessingStep[];
  matchedService?: string | null;
}

// SIPOC document types
export interface SIPOCDocument {
  suppliers: string[];
  inputs: string[];
  process: string[];
  outputs: string[];
  customers: string[];
}

// Selection state
export interface SelectionState {
  selectedEmails: string[];
  selectedAttachments: string[];
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
