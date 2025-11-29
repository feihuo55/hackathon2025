import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar/Sidebar';
import { EmailList } from './components/EmailList/EmailList';
import { EmailFolder } from './components/EmailFolder/EmailFolder';
import { AnalysisPanel } from './components/AnalysisPanel/AnalysisPanel';
import { AuthModal } from './components/AuthModal/AuthModal';
import { PermissionModal } from './components/PermissionModal/PermissionModal';

// Types for permission modal
interface ServicePermission {
  id: string;
  name: string;
  description: string;
}

interface SharedFolder {
  id: string;
  name: string;
  emailCount: number;
}
import {
  fetchEmails,
  analyzeEmails,
  sendChatMessage,
  executeService,
} from './services/api';
import type {
  Email,
  SelectionState,
  ChatMessage,
  AnalysisResult,
  SIPOCDocument,
  AnalysisSession,
  ProcessingStep,
  ServiceExecutionResult,
} from './types';
import './styles/main.css';

// Simple folder type
interface FolderItem {
  id: string;
  name: string;
  icon: 'inbox' | 'sent' | 'archive' | 'trash' | 'starred' | 'important' | 'folder';
  count: number;
}

// Mock services based on department permissions
const MOCK_SERVICES: ServicePermission[] = [
  { id: 'dividend-service', name: 'Dividend Processing Service', description: 'Process fund dividend distributions' },
  { id: 'nav-service', name: 'NAV Calculation Service', description: 'Calculate net asset values' },
];

