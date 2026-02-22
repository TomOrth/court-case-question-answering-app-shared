export interface User {
    id: string;
    email: string;
}

export interface AuthResponse {
    user: User;
    token: string;
}

export interface Case {
    case_id: number;
    case_name: string;
    court?: string;
    status: string;
}

export interface ChatSession {
    session_id: string; // UUID is a string in JS
    case_id: number;
    user_id: string;
    session_title: string;
    created_at: string;
    updated_at: string;
    case_name?: string;

    messages?: ChatMessage[];
}

export interface CreateSessionRequest {
    case_id: number;
}

export interface ReasoningStep {
    step_id: string;
    message_id: string;
    step_type: 'gathered_context' | 'reasoning' | 'tool_call' | 'tool_result';
    step_data: {
      step_number?: number;
      content?: string;  // For gathered_context, reasoning
      tool?: string;  // For tool_call, tool_result
      parameters?: any;  // For tool_call
      result?: string;  // For tool_result
      parent_id?: string;  // For tool_result (links to tool_call)
      status?: 'pending' | 'executing' | 'completed' | 'failed';  // For tool_call (UI only)
      [key: string]: any;  // allow other fields
    };
    step_order: number;
    created_at: string;

}

export interface ChatMessage {
    message_id: string;
    session_id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    created_at: string;
    reasoning_steps?: ReasoningStep[];
}

export interface ChunkData {
  chunk_id: string;
  chunk_index: number;
  chunk_text: string;
  case_id: number;
}

export interface DocumentData {
  doc_id: number;
  title: string;
  doc_date: string | null;
  document_type: string | null;
  file_url: string | null;
  clearinghouse_link: string | null;
  total_chunks: number;
}

export interface ChunkCitation {
  citation_id: string;
  citation_type: 'chunk';
  chunk: ChunkData;
  document: DocumentData;
}

export interface DocketEntryData {
  docket_entry_id: string;
  entry_number: string | null;
  date_filed: string | null;
  description: string;
  url: string | null;
  recap_pdf_url: string | null;
  case_id: number;
}

export interface DocketEntryCitation {
  citation_id: string;
  citation_type: 'docket_entry';
  docket_entry: DocketEntryData;
}

// Union type for type-safe handling
export type Citation = ChunkCitation | DocketEntryCitation;

// Preprocessing types
export interface PreprocessCaseResponse {
    case_id: number;
    case_name: string;
    status: string;
    documents_count: number;
    chunks_count: number;
    embeddings_count: number;
    docket_entries_count: number;
    message: string;
}