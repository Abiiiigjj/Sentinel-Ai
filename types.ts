export interface ChatMessage {
  role: 'user' | 'model' | 'assistant';
  text: string;
  timestamp: Date;
  metadata?: {
    latency?: number;
    tokens?: number;
    vramUsed?: number;
    sources?: Array<{ filename: string; chunk_id: string }>;
    model?: string;
  };
}

export enum RiskLevel {
  MINIMAL = 'Minimal Risk',
  LIMITED = 'Limited Risk',
  HIGH = 'High Risk',
  UNACCEPTABLE = 'Unacceptable Risk',
}

export interface ComplianceCheck {
  piiDetected: boolean;
  gdprCompliant: boolean;
  euAiActRiskLevel: RiskLevel;
  dataEgress: boolean;
}

export interface DocumentChunk {
  id: string;
  content: string;
  metadata: {
    document_id: string;
    filename: string;
    chunk_index: number;
    pii_masked: boolean;
  };
}

export interface AuditEntry {
  id: number;
  timestamp: string;
  user_id: string;
  action: string;
  details: string;
  metadata?: Record<string, unknown>;
}