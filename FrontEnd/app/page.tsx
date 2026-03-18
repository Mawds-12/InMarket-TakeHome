'use client'

import { useState, useEffect } from 'react'
import { detectState } from '@/lib/api'
import { BriefResponse } from '@/lib/types'
import { useAnalysisWebSocket } from '@/hooks/useAnalysisWebSocket'
import AnalysisProgress from '@/components/AnalysisProgress'

const US_STATES = [
  { code: 'AL', name: 'Alabama' }, { code: 'AK', name: 'Alaska' }, { code: 'AZ', name: 'Arizona' },
  { code: 'AR', name: 'Arkansas' }, { code: 'CA', name: 'California' }, { code: 'CO', name: 'Colorado' },
  { code: 'CT', name: 'Connecticut' }, { code: 'DE', name: 'Delaware' }, { code: 'FL', name: 'Florida' },
  { code: 'GA', name: 'Georgia' }, { code: 'HI', name: 'Hawaii' }, { code: 'ID', name: 'Idaho' },
  { code: 'IL', name: 'Illinois' }, { code: 'IN', name: 'Indiana' }, { code: 'IA', name: 'Iowa' },
  { code: 'KS', name: 'Kansas' }, { code: 'KY', name: 'Kentucky' }, { code: 'LA', name: 'Louisiana' },
  { code: 'ME', name: 'Maine' }, { code: 'MD', name: 'Maryland' }, { code: 'MA', name: 'Massachusetts' },
  { code: 'MI', name: 'Michigan' }, { code: 'MN', name: 'Minnesota' }, { code: 'MS', name: 'Mississippi' },
  { code: 'MO', name: 'Missouri' }, { code: 'MT', name: 'Montana' }, { code: 'NE', name: 'Nebraska' },
  { code: 'NV', name: 'Nevada' }, { code: 'NH', name: 'New Hampshire' }, { code: 'NJ', name: 'New Jersey' },
  { code: 'NM', name: 'New Mexico' }, { code: 'NY', name: 'New York' }, { code: 'NC', name: 'North Carolina' },
  { code: 'ND', name: 'North Dakota' }, { code: 'OH', name: 'Ohio' }, { code: 'OK', name: 'Oklahoma' },
  { code: 'OR', name: 'Oregon' }, { code: 'PA', name: 'Pennsylvania' }, { code: 'RI', name: 'Rhode Island' },
  { code: 'SC', name: 'South Carolina' }, { code: 'SD', name: 'South Dakota' }, { code: 'TN', name: 'Tennessee' },
  { code: 'TX', name: 'Texas' }, { code: 'UT', name: 'Utah' }, { code: 'VT', name: 'Vermont' },
  { code: 'VA', name: 'Virginia' }, { code: 'WA', name: 'Washington' }, { code: 'WV', name: 'West Virginia' },
  { code: 'WI', name: 'Wisconsin' }, { code: 'WY', name: 'Wyoming' }
]

