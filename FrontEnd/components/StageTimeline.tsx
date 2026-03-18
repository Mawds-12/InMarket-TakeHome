'use client'

import { AnalysisProgress, StageType } from '@/lib/types'
import StageMetadata from './StageMetadata'

interface StageTimelineProps {
  progress: AnalysisProgress
}

const STAGE_LABELS: Record<StageType, string> = {
  jurisdiction: 'Jurisdiction Detection',
  issue_extraction: 'Issue Extraction',
  retrieval: 'Authority Retrieval',
  reduction: 'Relevance Filtering',
  brief_writing: 'Brief Composition'
}

const STAGE_ORDER: StageType[] = ['jurisdiction', 'issue_extraction', 'retrieval', 'reduction', 'brief_writing']

export default function StageTimeline({ progress }: StageTimelineProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Stages</h3>
      
      <div className="relative">
        {STAGE_ORDER.map((stageName, index) => {
          const stage = progress.stages[stageName]
          const isLast = index === STAGE_ORDER.length - 1
          
          return (
            <div key={stageName} className="relative pb-8">
              {!isLast && (
                <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-gray-200" 
                     style={{
                       backgroundColor: stage.status === 'completed' ? '#10b981' : '#e5e7eb'
                     }}
                />
              )}
              
              <div className="relative flex items-start">
                <div className="flex items-center justify-center">
                  {stage.status === 'pending' && (
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                      <div className="w-3 h-3 rounded-full bg-gray-400" />
                    </div>
                  )}
                  
                  {stage.status === 'active' && (
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <div className="w-3 h-3 rounded-full bg-blue-600 animate-pulse" />
                    </div>
                  )}
                  
                  {stage.status === 'completed' && (
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                      <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                  
                  {stage.status === 'error' && (
                    <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                      <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
                
                <div className="ml-4 flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-gray-900">
                      {STAGE_LABELS[stageName]}
                    </h4>
                    {stage.duration_ms !== undefined && (
                      <span className="text-xs text-gray-500 ml-2">
                        {stage.duration_ms}ms
                      </span>
                    )}
                  </div>
                  
                  {stage.status === 'active' && (
                    <p className="text-sm text-blue-600">Processing...</p>
                  )}
                  
                  {stage.status === 'completed' && stage.metadata && (
                    <StageMetadata stageName={stageName} metadata={stage.metadata} />
                  )}
                  
                  {stage.status === 'error' && (
                    <p className="text-sm text-red-600">Failed</p>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
