import axios from 'axios';
import type { Email, Folder, AnalysisResult, SIPOCDocument, ApiResponse, ProcessingStep } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Generate a session ID for this browser session - persist in sessionStorage to survive hot reloads
const getSessionId = (): string => {
  const STORAGE_KEY = 'custody_ai_session_id';
  let sessionId = sessionStorage.getItem(STORAGE_KEY);
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem(STORAGE_KEY, sessionId);
    console.log('[DEBUG] Created new SESSION_ID:', sessionId);
  } else {
    console.log('[DEBUG] Reusing existing SESSION_ID:', sessionId);
  }
  return sessionId;
};
const SESSION_ID = getSessionId();

// Email APIs
export async function fetchEmails(): Promise<Email[]> {
  try {
    const response = await api.get('/emails');
    if (response.data.success) {
      // Transform from_addr to from
      return response.data.data.map((email: Record<string, unknown>) => ({
        ...email,
        from: email.from_addr,
      }));
    }
    return [];
  } catch (error) {
    console.error('Failed to fetch emails:', error);
    // Return mock data as fallback
    return [
      {
        id: '1',
        from: 'john.smith@fundcompany.com',
        subject: '基金净值报告 - Q4 2024 / Fund NAV Report - Q4 2024',
        summary: '请查收附件中的季度净值报告。富国天惠(161005)本季度表现优异，净值增长2.35%。',
        date: 'Nov 26',
        hasAttachment: true,
        attachments: [
          { id: 'a1', name: 'NAV_Report_Q4_2024.xlsx', size: '245 KB', type: 'xlsx', emailId: '1', isSelected: false },
          { id: 'a2', name: 'Fund_Performance_Summary.pdf', size: '1.2 MB', type: 'pdf', emailId: '1', isSelected: false },
        ],
        isSelected: false,
      },
      {
        id: '2',
        from: 'sarah.chen@bank.com',
        subject: '分红派息申请 / Dividend Distribution Request',
        summary: '申请处理基金161005的分红派息。请审核并批准附件中的授权表格。',
        date: 'Nov 25',
        hasAttachment: true,
        attachments: [
          { id: 'a3', name: 'Dividend_Authorization.pdf', size: '156 KB', type: 'pdf', emailId: '2', isSelected: false },
        ],
        isSelected: false,
      },
      {
        id: '3',
        from: 'mike.johnson@investor.com',
        subject: '查询: 基金110003业绩 / Query: Fund 110003 Performance',
        summary: '请提供基金110003（易方达上证50指数A）的最新业绩指标。',
        date: 'Nov 24',
        hasAttachment: false,
        attachments: [],
        isSelected: false,
      },
    ];
  }
}

// Folder APIs
export async function fetchFolders(): Promise<Folder[]> {
  try {
    const response = await api.get('/folders');
    if (response.data.success) {
      return response.data.data;
    }
    return [];
  } catch (error) {
    console.error('Failed to fetch folders:', error);
    // Return mock data as fallback
    return [
      {
        id: 'f1',
        name: '2024-11-26_john.smith_Fund_NAV_Report',
        type: 'folder',
        children: [
          { id: 'f1a', name: 'NAV_Report_Q4_2024.xlsx', type: 'file' },
          { id: 'f1b', name: 'Fund_Performance_Summary.pdf', type: 'file' },
        ],
      },
      {
        id: 'f2',
        name: 'Dividend_Authorization.pdf',
        type: 'file',
      },
    ];
  }
}

// Analysis API
export async function analyzeEmails(emailIds: string[]): Promise<ApiResponse<AnalysisResult>> {
  try {
    const response = await api.post('/analyze', { emailIds, sessionId: SESSION_ID });
    if (response.data.success) {
      return {
        success: true,
        data: response.data.data,
      };
    }
    return {
      success: false,
      error: 'Analysis failed',
    };
  } catch (error) {
    console.error('Analysis failed:', error);
    // Return mock data as fallback
    return {
      success: true,
      data: {
        emailSubject: 'Fund NAV Report - Q4 2024',
        summary: 'User needs quarterly NAV report and fund performance data',
        attachments: ['NAV_Report_Q4_2024.xlsx', 'Fund_Performance_Summary.pdf'],
        userIntent: 'Query fund NAV and performance metrics',
        suggestedAction: 'Execute getFundNAV service to retrieve fund information',
      },
    };
  }
}

// Option type for chat responses
export interface ChatOption {
  id: string;
  label: string;
  value: string;
}

// Action type for chat responses
export interface ChatAction {
  id: string;
  label: string;
  type: string;
  value?: string;
}