export default function Home() {
  const [question, setQuestion] = useState('')
  const [clauseText, setClauseText] = useState('')
  const [selectedState, setSelectedState] = useState('CA')
  const [stateWasDetected, setStateWasDetected] = useState(false)
  const [searchMode] = useState<'semantic' | 'keyword'>('semantic')
  const [result, setResult] = useState<BriefResponse | null>(null)
  const [showForm, setShowForm] = useState(true)
  
  const { progress, isConnected, error: wsError, connect, reset } = useAnalysisWebSocket()

  useEffect(() => {
    const loadStateDetection = async () => {
      const detection = await detectState()
      if (detection.state_code) {
        setSelectedState(detection.state_code)
        setStateWasDetected(true)
      }
    }
    loadStateDetection()
  }, [])

  const handleStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedState(e.target.value)
    setStateWasDetected(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    setShowForm(false)
    // Don't reset progress here - let it show until new data arrives

    try {
      await connect({
        question,
        clause_text: clauseText || undefined,
        state_override: selectedState,
        search_mode: searchMode,
        detected_state: selectedState
      })
    } catch (err) {
      console.error('WebSocket connection failed:', err)
      setShowForm(true)
    }
  }

  const handleNewAnalysis = () => {
    reset()
    setResult(null)
    setShowForm(true)
    setQuestion('')
    setClauseText('')
  }

  useEffect(() => {
    if (progress?.isComplete && progress.briefResponse) {
      setResult(progress.briefResponse)
    }
  }, [progress])

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Precedent Brief</h1>
          <p className="text-gray-900">AI-powered legal research triage</p>
        </header>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
          <h2 className="text-sm font-semibold text-gray-900 mb-2">How to Use</h2>
          <ol className="text-sm text-gray-900 space-y-1 mb-3">
            <li>1. Enter your legal question below</li>
            <li>2. Verify the jurisdiction (auto-detected from your location)</li>
            <li>3. Optionally add contract text or additional facts</li>
            <li>4. Click "Analyze Question" to get your research brief</li>
          </ol>
          <p className="text-xs text-gray-900">Not legal advice. Always verify sources with qualified counsel.</p>
        </div>

        {showForm && (
          <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 mb-8">
          <div className="mb-6">
            <label htmlFor="question" className="block text-sm font-medium text-gray-900 mb-2">
              Legal Question *
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              required
              minLength={10}
              rows={5}
              disabled={isConnected}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900"
              placeholder="Enter your legal question here..."
            />
          </div>

          <div className="mb-6">
            <label htmlFor="state" className="block text-sm font-medium text-gray-900 mb-2">
              Jurisdiction
            </label>
            <div className="flex items-center gap-3">
              <select
                id="state"
                value={selectedState}
                onChange={handleStateChange}
                disabled={isConnected}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900"
              >
                {US_STATES.map(state => (
                  <option key={state.code} value={state.code}>
                    {state.name}
                  </option>
                ))}
              </select>
              {stateWasDetected && (
                <span className="text-xs text-gray-900 bg-gray-100 px-2 py-1 rounded">
                  Detected from network
                </span>
              )}
            </div>
          </div>

          <div className="mb-6">
            <label htmlFor="clause" className="block text-sm font-medium text-gray-900 mb-2">
              Contract Clause or Facts (Optional)
            </label>
            <textarea
              id="clause"
              value={clauseText}
              onChange={(e) => setClauseText(e.target.value)}
              rows={3}
              disabled={isConnected}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900"
              placeholder="Paste relevant contract text or factual details..."
            />
          </div>

          {wsError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
              {wsError}
            </div>
          )}

          <button
            type="submit"
            disabled={isConnected || !question || question.length < 10}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Analyze Question
          </button>
        </form>
        )}

        {progress && !showForm && (
          <AnalysisProgress progress={progress} />
        )}

        {result && (
          <>
            <div className="mb-4">
              <button
                onClick={handleNewAnalysis}
                className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
              >
                New Analysis
              </button>
            </div>
            <div className="bg-white shadow rounded-lg p-6">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Issue Summary</h2>
              <p className="text-gray-900">{result.issue_summary}</p>
            </div>

            {result.pertinent_authorities.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Pertinent Authorities</h2>
                <div className="space-y-4">
                  {result.pertinent_authorities.map((authority, idx) => (
                    <div
                      key={idx}
                      className={`border-l-4 p-4 rounded-r ${
                        authority.kind === 'case'
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-green-500 bg-green-50'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-gray-900">{authority.title}</h3>
                        <span className="text-xs text-gray-900 uppercase px-2 py-1 bg-gray-50 rounded">
                          {authority.kind}
                        </span>
                      </div>
                      {authority.citation && (
                        <p className="text-sm text-gray-900 mb-1">{authority.citation}</p>
                      )}
                      {authority.court && (
                        <p className="text-sm text-gray-900 mb-2">{authority.court}</p>
                      )}
                      <p className="text-sm text-gray-900 mb-2">{authority.date}</p>
                      
                      <div className="mt-3">
                        <p className="text-sm font-medium text-gray-900 mb-1">Why Pertinent:</p>
                        <p className="text-sm text-gray-900">{authority.why_pertinent}</p>
                      </div>
                      
                      <div className="mt-3">
                        <p className="text-sm font-medium text-gray-900 mb-1">Key Point:</p>
                        <p className="text-sm text-gray-900">{authority.key_point}</p>
                      </div>
                      
                      <a
                        href={authority.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-3 text-sm text-blue-600 hover:text-blue-800"
                      >
                        View Source
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.fact_sensitive_considerations.length > 0 && (
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-3">Fact-Sensitive Considerations</h2>
                <ul className="list-disc list-inside space-y-1">
                  {result.fact_sensitive_considerations.map((consideration, idx) => (
                    <li key={idx} className="text-gray-900">{consideration}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="border-t pt-4">
              <p className="text-sm text-gray-900">{result.coverage_note}</p>
            </div>
          </div>
          </>
        )}
      </div>
    </main>
  )
}
