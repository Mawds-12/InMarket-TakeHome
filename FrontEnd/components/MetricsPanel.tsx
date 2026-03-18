'use client'

import { AnalysisProgress } from '@/lib/types'

interface MetricsPanelProps {
  progress: AnalysisProgress
}

export default function MetricsPanel({ progress }: MetricsPanelProps) {
  const completedStages = Object.values(progress.stages).filter(
    stage => stage.status === 'completed'
  ).length
  const totalStages = Object.keys(progress.stages).length
  const progressPercentage = (completedStages / totalStages) * 100

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900">Live Metrics</h3>

      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-600">Progress</span>
            <span className="text-xs font-medium text-gray-900">
              {completedStages}/{totalStages} stages
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {progress.totalDuration > 0 && (
          <div className="flex items-center justify-between py-2 border-t border-gray-200">
            <span className="text-xs text-gray-600">Total Duration</span>
            <span className="text-sm font-medium text-gray-900">
              {formatDuration(progress.totalDuration)}
            </span>
          </div>
        )}

        {progress.totalTokens > 0 && (
          <div className="flex items-center justify-between py-2 border-t border-gray-200">
            <span className="text-xs text-gray-600">Total Tokens</span>
            <span className="text-sm font-medium text-blue-600">
              {progress.totalTokens.toLocaleString()}
            </span>
          </div>
        )}

        {progress.currentStage && !progress.isComplete && (
          <div className="pt-2 border-t border-gray-200">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse mr-2" />
              <span className="text-xs text-gray-600">
                Processing: <span className="font-medium text-gray-900">
                  {progress.currentStage.replace('_', ' ')}
                </span>
              </span>
            </div>
          </div>
        )}

        {progress.isComplete && (
          <div className="pt-2 border-t border-gray-200">
            <div className="flex items-center text-green-600">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-xs font-medium">Analysis Complete</span>
            </div>
          </div>
        )}
      </div>

      <div className="pt-3 border-t border-gray-200">
        <h4 className="text-xs font-semibold text-gray-700 mb-2">Stage Breakdown</h4>
        <div className="space-y-1">
          {Object.entries(progress.stages).map(([name, stage]) => (
            <div key={name} className="flex items-center justify-between text-xs">
              <span className="text-gray-600 truncate">
                {name.replace('_', ' ')}
              </span>
              {stage.duration_ms !== undefined && (
                <span className="text-gray-500 ml-2">
                  {formatDuration(stage.duration_ms)}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
