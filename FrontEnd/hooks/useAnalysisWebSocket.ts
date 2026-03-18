import { useState, useEffect, useCallback, useRef } from 'react'
import { AnalysisWebSocket } from '@/lib/websocket'
import { AnalysisProgress, WebSocketEvent } from '@/lib/types'

interface UseAnalysisWebSocketReturn {
  progress: AnalysisProgress | null
  isConnected: boolean
  error: string | null
  connect: (params: {
    question: string
    clause_text?: string
    state_override?: string
    search_mode?: string
    detected_state?: string
  }) => Promise<void>
  disconnect: () => void
  reset: () => void
}

export function useAnalysisWebSocket(): UseAnalysisWebSocketReturn {
  const [progress, setProgress] = useState<AnalysisProgress | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<AnalysisWebSocket | null>(null)

  useEffect(() => {
    // Initialize WebSocket client
    wsRef.current = new AnalysisWebSocket()

    // Set up progress handler
    wsRef.current.onProgress((newProgress) => {
      setProgress(newProgress)
    })

    // Set up error handler
    wsRef.current.onError((errorMsg) => {
      setError(errorMsg)
      setIsConnected(false)
    })

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect()
      }
    }
  }, [])

  const connect = useCallback(async (params: {
    question: string
    clause_text?: string
    state_override?: string
    search_mode?: string
    detected_state?: string
  }) => {
    if (!wsRef.current) return

    try {
      setError(null)
      setIsConnected(false)
      // Reset WebSocket state for clean analysis
      wsRef.current.reset()
      await wsRef.current.connect(params)
      setIsConnected(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
      setIsConnected(false)
      throw err
    }
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect()
      setIsConnected(false)
    }
  }, [])

  const reset = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.reset()
      setProgress(null)
      setIsConnected(false)
      setError(null)
    }
  }, [])

  return {
    progress,
    isConnected,
    error,
    connect,
    disconnect,
    reset
  }
}
