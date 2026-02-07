/**
 * Local LLM Service - Connects to SentinelAI Backend
 * Replaces Gemini API with local Ollama-powered backend
 */

const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatResponse {
  response: string;
  sources: Array<{ filename: string; chunk_id: string }>;
  metadata: {
    model: string;
    rag_enabled: boolean;
    context_chunks: number;
  };
}

export interface DocumentInfo {
  id: string;
  filename: string;
  uploaded_at: string;
  chunk_count: number;
  pii_detected: boolean;
  pii_summary?: string;
}

export interface ComplianceStats {
  total_documents: number;
  total_chunks: number;
  pii_documents: number;
  audit_entries: number;
  last_activity?: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  ollama_connected: boolean;
  model_loaded: boolean;
  vector_store_ready: boolean;
  timestamp: string;
}

/**
 * Check backend health status
 */
export const checkHealth = async (): Promise<HealthStatus> => {
  const response = await fetch(`${BACKEND_URL}/health`);
  if (!response.ok) {
    throw new Error('Backend not available');
  }
  return response.json();
};

/**
 * Send a chat message and get complete response
 */
export const sendChatMessage = async (
  messages: ChatMessage[],
  useRag: boolean = true,
  sessionId?: string
): Promise<ChatResponse> => {
  const response = await fetch(`${BACKEND_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages: messages.map(m => ({ role: m.role, content: m.content })),
      use_rag: useRag,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Stream chat response for real-time display
 */
export async function* streamChatMessage(
  messages: ChatMessage[],
  useRag: boolean = true,
  sessionId?: string
): AsyncGenerator<string, void, unknown> {
  const response = await fetch(`${BACKEND_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages: messages.map(m => ({ role: m.role, content: m.content })),
      use_rag: useRag,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Stream request failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const text = decoder.decode(value, { stream: true });
    yield text;
  }
}

/**
 * Upload a document for processing
 */
export const uploadDocument = async (file: File): Promise<DocumentInfo> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${BACKEND_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
};

/**
 * Get list of all documents
 */
export const getDocuments = async (): Promise<DocumentInfo[]> => {
  const response = await fetch(`${BACKEND_URL}/documents`);
  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }
  return response.json();
};

/**
 * Delete a document (GDPR: Right to erasure)
 */
export const deleteDocument = async (documentId: string): Promise<void> => {
  const response = await fetch(`${BACKEND_URL}/documents/${documentId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete document');
  }
};

/**
 * Get compliance statistics
 */
export const getComplianceStats = async (): Promise<ComplianceStats> => {
  const response = await fetch(`${BACKEND_URL}/compliance/stats`);
  if (!response.ok) {
    throw new Error('Failed to fetch compliance stats');
  }
  return response.json();
};

/**
 * Get audit log entries
 */
export const getAuditLog = async (
  limit: number = 100,
  offset: number = 0
): Promise<{ entries: any[]; limit: number; offset: number }> => {
  const response = await fetch(
    `${BACKEND_URL}/compliance/audit?limit=${limit}&offset=${offset}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch audit log');
  }
  return response.json();
};

/**
 * Legacy compatibility: Stream simulation (now uses real local LLM)
 */
export const streamLocalSimulation = async (
  history: { role: string; parts: { text: string }[] }[],
  message: string
) => {
  // Convert legacy format to new format
  const messages: ChatMessage[] = history.map(h => ({
    role: h.role === 'model' ? 'assistant' : h.role as 'user' | 'assistant',
    content: h.parts[0]?.text || '',
  }));
  
  messages.push({ role: 'user', content: message });

  // Return async iterator that mimics old API
  return {
    async *[Symbol.asyncIterator]() {
      for await (const chunk of streamChatMessage(messages)) {
        yield { text: () => chunk };
      }
    }
  };
};

/**
 * Legacy compatibility: Analyze compliance (now uses real PII detection)
 */
export const analyzeCompliance = async (text: string) => {
  // This is now handled by the backend during document upload
  // For chat messages, we can do a simple client-side check
  const piiPatterns = [
    /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/,  // Email
    /\b(?:\+49|0049|0)[\s\-]?(?:\d{2,4})[\s\-]?(?:\d{3,})/,  // German phone
    /\b[A-Z]{2}\d{2}[\s]?(?:\d{4}[\s]?){4,7}/,  // IBAN
  ];

  const piiDetected = piiPatterns.some(pattern => pattern.test(text));
  
  return {
    piiDetected,
    summary: piiDetected ? 'Mögliche PII erkannt' : 'Keine PII erkannt'
  };
};