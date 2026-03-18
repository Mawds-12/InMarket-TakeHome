import { NextRequest, NextResponse } from 'next/server'

export async function GET(req: NextRequest) {
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/detect-state`, {
      headers: {
        'x-forwarded-for': req.headers.get('x-forwarded-for') || '',
      },
    })
    
    if (!response.ok) {
      return NextResponse.json(
        { country: 'US', state: null, state_code: 'CA', confidence: 'fallback' },
        { status: 200 }
      )
    }
    
    const data = await response.json()
    return NextResponse.json({
      country: 'US',
      state: null,
      state_code: data.state_code || 'CA',
      confidence: 'detected'
    })
  } catch (error) {
    console.error('Error detecting state:', error)
    return NextResponse.json(
      { country: 'US', state: null, state_code: 'CA', confidence: 'fallback' },
      { status: 200 }
    )
  }
}