function App() {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(true);
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [userDepartment, setUserDepartment] = useState<string | null>(null);
  const [userServices, setUserServices] = useState<ServicePermission[]>([]);
  const [sharedFolders, setSharedFolders] = useState<SharedFolder[]>([]);

  // Tab state - now includes folder view
  const [activeTab, setActiveTab] = useState<'email' | null>(null);
  const [emailSubTab, setEmailSubTab] = useState<'folders' | 'emails'>('folders');

  // Folder state - dynamically set based on shared folders
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);

  // Data state
  const [emails, setEmails] = useState<Email[]>([]);
  const [allEmails, setAllEmails] = useState<Email[]>([]); // Store all emails from API

  // Selection state
  const [selection, setSelection] = useState<SelectionState>({
    selectedEmails: [],
    selectedAttachments: [],
  });

  // Analysis state
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [sipocDocument, setSipocDocument] = useState<SIPOCDocument | null>(null);
  const [pendingSipoc, setPendingSipoc] = useState<SIPOCDocument | null>(null); // For Generate Workflow button
  const [workflowSipoc, setWorkflowSipoc] = useState<SIPOCDocument | null>(null); // For displaying BPM workflow
  const [serviceExecutionResult, setServiceExecutionResult] = useState<ServiceExecutionResult | null>(null); // For displaying service execution results
  const [pendingWorkflowResult, setPendingWorkflowResult] = useState<ServiceExecutionResult | null>(null); // Stored result waiting for user confirmation
  const [isLoading, setIsLoading] = useState(false);

  // Multiple analysis sessions - each request gets its own section
  const [analysisSessions, setAnalysisSessions] = useState<AnalysisSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // Load initial data after authentication
  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  // Debug: Track sipocDocument state changes
  useEffect(() => {
    console.log('[DEBUG] sipocDocument state changed:', sipocDocument);
  }, [sipocDocument]);

  async function loadData() {
    const emailData = await fetchEmails();
    setAllEmails(emailData);
    // Set emails initially to all fetched emails
    setEmails(emailData);
  }

  // Handle login - returns department for popup, but doesn't set isAuthenticated yet
  // AuthModal will call onClose after user acknowledges department, then we set isAuthenticated
  async function handleLogin(username: string, password: string): Promise<{ success: boolean; department?: string; error?: string }> {
    // Simulate authentication - in production this would call a real API
    await new Promise(resolve => setTimeout(resolve, 1000));

    if (username === 'demo' && password === 'demo123') {
      const department = 'Business01';
      setUserDepartment(department);
      // Don't set isAuthenticated here - wait for department popup acknowledgment
      return { success: true, department };
    }

    return { success: false, error: 'Invalid username or password' };
  }

  // Called when user acknowledges department popup - now shows permission modal
  function handleAuthComplete() {
    setShowAuthModal(false);
    // Load permissions and show permission modal
    loadPermissions();
    setShowPermissionModal(true);
  }

  // Load permissions based on department
  async function loadPermissions() {
    // In production, this would fetch from API based on department
    // For now, mock the data
    setUserServices(MOCK_SERVICES);

    // Fetch emails to get the correct count
    const emailData = await fetchEmails();
    setAllEmails(emailData);
    setEmails(emailData);

    // Create shared folders with correct email counts
    const mockSharedFolders: SharedFolder[] = [
      { id: 'monitor', name: 'Monitor Folder', emailCount: emailData.length },
      { id: 'dividend-requests', name: 'Dividend Requests', emailCount: 2 },
    ];
    setSharedFolders(mockSharedFolders);

    // Update folder list with correct counts
    const folderItems: FolderItem[] = mockSharedFolders.map(folder => ({
      id: folder.id,
      name: folder.name,
      icon: folder.id === 'monitor' ? 'inbox' as const : 'folder' as const,
      count: folder.emailCount,
    }));
    setFolders(folderItems);
  }

  // Called when user clicks continue on permission modal
  function handlePermissionComplete() {
    setShowPermissionModal(false);
    setIsAuthenticated(true);
    setActiveTab('email'); // Automatically switch to email tab
  }

  // Handle folder selection
  function handleFolderSelect(folderId: string) {
    setSelectedFolderId(folderId);
    // For simplicity, all folders show the same emails (from API)
    setEmails(allEmails);
    // Clear previous selection
    setSelection({ selectedEmails: [], selectedAttachments: [] });
    // Switch to emails view
    setEmailSubTab('emails');
  }

  // Handle back to folders
  function handleBackToFolders() {
    setEmailSubTab('folders');
    setSelectedFolderId(null);
  }

  // Handle email selection
  function handleEmailSelection(emailId: string, selected: boolean) {
    const email = emails.find((e) => e.id === emailId);
    if (!email) return;

    setSelection((prev) => {
      const newSelectedEmails = selected
        ? [...prev.selectedEmails, emailId]
        : prev.selectedEmails.filter((id) => id !== emailId);

      const newSelectedAttachments = selected
        ? [...prev.selectedAttachments, ...email.attachments.map((a) => a.id)]
        : prev.selectedAttachments.filter(
            (id) => !email.attachments.some((a) => a.id === id)
          );

      return {
        selectedEmails: newSelectedEmails,
        selectedAttachments: newSelectedAttachments,
      };
    });
  }

  // Handle email click
  function handleEmailClick(email: Email) {
    console.log('Email clicked:', email);
  }

  // Create a new analysis session and collapse previous ones
  function createNewSession(messageCount: number): string {
    const sessionId = `session_${Date.now()}`;

    // Collapse all previous sessions
    setAnalysisSessions(prev => [
      ...prev.map(s => ({ ...s, isCollapsed: true })),
      {
        id: sessionId,
        steps: [],
        isCollapsed: false,
        isComplete: false,
        startMessageIndex: messageCount,
      }
    ]);

    setCurrentSessionId(sessionId);
    return sessionId;
  }

  // Update session steps progressively
  async function showSessionProgress(sessionId: string, steps: ProcessingStep[]) {
    // Find if there's a collaboration step
    const collaborationStepIndex = steps.findIndex(step => step.showCollaboration);

    // Determine where to stop (include collaboration step, but stop before remaining steps)
    const stopIndex = collaborationStepIndex >= 0 ? collaborationStepIndex + 1 : steps.length;
    const stepsToShow = steps.slice(0, stopIndex);
    const pendingSteps = collaborationStepIndex >= 0 ? steps.slice(stopIndex) : [];

    // Show steps up to (and including) the collaboration step
    for (let i = 0; i < stepsToShow.length; i++) {
      setAnalysisSessions(prev => prev.map(s =>
        s.id === sessionId
          ? { ...s, steps: stepsToShow.slice(0, i + 1) }
          : s
      ));
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    // If there's a collaboration step, store pending steps and wait
    if (collaborationStepIndex >= 0) {
      setAnalysisSessions(prev => prev.map(s =>
        s.id === sessionId
          ? { ...s, pendingSteps, waitingForCollaboration: true }
          : s
      ));
      // Don't mark as complete yet - wait for collaboration to finish
    } else {
      // No collaboration step, mark session as complete
      setAnalysisSessions(prev => prev.map(s =>
        s.id === sessionId
          ? { ...s, isComplete: true }
          : s
      ));
    }
  }

  // Show remaining steps after collaboration completes
  async function showPendingSteps(sessionId: string) {
    console.log('[DEBUG showPendingSteps] Called for sessionId:', sessionId);

    // Use a ref-like pattern to get the latest session data
    // We need to read from the current state at call time
    let currentSession: AnalysisSession | undefined;
    setAnalysisSessions(prev => {
      currentSession = prev.find(s => s.id === sessionId);
      console.log('[DEBUG showPendingSteps] Current session:', currentSession?.id, 'pendingMessage:', currentSession?.pendingMessage ? 'exists' : 'none', 'pendingSteps:', currentSession?.pendingSteps?.length || 0);
      return prev; // Don't modify, just read
    });

    // Small delay to ensure state is read
    await new Promise(resolve => setTimeout(resolve, 50));

    // Show pending steps if any - use functional update to get latest state
    setAnalysisSessions(prev => {
      const session = prev.find(s => s.id === sessionId);
      if (session?.pendingSteps && session.pendingSteps.length > 0) {
        console.log('[DEBUG showPendingSteps] Will show', session.pendingSteps.length, 'pending steps');
      }
      return prev;
    });

    // Get pending steps and show them one by one
    let pendingStepsToShow: ProcessingStep[] = [];
    setAnalysisSessions(prev => {
      const session = prev.find(s => s.id === sessionId);
      pendingStepsToShow = session?.pendingSteps || [];
      return prev;
    });

    for (let i = 0; i < pendingStepsToShow.length; i++) {
      setAnalysisSessions(prev => prev.map(s => {
        if (s.id !== sessionId) return s;
        return {
          ...s,
          steps: [...s.steps, pendingStepsToShow[i]],
        };
      }));
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    // Add pending message to chat if exists - use functional update
    setAnalysisSessions(prev => {
      const session = prev.find(s => s.id === sessionId);
      if (session?.pendingMessage) {
        console.log('[DEBUG showPendingSteps] Adding pending message to chat:', session.pendingMessage);
        // Use setTimeout to ensure this runs after current update
        setTimeout(() => {
          setChatMessages(chatPrev => [...chatPrev, session.pendingMessage!]);
        }, 0);
      } else {
        console.log('[DEBUG showPendingSteps] No pending message found for session:', sessionId);
      }
      return prev;
    });

    // Mark session as complete and clear pending data
    await new Promise(resolve => setTimeout(resolve, 100));
    setAnalysisSessions(prev => prev.map(s =>
      s.id === sessionId
        ? { ...s, isComplete: true, pendingSteps: [], pendingMessage: undefined, waitingForCollaboration: false }
        : s
    ));
  }

  // Toggle session collapse state
  function toggleSessionCollapse(sessionId: string) {
    setAnalysisSessions(prev => prev.map(s =>
      s.id === sessionId
        ? { ...s, isCollapsed: !s.isCollapsed }
        : s
    ));
  }

  // Handle analyze
  async function handleAnalyze() {
    if (selection.selectedEmails.length === 0) return;

    setIsLoading(true);
    setChatMessages([]);
    setAnalysisResult(null);
    setSipocDocument(null);
    setPendingSipoc(null);
    setWorkflowSipoc(null);
    setServiceExecutionResult(null);
    setPendingWorkflowResult(null);
    setAnalysisSessions([]); // Clear all sessions for new analysis

    // Create new session - pass 0 since we just cleared all messages
    const sessionId = createNewSession(0);

    try {
      const result = await analyzeEmails(selection.selectedEmails);

      if (result.success && result.data) {
        // Show progress with steps from backend
        if (result.data.processingSteps && result.data.processingSteps.length > 0) {
          await showSessionProgress(sessionId, result.data.processingSteps);
        }

        setAnalysisResult(result.data);

        // Build message content based on whether a service was found
        let messageContent = `I've analyzed the selected email(s).\n\n**Based on the content:** ${result.data.userIntent}\n\n`;

        if (result.data.matchedService) {
          messageContent += `**✓ Found Matching Service:** \`${result.data.matchedService}\`\n\n`;
          messageContent += `**Suggested Action:** ${result.data.suggestedAction}\n\n`;
          messageContent += `Would you like me to proceed with this action?`;
        } else {
          messageContent += `**✗ No Matching Service Found**\n\n`;
          messageContent += `**Suggested Action:** ${result.data.suggestedAction}\n\n`;
          messageContent += `I will need to create a new workflow using SIPOC. Would you like me to proceed?`;
        }

        // Add initial AI message with better formatting
        const initialMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: messageContent,
          timestamp: new Date(),
          actions: [
            { id: 'yes', label: 'Yes, proceed', type: 'confirm' },
            { id: 'no', label: 'No, that\'s not right', type: 'reject' },
          ],
        };
        setChatMessages([initialMessage]);
      }
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsLoading(false);
    }
  }

  // Handle send message
  async function handleSendMessage(message: string) {
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    };
    setChatMessages((prev) => [...prev, userMessage]);

    setIsLoading(true);
    try {
      const result = await sendChatMessage(message, {
        emailIds: selection.selectedEmails,
        analysisResult: analysisResult || undefined,
      });

      if (result.success && result.data) {
        // Determine actions based on response
        let actions: ChatMessage['actions'] = undefined;

        if (result.data.actions && result.data.actions.length > 0) {
          // Use actions from backend response
          actions = result.data.actions.map((act: { id: string; label: string; type: string }) => ({
            id: act.id,
            label: act.label,
            type: act.type as 'confirm' | 'reject' | 'option' | 'generate',
          }));
        } else if (result.data.options && result.data.options.length > 0) {
          // Convert options to action buttons
          actions = result.data.options.map(opt => ({
            id: opt.id,
            label: opt.label,
            type: 'option' as const,
            value: opt.value,
          }));
        } else if (!result.data.hasServiceMatch && !result.data.sipoc) {
          // Default Yes/No for confirmation
          actions = [
            { id: 'yes', label: 'Yes, proceed', type: 'confirm' },
            { id: 'no', label: 'No, that\'s not right', type: 'reject' },
          ];
        }

        // Only add chat message if response is not empty
        if (result.data.response && result.data.response.trim()) {
          const aiMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: result.data.response,
            timestamp: new Date(),
            actions,
          };
          setChatMessages((prev) => [...prev, aiMessage]);
        }

        // Store SIPOC for later use
        if (result.data.sipoc) {
          if (result.data.actions?.some((a: { type: string }) => a.type === 'generate')) {
            // Store in pendingSipoc for Generate Workflow button
            setPendingSipoc(result.data.sipoc);
          } else {
            // Show SIPOCDisplay component
            setSipocDocument(result.data.sipoc);
          }
        }
      }
    } catch (error) {
      console.error('Chat failed:', error);
    } finally {
      setIsLoading(false);
    }
  }

  // Rejection options when user clicks No
  // - 'reanalyze' type: AI will automatically re-analyze
  // - 'input' type: Shows an input box for user to provide details
  const rejectionOptions = [
    { id: 'wrong-intent', label: 'The detected intent is incorrect', type: 'reanalyze' as const, value: 'wrong-intent' },
    { id: 'wrong-action', label: 'The suggested action is not what I need', type: 'reanalyze' as const, value: 'wrong-action' },
    { id: 'missing-info', label: 'Some information is missing or wrong', type: 'input' as const, value: '', placeholder: 'Please describe what information is missing or incorrect...' },
    { id: 'other', label: 'Something else (I will explain)', type: 'input' as const, value: '', placeholder: 'Please explain what needs to be corrected...' },
  ];

  // Handle Generate SIPOC from collaboration panel
  async function handleGenerateSipoc(sipoc: SIPOCDocument) {
    console.log('[DEBUG] handleGenerateSipoc called with:', sipoc);
    setSipocDocument(sipoc);

    // Execute the service with the generated SIPOC
    setIsLoading(true);
    const sessionId = createNewSession(chatMessages.length);

    try {
      const result = await executeService(sipoc);

      if (result.success && result.data) {
        // Show progress with steps from backend
        if (result.data.processingSteps && result.data.processingSteps.length > 0) {
          await showSessionProgress(sessionId, result.data.processingSteps);
        }

        const successMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: result.data.message,
          timestamp: new Date(),
        };
        setChatMessages((prev) => [...prev, successMessage]);
        setSipocDocument(null);
      }
    } finally {
      setIsLoading(false);
    }
  }

  // Handle action click (Yes/No, Correct/Wrong, or Option selection)
  async function handleActionClick(actionType: string, optionValue?: string, optionLabel?: string) {
    if (actionType === 'option' && optionValue) {
      // User selected an option - show label as user message, send value to backend
      // First add user message with the friendly label
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: optionLabel || optionValue,
        timestamp: new Date(),
      };
      setChatMessages((prev) => [...prev, userMessage]);

      // Then send the value to backend
      setIsLoading(true);
      try {
        const result = await sendChatMessage(optionValue, {
          emailIds: selection.selectedEmails,
          analysisResult: analysisResult || undefined,
        });

        if (result.success && result.data) {
          let actions: ChatMessage['actions'] = undefined;

          if (result.data.actions && result.data.actions.length > 0) {
            actions = result.data.actions.map((act: { id: string; label: string; type: string; value?: string }) => ({
              id: act.id,
              label: act.label,
              type: act.type as 'confirm' | 'reject' | 'option' | 'generate',
              value: act.value,
            }));
          }

          if (result.data.response && result.data.response.trim()) {
            const aiMessage: ChatMessage = {
              id: (Date.now() + 1).toString(),
              role: 'assistant',
              content: result.data.response,
              timestamp: new Date(),
              actions,
            };
            setChatMessages((prev) => [...prev, aiMessage]);
          }
        }
      } catch (error) {
        console.error('Option selection failed:', error);
      } finally {
        setIsLoading(false);
      }
      return;
    } else if (actionType === 'confirm') {
      // User confirmed - check if we already have a matched service
      const hasMatchedService = analysisResult?.matchedService;

      setIsLoading(true);

      // Only create a new session if we need to show Analysis Process (i.e., no matched service)
      let sessionId: string | null = null;
      if (!hasMatchedService) {
        sessionId = createNewSession(chatMessages.length);
      }

      try {
        const result = await sendChatMessage('Yes, please proceed with the suggested action', {
          emailIds: selection.selectedEmails,
          analysisResult: analysisResult || undefined,
        });

        if (result.success && result.data) {
          // Check if there's a collaboration step
          const hasCollaborationStep = result.data.processingSteps?.some(
            (step: ProcessingStep) => step.showCollaboration
          );
          const hasGenerateAction = result.data.actions?.some(
            (a: { type: string }) => a.type === 'generate' || a.type === 'generateWorkflow'
          );

          // Only show progress if we need Analysis Process (creation flow, not query flow)
          // If we already found a service, skip the Analysis Process and just show results
          if (!hasMatchedService && sessionId && result.data.processingSteps && result.data.processingSteps.length > 0) {
            await showSessionProgress(sessionId, result.data.processingSteps);
          }

          // Determine actions from backend response
          let actions: ChatMessage['actions'] = undefined;
          console.log('[DEBUG handleActionClick confirm] result.data.actions:', result.data.actions);
          if (result.data.actions && result.data.actions.length > 0) {
            actions = result.data.actions.map((act: { id: string; label: string; type: string }) => ({
              id: act.id,
              label: act.label,
              type: act.type as 'confirm' | 'reject' | 'option' | 'generate',
            }));
            console.log('[DEBUG handleActionClick confirm] mapped actions:', actions);
          }

          // Only add chat message if response is not empty
          console.log('[DEBUG handleActionClick confirm] result.data.response:', result.data.response);
          console.log('[DEBUG handleActionClick confirm] hasMatchedService:', hasMatchedService, 'hasCollaborationStep:', hasCollaborationStep, 'hasGenerateAction:', hasGenerateAction, 'sessionId:', sessionId);

          if (result.data.response && result.data.response.trim()) {
            // If collaboration is involved, ALWAYS store the message for later (regardless of action type)
            // This ensures the message only shows after collaboration completes
            if (hasCollaborationStep && sessionId) {
              console.log('[DEBUG handleActionClick confirm] Storing message for after collaboration (hasCollaborationStep=true)');
              // Store the pending message in the session for later display
              setAnalysisSessions(prev => prev.map(s =>
                s.id === sessionId
                  ? {
                      ...s,
                      pendingMessage: {
                        id: (Date.now() + 1).toString(),
                        role: 'assistant' as const,
                        content: result.data.response,
                        timestamp: new Date(),
                        actions,
                      }
                    }
                  : s
              ));
            } else {
              // Directly show the result message (for query flow or non-collaboration flow)
              const aiMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: result.data.response,
                timestamp: new Date(),
                actions,
              };
              console.log('[DEBUG handleActionClick confirm] Creating aiMessage with actions (no collaboration):', aiMessage);
              setChatMessages((prev) => [...prev, aiMessage]);
            }
          } else {
            console.log('[DEBUG handleActionClick confirm] Response is empty, not adding message');
          }

          // Store SIPOC for later use (for generateWorkflow action)
          if (result.data.sipoc) {
            // Store in pendingSipoc for Generate Workflow button (both 'generate' and 'generateWorkflow' types)
            console.log('[DEBUG] Storing SIPOC in pendingSipoc for Generate Workflow');
            setPendingSipoc(result.data.sipoc);

            // Also store SIPOC in the session for fallback retrieval
            if (hasCollaborationStep && sessionId) {
              setAnalysisSessions(prev => prev.map(s =>
                s.id === sessionId
                  ? { ...s, pendingSipoc: result.data.sipoc }
                  : s
              ));
            }

            if (!hasGenerateAction) {
              // Show SIPOCDisplay component
              console.log('[DEBUG] Setting sipocDocument from confirm:', result.data.sipoc);
              setSipocDocument(result.data.sipoc);
            }
          }
        }
      } finally {
        setIsLoading(false);
      }
    } else if (actionType === 'reject') {
      // User rejected - show clickable options for what's wrong
      const aiMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'I understand. Please let me know what needs to be corrected:',
        timestamp: new Date(),
        actions: rejectionOptions.map(opt => ({
          id: opt.id,
          label: opt.label,
          type: opt.type,
          value: opt.value,
          placeholder: opt.placeholder,
        })),
      };
      setChatMessages((prev) => [...prev, aiMessage]);
    } else if (actionType === 'reanalyze') {
      // User selected a clear option - AI needs to deeply re-think and re-analyze
      setIsLoading(true);

      // Add user's selection as a message for context
      const userFeedbackMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: optionValue === 'wrong-intent'
          ? 'The detected intent is incorrect.'
          : 'The suggested action is not what I need.',
        timestamp: new Date(),
      };
      setChatMessages((prev) => [...prev, userFeedbackMessage]);

      try {
        // Send detailed re-analysis request to backend
        const reanalyzeMessage = optionValue === 'wrong-intent'
          ? '[REANALYZE_INTENT] The user indicates the detected intent is incorrect. Please deeply re-analyze the email content, consider alternative interpretations, and provide a completely different understanding of what the user actually needs. Do not repeat the previous intent.'
          : '[REANALYZE_ACTION] The user indicates the suggested action is not what they need. Please deeply re-analyze and suggest a completely different action that might better match the user\'s actual requirements.';

        const result = await sendChatMessage(reanalyzeMessage, {
          emailIds: selection.selectedEmails,
          analysisResult: analysisResult || undefined,
        });

        if (result.success && result.data) {
          // Determine actions - use backend actions if available, otherwise default to Yes/No
          let actions: ChatMessage['actions'] = [
            { id: 'yes', label: 'Yes, proceed', type: 'confirm' },
            { id: 'no', label: 'No, that\'s not right', type: 'reject' },
          ];

          if (result.data.actions && result.data.actions.length > 0) {
            actions = result.data.actions.map((act: { id: string; label: string; type: string }) => ({
              id: act.id,
              label: act.label,
              type: act.type as 'confirm' | 'reject' | 'option' | 'generate',
            }));
          }

          const aiMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: result.data.response,
            timestamp: new Date(),
            actions,
          };
          setChatMessages((prev) => [...prev, aiMessage]);
        }
      } finally {
        setIsLoading(false);
      }
    } else if (actionType === 'input') {
      // User needs to provide more details - show input prompt message
      const promptMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: optionValue || 'Please provide more details:',
        timestamp: new Date(),
      };
      setChatMessages((prev) => [...prev, promptMessage]);
      // The user will type their response in the chat input
    } else if (actionType === 'correct') {
      // SIPOC is correct - create new session and execute service
      setIsLoading(true);
      const sessionId = createNewSession(chatMessages.length);

      try {
        if (sipocDocument) {
          const result = await executeService(sipocDocument);

          if (result.success && result.data) {
            // Show progress with steps from backend
            if (result.data.processingSteps && result.data.processingSteps.length > 0) {
              await showSessionProgress(sessionId, result.data.processingSteps);
            }

            const successMessage: ChatMessage = {
              id: Date.now().toString(),
              role: 'assistant',
              content: result.data.message,
              timestamp: new Date(),
            };
            setChatMessages((prev) => [...prev, successMessage]);
            setSipocDocument(null);
          }
        }
      } finally {
        setIsLoading(false);
      }
    } else if (actionType === 'generate') {
      // Generate workflow from pendingSipoc
      if (pendingSipoc) {
        setIsLoading(true);
        const sessionId = createNewSession(chatMessages.length);

        try {
          const result = await executeService(pendingSipoc);

          if (result.success && result.data) {
            // Show progress with steps from backend
            if (result.data.processingSteps && result.data.processingSteps.length > 0) {
              await showSessionProgress(sessionId, result.data.processingSteps);
            }

            const successMessage: ChatMessage = {
              id: Date.now().toString(),
              role: 'assistant',
              content: result.data.message,
              timestamp: new Date(),
            };
            setChatMessages((prev) => [...prev, successMessage]);
            setPendingSipoc(null);
          }
        } finally {
          setIsLoading(false);
        }
      } else {
        console.error('[ERROR] No pendingSipoc available for generate action');
      }
    } else if (actionType === 'generateWorkflow') {
      // Generate BPM workflow from pendingSipoc or session fallback
      console.log('[DEBUG handleActionClick generateWorkflow] pendingSipoc:', pendingSipoc);

      // Try multiple sources for SIPOC data
      let sipocToUse: SIPOCDocument | null = pendingSipoc;

      // Fallback 1: Check session's pendingSipoc
      if (!sipocToUse) {
        console.log('[DEBUG handleActionClick generateWorkflow] pendingSipoc is null, checking sessions...');
        const sessionWithSipoc = analysisSessions.find(s => s.pendingSipoc);
        if (sessionWithSipoc?.pendingSipoc) {
          sipocToUse = sessionWithSipoc.pendingSipoc;
          console.log('[DEBUG handleActionClick generateWorkflow] Found SIPOC from session.pendingSipoc:', sipocToUse);
        }
      }

      // Fallback 2: Check collaboration's generatedSipoc
      if (!sipocToUse) {
        const latestSessionWithCollab = analysisSessions.find(s => s.steps.some(step => step.collaboration?.generatedSipoc));
        if (latestSessionWithCollab) {
          const collabStep = latestSessionWithCollab.steps.find(step => step.collaboration?.generatedSipoc);
          if (collabStep?.collaboration?.generatedSipoc) {
            sipocToUse = collabStep.collaboration.generatedSipoc;
            console.log('[DEBUG handleActionClick generateWorkflow] Found SIPOC from collaboration.generatedSipoc:', sipocToUse);
          }
        }
      }

      if (sipocToUse) {
        console.log('[DEBUG handleActionClick generateWorkflow] Setting workflowSipoc with:', sipocToUse);
        // Set the workflow SIPOC to display the BPM workflow diagram
        setWorkflowSipoc(sipocToUse);
        setPendingSipoc(null);

        // Add success message
        const successMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: '**BPMN 2.0 Workflow Generated Successfully!**\n\nThe workflow diagram above shows the complete process flow based on your SIPOC document. Each lane represents a different phase of the process, with tasks, gateways, and events following BPMN 2.0 standards.\n\nYou can use this workflow to:\n- Visualize the end-to-end process\n- Identify automation opportunities\n- Document the business process for stakeholders',
          timestamp: new Date(),
        };
        setChatMessages((prev) => [...prev, successMessage]);
      } else {
        console.error('[ERROR] No SIPOC data available for generateWorkflow action from any source');
      }
    } else if (actionType === 'generateService') {
      // Generate and execute service from workflowSipoc
      console.log('[DEBUG handleActionClick generateService] workflowSipoc:', workflowSipoc);

      // Prevent duplicate calls while loading
      if (isLoading) {
        console.log('[DEBUG generateService] Already loading, ignoring duplicate call');
        return;
      }

      if (workflowSipoc) {
        setIsLoading(true);

        // Create new session for service generation progress
        const currentMsgCount = chatMessages.length;
        const sessionId = createNewSession(currentMsgCount);
        console.log('[DEBUG generateService] Created session:', sessionId, 'at message index:', currentMsgCount);

        try {
          const result = await executeService(workflowSipoc);
          console.log('[DEBUG generateService] API result:', result);

          if (result.success && result.data) {
            console.log('[DEBUG generateService] result.data.processingSteps:', result.data.processingSteps);
            console.log('[DEBUG generateService] result.data.codeSnippet:', result.data.codeSnippet ? 'present' : 'missing');

            // Show processing steps (Analysis Process)
            if (result.data.processingSteps && result.data.processingSteps.length > 0) {
              console.log('[DEBUG generateService] Showing', result.data.processingSteps.length, 'processing steps');
              await showSessionProgress(sessionId, result.data.processingSteps);
            }

            // Extract workflowResult from the response - store but don't display yet
            // User will see the result after clicking "Yes, execute and return results"
            const workflowResult = result.data.workflowResult as ServiceExecutionResult | undefined;
            console.log('[DEBUG generateService] workflowResult:', workflowResult ? 'present' : 'missing');

            // Store the workflow result in pending state - don't display ServiceExecutionResultDisplay yet
            // The user needs to confirm they want to see the detailed results first
            if (workflowResult) {
              setPendingWorkflowResult(workflowResult);
              console.log('[DEBUG generateService] Stored workflowResult in pendingWorkflowResult');
            }

            // Build success message with short code preview
            const serviceName = result.data.serviceName || 'DividendProcessingService';
            let messageContent = `**Service Generated Successfully!**\n\n`;
            messageContent += `The service \`${serviceName}\` has been created and registered.\n\n`;

            // Show only a short preview of the code
            if (result.data.codeSnippet) {
              // Extract just the class definition header (first few lines)
              const codeLines = result.data.codeSnippet.split('\n');
              const previewLines = codeLines.slice(0, 8).join('\n'); // First 8 lines
              messageContent += `**Code Preview:**\n\`\`\`python\n${previewLines}\n    # ... (${codeLines.length - 8} more lines)\n\`\`\`\n\n`;
            }

            // Ask user if they want to execute the new service to process the original email request
            messageContent += `Would you like me to execute this new service to process your original email request?`;

            // Add success message with action button
            const successMessage: ChatMessage = {
              id: Date.now().toString(),
              role: 'assistant',
              content: messageContent,
              timestamp: new Date(),
              actions: [
                { id: 'returnData', label: 'Yes, execute and return results', type: 'returnData' },
                { id: 'done', label: 'No, I\'m done', type: 'done' },
              ],
            };
            console.log('[DEBUG generateService] Adding success message to chat');
            setChatMessages((prev) => {
              console.log('[DEBUG generateService] Previous messages count:', prev.length);
              return [...prev, successMessage];
            });
          } else {
            console.log('[DEBUG generateService] API returned success=false or no data');
          }
        } catch (error) {
          console.error('[ERROR] Service execution failed:', error);
          const errorMessage: ChatMessage = {
            id: Date.now().toString(),
            role: 'assistant',
            content: 'Sorry, there was an error executing the service. Please try again.',
            timestamp: new Date(),
          };
          setChatMessages((prev) => [...prev, errorMessage]);
        } finally {
          setIsLoading(false);
          console.log('[DEBUG generateService] Finished, isLoading set to false');
        }
      } else {
        console.error('[ERROR] No workflowSipoc available for generateService action');
      }
    } else if (actionType === 'returnData') {
      // User wants to see detailed results from the already executed service
      // Use the pendingWorkflowResult which was stored when service was generated
      const workflowResultToShow = pendingWorkflowResult || serviceExecutionResult;

      if (analysisResult && workflowResultToShow) {
        // Build detailed response message with table format (similar to first email query result)
        let responseContent = `**Service Execution Results**\n\n`;
        responseContent += `**Original Request:** ${analysisResult.userIntent}\n\n`;
        responseContent += `**Email Subject:** ${analysisResult.emailSubject}\n\n`;
        responseContent += `**Workflow:** ${workflowResultToShow.workflowType}\n\n`;
        responseContent += `**Status:** ${workflowResultToShow.completedSteps}/${workflowResultToShow.totalSteps} steps completed ✓\n\n`;

        // Show detailed results in table format
        responseContent += `**Results Detail:**\n\n`;

        // Build table based on workflow type
        if (workflowResultToShow.workflowType === 'dividend_processing') {
          // Dividend processing detail table
          responseContent += `| Metric | Value |\n`;
          responseContent += `|--------|-------|\n`;
          responseContent += `| Workflow Type | ${workflowResultToShow.workflowType} |\n`;
          responseContent += `| Total Steps | ${workflowResultToShow.totalSteps} |\n`;
          responseContent += `| Completed Steps | ${workflowResultToShow.completedSteps} |\n`;

          if (workflowResultToShow.summary) {
            const summary = workflowResultToShow.summary as Record<string, unknown>;
            if (summary.success_rate) responseContent += `| Success Rate | ${summary.success_rate} |\n`;
            if (summary.execution_status) responseContent += `| Execution Status | ${summary.execution_status} |\n`;
            if (summary.total_distribution) responseContent += `| Total Distribution | ¥${Number(summary.total_distribution).toLocaleString()} |\n`;
            if (summary.funds_processed) responseContent += `| Funds Processed | ${summary.funds_processed} |\n`;
            if (summary.accounts_processed) responseContent += `| Accounts Processed | ${summary.accounts_processed} |\n`;
            if (summary.report_id) responseContent += `| Report ID | ${summary.report_id} |\n`;
          }
        } else {
          // Generic detail table for other workflow types
          responseContent += `| Metric | Value |\n`;
          responseContent += `|--------|-------|\n`;
          responseContent += `| Workflow Type | ${workflowResultToShow.workflowType} |\n`;
          responseContent += `| Total Steps | ${workflowResultToShow.totalSteps} |\n`;
          responseContent += `| Completed Steps | ${workflowResultToShow.completedSteps} |\n`;

          if (workflowResultToShow.summary) {
            for (const [key, value] of Object.entries(workflowResultToShow.summary)) {
              if (key !== 'query_results' && key !== 'analysis_results' && value !== undefined) {
                const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                responseContent += `| ${formattedKey} | ${value} |\n`;
              }
            }
          }
        }

        responseContent += `\nThe service has successfully processed your request. This workflow is now saved and can automatically handle similar requests in the future.`;

        const resultMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: responseContent,
          timestamp: new Date(),
        };
        setChatMessages((prev) => [...prev, resultMessage]);

        // Now show the ServiceExecutionResultDisplay component
        if (pendingWorkflowResult) {
          setServiceExecutionResult(pendingWorkflowResult);
          setPendingWorkflowResult(null); // Clear pending state
        }
      } else if (analysisResult) {
        // Fallback: show analysis data if no execution result available
        const fallbackMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `**Email Analysis Data:**\n\n` +
            `**Subject:** ${analysisResult.emailSubject}\n\n` +
            `**Summary:** ${analysisResult.summary}\n\n` +
            `**Detected Intent:** ${analysisResult.userIntent}\n\n` +
            `**Suggested Action:** ${analysisResult.suggestedAction}\n\n` +
            (analysisResult.attachments && analysisResult.attachments.length > 0
              ? `**Attachments:** ${analysisResult.attachments.join(', ')}\n\n`
              : '') +
            `The service has been registered and is ready to process similar requests.`,
          timestamp: new Date(),
        };
        setChatMessages((prev) => [...prev, fallbackMessage]);
      } else {
        const noDataMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: 'The service has been successfully generated. No additional email data is available at this time.',
          timestamp: new Date(),
        };
        setChatMessages((prev) => [...prev, noDataMessage]);
      }
    } else if (actionType === 'done') {
      // User is done, just acknowledge
      const doneMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Great! The service has been saved. You can now process similar email requests automatically. Feel free to select another email to analyze.',
        timestamp: new Date(),
      };
      setChatMessages((prev) => [...prev, doneMessage]);
    } else if (actionType === 'wrong') {
      // SIPOC is wrong - ask for corrections with options
      setSipocDocument(null);
      const sipocCorrectionOptions = [
        { id: 'suppliers', label: 'Suppliers are incorrect', value: 'The suppliers in the SIPOC are incorrect.' },
        { id: 'inputs', label: 'Inputs are incorrect', value: 'The inputs in the SIPOC are incorrect.' },
        { id: 'process', label: 'Process steps are incorrect', value: 'The process steps in the SIPOC are incorrect.' },
        { id: 'outputs', label: 'Outputs are incorrect', value: 'The outputs in the SIPOC are incorrect.' },
        { id: 'customers', label: 'Customers are incorrect', value: 'The customers in the SIPOC are incorrect.' },
        { id: 'other-sipoc', label: 'Something else (I will explain)', value: '' },
      ];

      const aiMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'I apologize for the misunderstanding. Please select which part needs correction:',
        timestamp: new Date(),
        actions: sipocCorrectionOptions.map(opt => ({
          id: opt.id,
          label: opt.label,
          type: 'option' as const,
          value: opt.value,
        })),
      };
      setChatMessages((prev) => [...prev, aiMessage]);
    }
  }

  // Handle input submission from inline input boxes (for "Some information is missing" and "Something else" options)
  async function handleInputSubmit(inputValue: string, placeholder?: string) {
    // Add user's input as a message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };
    setChatMessages((prev) => [...prev, userMessage]);

    setIsLoading(true);

    try {
      // Determine the context based on placeholder
      const isMissingInfo = placeholder?.includes('missing or incorrect');
      const contextMessage = isMissingInfo
        ? `[USER_FEEDBACK_MISSING_INFO] The user indicates some information is missing or wrong. Here is their explanation: "${inputValue}". Please re-analyze considering this feedback, search for matching services based on the corrected understanding, and provide an updated response.`
        : `[USER_FEEDBACK_OTHER] The user has additional feedback: "${inputValue}". Please re-analyze considering this feedback, search for matching services, and provide an updated response.`;

      const result = await sendChatMessage(contextMessage, {
        emailIds: selection.selectedEmails,
        analysisResult: analysisResult || undefined,
      });

      if (result.success && result.data) {
        // Determine actions based on response
        let actions: ChatMessage['actions'] = undefined;

        if (result.data.actions && result.data.actions.length > 0) {
          // Use actions from backend response
          actions = result.data.actions.map((act: { id: string; label: string; type: string }) => ({
            id: act.id,
            label: act.label,
            type: act.type as 'confirm' | 'reject' | 'option' | 'generate',
          }));
        } else if (result.data.hasServiceMatch) {
          // Service found - show confirm/reject
          actions = [
            { id: 'yes', label: 'Yes, proceed', type: 'confirm' },
            { id: 'no', label: 'No, that\'s not right', type: 'reject' },
          ];
        } else if (result.data.sipoc) {
          // No service match but SIPOC generated - show generate workflow button
          actions = [
            { id: 'generate', label: 'Generate Workflow', type: 'generate' },
            { id: 'no', label: 'No, that\'s not right', type: 'reject' },
          ];
          setPendingSipoc(result.data.sipoc);
        } else {
          // Default Yes/No for confirmation
          actions = [
            { id: 'yes', label: 'Yes, proceed', type: 'confirm' },
            { id: 'no', label: 'No, that\'s not right', type: 'reject' },
          ];
        }

        // Only add chat message if response is not empty
        if (result.data.response && result.data.response.trim()) {
          const aiMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: result.data.response,
            timestamp: new Date(),
            actions,
          };
          setChatMessages((prev) => [...prev, aiMessage]);
        }
      }
    } catch (error) {
      console.error('Input submit failed:', error);
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your feedback. Please try again.',
        timestamp: new Date(),
        actions: [
          { id: 'no', label: 'Try again', type: 'reject' },
        ],
      };
      setChatMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-container">
      {/* Authentication Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={handleAuthComplete}
        onLogin={handleLogin}
      />

      {/* Permission Modal - shows after department popup */}
      <PermissionModal
        isOpen={showPermissionModal}
        department={userDepartment || ''}
        services={userServices}
        sharedFolders={sharedFolders}
        onContinue={handlePermissionComplete}
      />

      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === 'email' && isAuthenticated && (
        <div className="list-panel">
          {/* Sub-tab navigation for Email Folders / Email List */}
          <div className="email-subtab-nav">
            <button
              className={`subtab-btn ${emailSubTab === 'folders' ? 'active' : ''}`}
              onClick={handleBackToFolders}
            >
              Email Folders
            </button>
            {selectedFolderId && (
              <button
                className={`subtab-btn ${emailSubTab === 'emails' ? 'active' : ''}`}
                onClick={() => setEmailSubTab('emails')}
              >
                {folders.find(f => f.id === selectedFolderId)?.name || 'Emails'}
              </button>
            )}
          </div>

          {/* Email Folders View */}
          {emailSubTab === 'folders' && (
            <EmailFolder
              folders={folders}
              selectedFolderId={selectedFolderId}
              onFolderSelect={handleFolderSelect}
            />
          )}

          {/* Email List View */}
          {emailSubTab === 'emails' && selectedFolderId && (
            <EmailList
              emails={emails}
              selection={selection}
              onSelectionChange={handleEmailSelection}
              onEmailClick={handleEmailClick}
              onAnalyze={handleAnalyze}
            />
          )}
        </div>
      )}

      <div className="main-content">
        <AnalysisPanel
          analysisResult={analysisResult}
          messages={chatMessages}
          sipocDocument={sipocDocument}
          workflowSipoc={workflowSipoc}
          serviceExecutionResult={serviceExecutionResult}
          isLoading={isLoading}
          analysisSessions={analysisSessions}
          onToggleSessionCollapse={toggleSessionCollapse}
          onSendMessage={handleSendMessage}
          onActionClick={handleActionClick}
          onInputSubmit={handleInputSubmit}
          onGenerateSipoc={handleGenerateSipoc}
          onCollaborationComplete={showPendingSteps}
          onAnalysisUpdate={(updatedIntent, updatedAction) => {
            // Update the analysis result with user's edits
            if (analysisResult) {
              setAnalysisResult({
                ...analysisResult,
                userIntent: updatedIntent,
                suggestedAction: updatedAction,
              });
            }
          }}
          onGoOn={() => {
            // User confirmed the analysis result without modifications
            // Trigger the flow to continue - simulate clicking confirm
            if (analysisResult) {
              handleActionClick('confirm');
            }
          }}
          onReanalyze={async (updatedIntent, updatedAction) => {
            // User modified intent/action and wants to reanalyze
            // Clear current analysis and chat, then re-run analysis with updated context
            if (analysisResult && selection.selectedEmails.length > 0) {
              // Reset states for fresh analysis
              setChatMessages([]);
              setSipocDocument(null);
              setPendingSipoc(null);
              setWorkflowSipoc(null);
              setServiceExecutionResult(null);
              setPendingWorkflowResult(null);
              setAnalysisSessions([]);

              // Update analysis result with user's corrections before reanalyzing
              const updatedAnalysisResult = {
                ...analysisResult,
                userIntent: updatedIntent,
                suggestedAction: updatedAction,
              };
              setAnalysisResult(updatedAnalysisResult);

              // Re-run analysis (simulating the analyze button click)
              setIsLoading(true);
              const sessionId = createNewSession(0);

              try {
                const result = await analyzeEmails(selection.selectedEmails);

                if (result.success && result.data) {
                  // Show processing steps
                  if (result.data.processingSteps && result.data.processingSteps.length > 0) {
                    await showSessionProgress(sessionId, result.data.processingSteps);
                  }

                  // Update with new analysis but keep user's corrections if they're more specific
                  const newAnalysis = {
                    ...result.data,
                    // Keep user's intent if they provided a more specific one
                    userIntent: updatedIntent || result.data.userIntent,
                    suggestedAction: updatedAction || result.data.suggestedAction,
                  };
                  setAnalysisResult(newAnalysis);

                  // Build message content
                  let messageContent = `I've reanalyzed the email with your feedback.\n\n**Based on the updated context:** ${newAnalysis.userIntent}\n\n`;

                  if (newAnalysis.matchedService) {
                    messageContent += `**✓ Found Matching Service:** \`${newAnalysis.matchedService}\`\n\n`;
                    messageContent += `**Suggested Action:** ${newAnalysis.suggestedAction}\n\n`;
                    messageContent += `Would you like me to proceed with this action?`;
                  } else {
                    messageContent += `**✗ No Matching Service Found**\n\n`;
                    messageContent += `I can help you create a new service workflow for this request. Would you like to proceed?`;
                  }

                  // Complete the session
                  setAnalysisSessions(prev => prev.map(s =>
                    s.id === sessionId ? { ...s, isComplete: true } : s
                  ));

                  // Add AI message with actions
                  const aiMessage: ChatMessage = {
                    id: Date.now().toString(),
                    role: 'assistant',
                    content: messageContent,
                    timestamp: new Date(),
                    actions: [
                      { id: '1', label: 'Yes, proceed', type: 'confirm' },
                      { id: '2', label: 'No, let me modify', type: 'reject' },
                    ],
                  };
                  setChatMessages([aiMessage]);
                }
              } finally {
                setIsLoading(false);
              }
            }
          }}
        />
      </div>
    </div>
  );
}

export default App;
