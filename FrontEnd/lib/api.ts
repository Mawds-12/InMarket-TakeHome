import { AnalyzeRequest, BriefResponse, StateDetectionResponse } from './types'

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

export async function detectState(): Promise<StateDetectionResponse> {
  try {
    const response = await fetch('/api/detect-state')
    
    if (!response.ok) {
      return { country: 'US', state: null, state_code: 'CA', confidence: 'fallback' }
    }
    
    return response.json()
  } catch (error) {
    console.error('State detection failed:', error)
    return { country: 'US', state: null, state_code: 'CA', confidence: 'fallback' }
  }
}
