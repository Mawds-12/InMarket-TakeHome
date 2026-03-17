import { AnalyzeRequest, BriefResponse } from './types'

export async function fetchBrief(request: AnalyzeRequest): Promise<BriefResponse> {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Failed to fetch brief')
  }

  return response.json()
}
