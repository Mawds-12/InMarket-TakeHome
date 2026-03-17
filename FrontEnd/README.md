# Frontend — Precedent Brief

The single-page research workspace. A structured form at the top, results sections below.
No chat bubbles. No open-ended back-and-forth. The UI is shaped around the output format.

---

## Setup

```bash
cd FrontEnd
npm install
cp .env.example .env.local
# Set BACKEND_URL in .env.local (default: http://localhost:8000)
npm run dev
```

Open http://localhost:3000

---

## Planned File Structure

```
FrontEnd/
├── README.md                ← This file
├── package.json
├── .env.example
├── next.config.js
├── tailwind.config.js
├── app/                     ← Next.js App Router
│   ├── layout.tsx           ← Root layout, fonts, global styles
│   ├── page.tsx             ← Main page — imports ResearchWorkspace
│   └── api/
│       └── analyze/
│           └── route.ts     ← Next.js API route — proxies to Backend, forwards IP
├── components/
│   ├── ResearchWorkspace.tsx    ← Top-level layout component
│   ├── form/
│   │   ├── QuestionInput.tsx    ← Large textarea for the legal question
│   │   ├── JurisdictionSelector.tsx ← State dropdown with "auto-detected" badge
│   │   ├── ClauseInput.tsx      ← Optional clause/facts textarea
│   │   ├── SearchModeToggle.tsx ← Cases only / Bills only / Both
│   │   └── AnalyzeButton.tsx    ← Submit + loading state
│   ├── results/
│   │   ├── IssueSummaryCard.tsx     ← Detected issue framing
│   │   ├── AuthorityCard.tsx        ← Single case or bill card (collapsed by default)
│   │   ├── AuthoritiesList.tsx      ← Maps over pertinent_authorities
│   │   ├── ConsiderationsList.tsx   ← Fact-sensitive considerations bullets
│   │   └── CoverageNote.tsx         ← Terse note about what was searched/excluded
│   └── ui/
│       ├── Badge.tsx            ← "State auto-detected" / "Inferred" badge
│       ├── Spinner.tsx          ← Loading indicator
│       └── ErrorMessage.tsx     ← Inline error display
└── lib/
    ├── api.ts               ← fetchBrief() function — calls /api/analyze route
    └── types.ts             ← TypeScript interfaces matching BriefResponse schema
```

---

## Page Layout

```
┌──────────────────────────────────────────────────────────┐
│  Precedent Brief                          [not legal advice] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Legal Question *                                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Describe your situation or legal question...      │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Jurisdiction                                            │
│  ┌──────────────────────┐  🔵 Detected from network     │
│  │  Oregon              ▼│  (change if wrong)           │
│  └──────────────────────┘                               │
│                                                          │
│  Contract clause or additional facts (optional)          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Paste a contract clause or relevant facts...      │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Search scope:  ● Cases + Bills   ○ Cases only           │
│                                                          │
│  [  Analyze  ]   [ Reset ]                               │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  RESULTS (shown after analysis)                          │
│                                                          │
│  ┌─ Issue ──────────────────────────────────────────────┐ │
│  │  This appears to raise a contract-formation question │ │
│  │  about whether informal text messages can constitute │ │
│  │  a binding service agreement.                        │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─ Smith v. Digital Works LLC  [Oregon, 2019] ─────────┐ │
│  │  Why pertinent: Addresses whether informal electronic │ │
│  │  communications can satisfy acceptance requirement.  │ │
│  │  ▶ Show key point                                    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─ Considerations ────────────────────────────────────┐  │
│  │  • Whether messages contained a definite price       │  │
│  │  • Whether work began after the messages             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                          │
│  Searched OR case law + OR bills. 2 of 8 case results   │
│  dropped as factually distant.                           │
└──────────────────────────────────────────────────────────┘
```

---

## Key UX Details

### Jurisdiction selector
- On first load: pre-filled with the IP-inferred state
- Shows a small badge: "Detected from network — change if wrong"
- Once the user manually selects a state, the badge changes to "Manually selected"
- Options: all 50 US states + "Federal only" + "Nationwide (all jurisdictions)"

### Authority cards
- Collapsed by default — only `why_pertinent` is visible
- Expand on click to show `key_point` and a link to the source
- Case cards show: case name, court, date, citation
- Bill cards show: bill ID, title, latest action, session

### Loading state
- The Analyze button shows a spinner and "Researching..." text
- Form inputs are disabled during the request
- Show a subtle progress message: "Extracting issue → Searching cases → Reducing results"

### Error states
- If the backend returns `no_results`: show "No pertinent authorities found for this question.
  Try rephrasing or broadening the jurisdiction."
- If the backend is unreachable: show "Research service unavailable. Try again."
- Never show raw error objects to the user

### Debug mode (dev only)
- If `NEXT_PUBLIC_SHOW_DEBUG_TOGGLE=true`, show a small toggle at the bottom
- "Show dropped results" — displays weak results that were filtered out
- Useful for testing the reducer; hidden in demo mode

---

## TypeScript Types (lib/types.ts)

```typescript
export interface IssueBundle {
  issue_label: string;
  topic_tags: string[];
  case_query: string;
  bill_query: string;
  fact_sensitive_points: string[];
  need_bills: boolean;
}

export interface Authority {
  kind: "case" | "bill";
  title: string;
  citation: string | null;
  court: string | null;
  date: string;
  url: string;
  why_pertinent: string;
  key_point: string;
}

export interface BriefResponse {
  issue_summary: string;
  jurisdiction_used: string;
  state_was_inferred: boolean;
  pertinent_authorities: Authority[];
  fact_sensitive_considerations: string[];
  coverage_note: string;
}

export interface AnalyzeRequest {
  question: string;
  clause_text: string | null;
  state_override: string | null;
  search_mode: "semantic" | "keyword";
  include_bills: boolean;
}
```

---

## Next.js API Route — app/api/analyze/route.ts

The browser never calls the Backend directly. All requests go through this route, which:
1. Extracts the real client IP from request headers
2. Forwards the request to the Backend
3. Returns the Backend's response

```typescript
// app/api/analyze/route.ts (pseudo-code)
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const clientIp =
    req.headers.get("x-forwarded-for")?.split(",")[0].trim() ?? "unknown";

  const response = await fetch(`${process.env.BACKEND_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, request_ip: clientIp }),
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
```

---

## Required Packages (package.json dependencies)

```json
{
  "dependencies": {
    "next": "^14",
    "react": "^18",
    "react-dom": "^18"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/react": "^18",
    "@types/node": "^20",
    "tailwindcss": "^3",
    "autoprefixer": "^10",
    "postcss": "^8"
  }
}
```