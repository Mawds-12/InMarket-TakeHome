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