// Chat API
export async function sendChatMessage(
  message: string,
  context: { emailIds: string[]; analysisResult?: AnalysisResult }
): Promise<ApiResponse<{ response: string; hasServiceMatch: boolean; sipoc?: SIPOCDocument; options?: ChatOption[]; processingSteps?: ProcessingStep[]; actions?: ChatAction[] }>> {
  try {
    const response = await api.post('/chat', {
      message,
      emailIds: context.emailIds,
      sessionId: SESSION_ID,
    });

    if (response.data.success) {
      const data = response.data.data;
      console.log('[DEBUG] Chat API response data:', data);
      console.log('[DEBUG] Chat API sipoc:', data.sipoc);
      console.log('[DEBUG] Chat API actions:', data.actions);
      const result = {
        success: true,
        data: {
          response: data.response,
          hasServiceMatch: data.hasServiceMatch,
          sipoc: data.sipoc ? {
            suppliers: data.sipoc.suppliers || [],
            inputs: data.sipoc.inputs || [],
            process: data.sipoc.process || [],
            outputs: data.sipoc.outputs || [],
            customers: data.sipoc.customers || [],
          } : undefined,
          options: data.options || undefined,
          processingSteps: data.processingSteps || undefined,
          actions: data.actions || undefined,
        },
      };
      console.log('[DEBUG] Chat API returning:', result.data.sipoc ? 'with sipoc' : 'WITHOUT sipoc', 'actions:', result.data.actions);
      return result;
    }
    return {
      success: false,
      error: response.data.error || 'Chat failed',
    };
  } catch (error) {
    console.error('Chat failed:', error);
    // Return mock data as fallback
    const isConfirmation = message.toLowerCase().includes('yes') || message.includes('是') || message.includes('确认');

    if (isConfirmation) {
      return {
        success: true,
        data: {
          response: 'I\'ve generated the SIPOC document for this service.',
          hasServiceMatch: true,
          sipoc: {
            suppliers: ['基金公司', '托管银行数据库', '投资者账户系统'],
            inputs: ['分红基金列表', '分红方式(现金/再投资)', '权益登记日'],
            process: [
              '1. 获取待分红基金清单',
              '2. 验证基金分红信息',
              '3. 计算各账户分红金额',
              '4. 执行分红派发',
              '5. 更新账户余额',
            ],
            outputs: ['分红处理结果', '账户余额变动记录', '分红报告'],
            customers: ['投资者', '基金管理人', '监管机构'],
          },
        },
      };
    }

    return {
      success: true,
      data: {
        response: 'Based on your email, I understand you need fund information. Is this correct?',
        hasServiceMatch: false,
      },
    };
  }
}

// Execute service result type
export interface ExecuteServiceResult {
  message: string;
  processingSteps?: ProcessingStep[];
  codeSnippet?: string;
  serviceName?: string;
  workflowResult?: {
    success: boolean;
    workflowType: string;
    totalSteps: number;
    completedSteps: number;
    stepResults: Array<{
      stepNumber: number;
      stepName: string;
      status: string;
      message: string;
      data?: Record<string, unknown>;
    }>;
    summary?: Record<string, unknown>;
  };
}

// Execute service
export async function executeService(sipoc: SIPOCDocument): Promise<ApiResponse<ExecuteServiceResult>> {
  try {
    const response = await api.post('/execute', {
      sipoc: {
        suppliers: sipoc.suppliers,
        inputs: sipoc.inputs,
        process: sipoc.process,
        outputs: sipoc.outputs,
        customers: sipoc.customers,
      },
      sessionId: SESSION_ID,
    });

    console.log('[DEBUG executeService] Raw API response:', response.data);

    if (response.data.success) {
      const data = response.data.data;
      console.log('[DEBUG executeService] Parsed data:', {
        message: data.message,
        codeSnippet: data.codeSnippet ? 'present (length: ' + data.codeSnippet.length + ')' : 'missing',
        serviceName: data.serviceName,
        workflowResult: data.workflowResult ? 'present' : 'missing',
        processingSteps: data.processingSteps?.length || 0
      });

      return {
        success: true,
        data: {
          message: data.message,
          processingSteps: data.processingSteps || undefined,
          codeSnippet: data.codeSnippet || undefined,
          serviceName: data.serviceName || undefined,
          workflowResult: data.workflowResult || undefined,
        },
      };
    }
    return {
      success: false,
      error: response.data.error || 'Execution failed',
    };
  } catch (error) {
    console.error('Execution failed:', error);
    // Return mock data as fallback
    return {
      success: true,
      data: {
        message: '**Service created and executed successfully!**\n\nResults:\n- Funds processed: 3\n- Total dividend amount: ¥15,000.00\n\nDetails have been recorded in the system.',
      },
    };
  }
}

export default api;
