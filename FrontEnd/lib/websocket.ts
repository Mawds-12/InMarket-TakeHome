import { WebSocketEvent, AnalysisProgress, StageType, StageInfo, StageStatus } from './types'

export type EventHandler = (event: WebSocketEvent) => void
export type ProgressHandler = (progress: AnalysisProgress) => void
export type ErrorHandler = (error: string) => void

export class AnalysisWebSocket {
  private ws: WebSocket | null = null
  private eventHandlers: EventHandler[] = []
  private progressHandler: ProgressHandler | null = null
  private errorHandler: ErrorHandler | null = null
  private progress: AnalysisProgress

  constructor() {
    this.progress = this.initializeProgress()
  }

  private initializeProgress(): AnalysisProgress {
    const stages: StageType[] = ['jurisdiction', 'issue_extraction', 'retrieval', 'ranking', 'brief_writing']
    const stageMap: Record<StageType, StageInfo> = {} as Record<StageType, StageInfo>
    
    stages.forEach(stage => {
      stageMap[stage] = {
        name: stage,
        status: 'pending'
      }
    })

    return {
      stages: stageMap,
      currentStage: null,
      totalDuration: 0,
      totalTokens: 0,
      isComplete: false
    }
  }

  connect(params: {
    question: string
    clause_text?: string
    state_override?: string
    search_mode?: string
    detected_state?: string
  }): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = 'ws://localhost:8000/ws/analyze'
      console.log('[WebSocket] Connecting to:', url)
      
      this.ws = new WebSocket(url)
      
      this.ws.onopen = () => {
        console.log('[WebSocket] Connected, sending analysis parameters')
        // Send parameters as JSON message after connection
        this.ws!.send(JSON.stringify(params))
        resolve()
      }

      this.ws.onerror = (event) => {
        const errorMsg = 'WebSocket connection error'
        if (this.errorHandler) {
          this.errorHandler(errorMsg)
        }
        reject(new Error(errorMsg))
      }

      this.ws.onmessage = (event) => {
        try {
          const wsEvent: WebSocketEvent = JSON.parse(event.data)
          this.handleEvent(wsEvent)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      this.ws.onclose = () => {
        // Connection closed, mark as complete if not already
        if (!this.progress.isComplete && !this.progress.error) {
          this.progress.isComplete = true
          this.notifyProgress()
        }
      }
    })
  }

  private handleEvent(event: WebSocketEvent) {
    // Notify all event handlers
    this.eventHandlers.forEach(handler => handler(event))

    // Update progress state
    switch (event.event_type) {
      case 'stage_started':
        this.progress.currentStage = event.stage
        this.progress.stages[event.stage].status = 'active'
        this.progress.stages[event.stage].startTime = event.timestamp
        break

      case 'stage_completed':
        this.progress.stages[event.stage].status = 'completed'
        this.progress.stages[event.stage].endTime = event.timestamp
        this.progress.stages[event.stage].duration_ms = event.duration_ms
        this.progress.stages[event.stage].metadata = event.metadata
        break

      case 'issue_extracted':
        if (this.progress.stages.issue_extraction.metadata) {
          this.progress.stages.issue_extraction.metadata = {
            ...this.progress.stages.issue_extraction.metadata,
            issue_label: event.issue_label,
            topic_tags: event.topic_tags,
            case_query_preview: event.case_query_preview,
            bill_query_preview: event.bill_query_preview,
            need_bills: event.need_bills,
            fact_points_count: event.fact_points_count,
            token_usage: event.token_usage
          }
        } else {
          this.progress.stages.issue_extraction.metadata = {
            issue_label: event.issue_label,
            topic_tags: event.topic_tags,
            case_query_preview: event.case_query_preview,
            bill_query_preview: event.bill_query_preview,
            need_bills: event.need_bills,
            fact_points_count: event.fact_points_count,
            token_usage: event.token_usage
          }
        }
        if (event.token_usage) {
          this.progress.totalTokens += event.token_usage.total_tokens
        }
        break

      case 'retrieval_started':
        if (!this.progress.stages.retrieval.metadata) {
          this.progress.stages.retrieval.metadata = {}
        }
        this.progress.stages.retrieval.metadata.retrieval_info = {
          case_query_preview: event.case_query_preview,
          bill_query_preview: event.bill_query_preview,
          search_mode: event.search_mode,
          state: event.state
        }
        break

      case 'retrieval_completed':
        if (!this.progress.stages.retrieval.metadata) {
          this.progress.stages.retrieval.metadata = {}
        }
        this.progress.stages.retrieval.metadata.case_count = event.case_count
        this.progress.stages.retrieval.metadata.bill_count = event.bill_count
        this.progress.stages.retrieval.metadata.mcp_call_details = event.mcp_call_details
        break

      case 'reduction_completed':
        if (!this.progress.stages.ranking.metadata) {
          this.progress.stages.ranking.metadata = {}
        }
        this.progress.stages.ranking.metadata.input_count = event.input_count
        this.progress.stages.ranking.metadata.filtered_count = event.filtered_count
        this.progress.stages.ranking.metadata.token_usage = event.token_usage
        if (event.token_usage) {
          this.progress.totalTokens += event.token_usage.total_tokens
        }
        break

      case 'brief_completed':
        if (!this.progress.stages.brief_writing.metadata) {
          this.progress.stages.brief_writing.metadata = {}
        }
        this.progress.stages.brief_writing.metadata.authority_count = event.authority_count
        this.progress.stages.brief_writing.metadata.token_usage = event.token_usage
        if (event.token_usage) {
          this.progress.totalTokens += event.token_usage.total_tokens
        }
        break

      case 'analysis_complete':
        this.progress.totalDuration = event.total_duration_ms
        this.progress.briefResponse = event.brief_response
        this.progress.isComplete = true
        break

      case 'error':
        this.progress.error = event.message
        if (event.stage) {
          const stageType = event.stage as StageType
          if (this.progress.stages[stageType]) {
            this.progress.stages[stageType].status = 'error'
          }
        }
        break
    }

    this.notifyProgress()
  }

  private notifyProgress() {
    if (this.progressHandler) {
      this.progressHandler({ ...this.progress })
    }
  }

  onEvent(handler: EventHandler) {
    this.eventHandlers.push(handler)
  }

  onProgress(handler: ProgressHandler) {
    this.progressHandler = handler
  }

  onError(handler: ErrorHandler) {
    this.errorHandler = handler
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  getProgress(): AnalysisProgress {
    return { ...this.progress }
  }

  reset() {
    this.disconnect()
    this.progress = this.initializeProgress()
    this.notifyProgress()
  }
}
