export interface IssueBundle {
  issue_label: string
  topic_tags: string[]
  case_query: string
  bill_query: string
  fact_sensitive_points: string[]
  need_bills: boolean
}

export interface Authority {
  kind: 'case' | 'bill'
  title: string
  citation: string | null
  court: string | null
  date: string
  url: string
  why_pertinent: string
  key_point: string
}

export interface BriefResponse {
  issue_summary: string
  jurisdiction_used: string
  state_was_inferred: boolean
  pertinent_authorities: Authority[]
  fact_sensitive_considerations: string[]
  coverage_note: string
}

export interface AnalyzeRequest {
  question: string
  clause_text: string | null
  state_override: string | null
  search_mode: 'semantic' | 'keyword'
  include_bills: boolean
}

export interface StateDetectionResponse {
  country: string
  state: string | null
  state_code: string | null
  confidence: string
}

// WebSocket Event Types
export type StageType = 'jurisdiction' | 'issue_extraction' | 'retrieval' | 'reduction' | 'brief_writing'
export type StageStatus = 'pending' | 'active' | 'completed' | 'error'

export interface TokenUsage {
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  requests: number
}

export interface BaseEvent {
  event_type: string
  timestamp: string
}

export interface StageStartedEvent extends BaseEvent {
  event_type: 'stage_started'
  stage: StageType
  data?: Record<string, any>
}

export interface StageCompletedEvent extends BaseEvent {
  event_type: 'stage_completed'
  stage: StageType
  duration_ms: number
  metadata: Record<string, any>
}

export interface IssueExtractedEvent extends BaseEvent {
  event_type: 'issue_extracted'
  issue_label: string
  topic_tags: string[]
  case_query_preview: string
  bill_query_preview: string
  need_bills: boolean
  fact_points_count: number
  token_usage?: TokenUsage
}

export interface RetrievalStartedEvent extends BaseEvent {
  event_type: 'retrieval_started'
  case_query_preview: string
  bill_query_preview: string | null
  search_mode: string
  state: string
}

export interface RetrievalCompletedEvent extends BaseEvent {
  event_type: 'retrieval_completed'
  case_count: number
  bill_count: number
  mcp_call_details: {
    cases: { duration_ms: number; count: number }
    bills: { duration_ms: number; count: number }
  }
}

export interface ReductionCompletedEvent extends BaseEvent {
  event_type: 'reduction_completed'
  input_count: number
  filtered_count: number
  token_usage?: TokenUsage
}

export interface BriefCompletedEvent extends BaseEvent {
  event_type: 'brief_completed'
  authority_count: number
  token_usage?: TokenUsage
}

export interface AnalysisCompleteEvent extends BaseEvent {
  event_type: 'analysis_complete'
  total_duration_ms: number
  total_tokens?: number
  brief_response: BriefResponse
}

export interface ErrorEvent extends BaseEvent {
  event_type: 'error'
  stage?: string
  message: string
  error_type: string
}

export type WebSocketEvent = 
  | StageStartedEvent
  | StageCompletedEvent
  | IssueExtractedEvent
  | RetrievalStartedEvent
  | RetrievalCompletedEvent
  | ReductionCompletedEvent
  | BriefCompletedEvent
  | AnalysisCompleteEvent
  | ErrorEvent

export interface StageInfo {
  name: StageType
  status: StageStatus
  startTime?: string
  endTime?: string
  duration_ms?: number
  metadata?: Record<string, any>
}

export interface AnalysisProgress {
  stages: Record<StageType, StageInfo>
  currentStage: StageType | null
  totalDuration: number
  totalTokens: number
  error?: string
  isComplete: boolean
  briefResponse?: BriefResponse
}
