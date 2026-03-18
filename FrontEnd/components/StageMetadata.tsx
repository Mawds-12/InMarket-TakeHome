'use client'

import { StageType, TokenUsage } from '@/lib/types'

interface StageMetadataProps {
  stageName: StageType
  metadata: Record<string, any>
}

export default function StageMetadata({ stageName, metadata }: StageMetadataProps) {
  const formatTokens = (usage?: TokenUsage) => {
    if (!usage) return null
    return `${usage.total_tokens.toLocaleString()} tokens`
  }

  const renderMetadataContent = () => {
    switch (stageName) {
      case 'jurisdiction':
        return (
          <div className="mt-2 text-xs text-gray-600 space-y-1">
            <div>State: <span className="font-medium">{metadata.state}</span></div>
            {metadata.inferred && (
              <div className="text-gray-500">Auto-detected from location</div>
            )}
          </div>
        )

      case 'issue_extraction':
        return (
          <div className="mt-2 text-xs text-gray-600 space-y-1">
            {metadata.issue_label && (
              <div>Issue: <span className="font-medium">{metadata.issue_label}</span></div>
            )}
            {metadata.topic_tags && metadata.topic_tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {metadata.topic_tags.slice(0, 3).map((tag: string, i: number) => (
                  <span key={i} className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">
                    {tag}
                  </span>
                ))}
                {metadata.topic_tags.length > 3 && (
                  <span className="text-gray-500">+{metadata.topic_tags.length - 3} more</span>
                )}
              </div>
            )}
            {metadata.case_query_preview && (
              <div className="mt-1">
                <div className="text-gray-500">Case Query:</div>
                <div className="font-mono text-xs bg-gray-50 p-1 rounded mt-0.5">
                  {metadata.case_query_preview}
                </div>
              </div>
            )}
            {metadata.token_usage && (
              <div className="text-blue-600 mt-1">
                {formatTokens(metadata.token_usage)}
              </div>
            )}
          </div>
        )

      case 'retrieval':
        return (
          <div className="mt-2 text-xs text-gray-600 space-y-1">
            {metadata.retrieval_info && (
              <div className="mb-2">
                <div>Mode: <span className="font-medium">{metadata.retrieval_info.search_mode}</span></div>
                <div className="font-mono text-xs bg-gray-50 p-1 rounded mt-1">
                  {metadata.retrieval_info.case_query_preview}
                </div>
              </div>
            )}
            <div className="flex items-center gap-4">
              <div>
                <span className="font-medium">{metadata.case_count || 0}</span> cases
              </div>
              {metadata.bill_count !== undefined && metadata.bill_count > 0 && (
                <div>
                  <span className="font-medium">{metadata.bill_count}</span> bills
                </div>
              )}
            </div>
            {metadata.mcp_call_details && (
              <div className="text-gray-500 mt-1">
                <div>Case search: {metadata.mcp_call_details.cases.duration_ms}ms</div>
                {metadata.mcp_call_details.bills.count > 0 && (
                  <div>Bill search: {metadata.mcp_call_details.bills.duration_ms}ms</div>
                )}
              </div>
            )}
          </div>
        )

      case 'reduction':
        return (
          <div className="mt-2 text-xs text-gray-600 space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-medium">{metadata.input_count}</span>
              <span className="text-gray-400">→</span>
              <span className="font-medium text-green-600">{metadata.filtered_count}</span>
              authorities
            </div>
            {metadata.token_usage && (
              <div className="text-blue-600">
                {formatTokens(metadata.token_usage)}
              </div>
            )}
          </div>
        )

      case 'brief_writing':
        return (
          <div className="mt-2 text-xs text-gray-600 space-y-1">
            <div>
              <span className="font-medium">{metadata.authority_count}</span> authorities cited
            </div>
            {metadata.token_usage && (
              <div className="text-blue-600">
                {formatTokens(metadata.token_usage)}
              </div>
            )}
          </div>
        )

      default:
        return null
    }
  }

  return <div className="stage-metadata">{renderMetadataContent()}</div>
}
