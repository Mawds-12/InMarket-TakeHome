import { NextRequest, NextResponse } from 'next/server'

export async function GET(req: NextRequest) {
  try {
    const clientIp = req.headers.get('x-forwarded-for')?.split(',')[0].trim() 
      || req.headers.get('x-real-ip') 
      || '8.8.8.8'
    
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/dev/test-geo-lookup?ip=${clientIp}`, {
      method: 'POST',
    })
    
    if (!response.ok) {
      return NextResponse.json(
        { country: 'US', state: null, state_code: 'CA', confidence: 'fallback' },
        { status: 200 }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error detecting state:', error)
    return NextResponse.json(
      { country: 'US', state: null, state_code: 'CA', confidence: 'fallback' },
      { status: 200 }
    )
  }
}
