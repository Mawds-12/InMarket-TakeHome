# Code Standards — Frontend

This is a single-page research workspace built with Next.js App Router.
A structured form at the top, results sections below.
No chat interface. No open-ended layout. The UI is shaped around the output format.

---

## Core Philosophy

Components do one thing. State lives as close to where it's used as possible.
The browser never calls external APIs directly — all requests go through a
Next.js API route. Types live in one place and are never duplicated.

---

## File Header Block

Required at the top of every file. One short paragraph. Omit fields that have
nothing useful to say.

```typescript
// components/results/AuthorityCard.tsx
//
// Renders a single case or bill authority as a collapsible card.
// Collapsed by default; expands on click to show key_point and a source link.
```

```typescript
// components/form/JurisdictionSelector.tsx
//
// Dropdown for selecting the search jurisdiction.
// Pre-filled with the IP-inferred state; shows a badge indicating whether
// the current value was auto-detected or manually chosen by the user.
```

```typescript
// lib/api.ts
//
// All fetch calls to the backend proxy route (/api/analyze).
// Components never call fetch directly — they use these functions.
```

For simple files (e.g., `lib/types.ts`, `components/ui/Spinner.tsx`), one line is enough.

---

## Inline Comments

Add a comment only when the code cannot explain itself.

```typescript
// BAD — narrates the code
const [open, setOpen] = useState(false) // track whether card is open

// GOOD — explains why the default matters
// Collapsed by default so long why_pertinent text doesn't overwhelm the list view.
const [open, setOpen] = useState(false)
```

```typescript
// BAD
authorities.filter(a => a.kind === "case") // filter to cases only

// GOOD — explains a policy decision, not the mechanics
// Bills are rendered after cases regardless of API return order
// so the user sees case law first.
const cases = authorities.filter(a => a.kind === "case")
const bills = authorities.filter(a => a.kind === "bill")
```

Never comment:
- What a clearly named prop or variable holds
- What a clearly named component does
- Disabled code — delete it, git has history

---

## Folder Structure

```
FrontEnd/
├── app/
│   ├── layout.tsx                  ← Root layout, fonts, global styles only
│   ├── page.tsx                    ← Imports and renders ResearchWorkspace
│   └── api/
│       └── analyze/
│           └── route.ts            ← Proxy to Backend; injects client IP
├── components/
│   ├── ResearchWorkspace.tsx       ← Top-level layout: form + results
│   ├── form/
│   │   ├── QuestionInput.tsx       ← Legal question textarea
│   │   ├── JurisdictionSelector.tsx ← State dropdown with auto-detect badge
│   │   ├── ClauseInput.tsx         ← Optional clause/facts textarea
│   │   ├── SearchModeToggle.tsx    ← Cases + bills / cases only toggle
│   │   └── AnalyzeButton.tsx       ← Submit button with loading state
│   ├── results/
│   │   ├── IssueSummaryCard.tsx    ← Detected issue framing
│   │   ├── AuthoritiesList.tsx     ← Maps over pertinent_authorities
│   │   ├── AuthorityCard.tsx       ← Single case or bill card
│   │   ├── ConsiderationsList.tsx  ← Fact-sensitive considerations
│   │   └── CoverageNote.tsx        ← What was searched / excluded
│   └── ui/
│       ├── Badge.tsx               ← "Auto-detected" / "Manually selected"
│       ├── Spinner.tsx             ← Loading indicator
│       └── ErrorMessage.tsx        ← Inline error display
└── lib/
    ├── api.ts                      ← All fetch calls (one place)
    └── types.ts                    ← All shared TypeScript interfaces (one place)
```

---

## Component Rules

### One component, one file, one job

```tsx
// BAD — two concerns in one component
export function ResultsSection({ brief }: { brief: BriefResponse }) {
  return (
    <div>
      <h2>{brief.issue_summary}</h2>
      {brief.pertinent_authorities.map(a => (
        <div key={a.title}>
          <p>{a.why_pertinent}</p>
          {/* expand/collapse logic inline */}
        </div>
      ))}
    </div>
  )
}

// GOOD — composed from focused components
// components/results/AuthoritiesList.tsx
export function AuthoritiesList({ authorities }: { authorities: Authority[] }) {
  return (
    <ul>
      {authorities.map(a => (
        <AuthorityCard key={a.title} authority={a} />
      ))}
    </ul>
  )
}

// components/results/AuthorityCard.tsx — handles its own expand/collapse
```

### Props — type inline for simple components, extract interface for complex ones

```tsx
// Simple — type inline
export function CoverageNote({ note }: { note: string }) {
  return <p className="text-sm text-gray-500">{note}</p>
}

// Complex — extract interface above the component
interface AuthorityCardProps {
  authority: Authority
  defaultOpen?: boolean
}

export function AuthorityCard({ authority, defaultOpen = false }: AuthorityCardProps) {
  const [open, setOpen] = useState(defaultOpen)
  ...
}
```

### Naming — match the file name exactly

The component exported from `AuthorityCard.tsx` is named `AuthorityCard`.
The component exported from `JurisdictionSelector.tsx` is named `JurisdictionSelector`.
No mismatches.

---

## State Management

Keep state as close to where it's used as possible.
Don't lift state higher than necessary.

```tsx
// BAD — lifted to parent when only AuthorityCard cares about open/closed
const [openCardId, setOpenCardId] = useState<string | null>(null)

// GOOD — local to the card that owns it
export function AuthorityCard({ authority }: AuthorityCardProps) {
  const [open, setOpen] = useState(false)
  ...
}
```

The main page-level state (form inputs, brief response, loading, error) lives in
`ResearchWorkspace.tsx` because the form and results both depend on it.

---

## API Calls — lib/api.ts only

Components never call `fetch` directly. All network calls live in `lib/api.ts`.

```typescript
// lib/api.ts
//
// All fetch calls to the backend proxy route (/api/analyze).
// Components never call fetch directly — they use these functions.

import type { AnalyzeRequest, BriefResponse } from "./types"

export async function fetchBrief(request: AnalyzeRequest): Promise<BriefResponse> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({}))
    throw new Error(error.message ?? "Analysis failed")
  }

  return res.json()
}
```

Usage in a component:

```tsx
import { fetchBrief } from "@/lib/api"

const brief = await fetchBrief({ question, state_override, clause_text, include_bills })
```

---

## Next.js API Route — app/api/analyze/route.ts

This route proxies the browser request to the Backend.
It injects the real client IP before forwarding.
No transformation, no business logic.

```typescript
// app/api/analyze/route.ts
//
// Proxies POST /api/analyze from the browser to the Backend.
// Injects the real client IP from request headers before forwarding.

import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  const body = await req.json()
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0].trim() ?? "unknown"

  const res = await fetch(`${process.env.BACKEND_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, request_ip: ip }),
  })

  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}
```

`BACKEND_URL` is a server-side env variable. It is never prefixed with `NEXT_PUBLIC_`.

---

## Types — lib/types.ts only

Every interface used by more than one file lives in `lib/types.ts`.
Never duplicate a type. Never define a shared type inside a component file.

```typescript
// lib/types.ts — single source of truth for all shared interfaces

export interface Authority {
  kind: "case" | "bill"
  title: string
  citation: string | null
  court: string | null
  date: string
  url: string
  why_pertinent: string
  key_point: string
}

export interface BriefResponse {
  issue_summary: string
  jurisdiction_used: string
  state_was_inferred: boolean
  pertinent_authorities: Authority[]
  fact_sensitive_considerations: string[]
  coverage_note: string
}

export interface AnalyzeRequest {
  question: string
  clause_text: string | null
  state_override: string | null
  search_mode: "semantic" | "keyword"
  include_bills: boolean
}
```

Component-local shapes (a prop interface used by exactly one component) can be
typed inline at that component. They do not need to go in `lib/types.ts`.

---

## Error Handling in Components

Never show raw error objects or status codes to the user.
Handle three cases: loading, error, and empty results.

```tsx
// components/ResearchWorkspace.tsx (excerpt)

{loading && <Spinner />}

{error && (
  <ErrorMessage message="Research service unavailable. Please try again." />
)}

{brief && brief.pertinent_authorities.length === 0 && (
  <ErrorMessage message="No pertinent authorities found. Try rephrasing or broadening the jurisdiction." />
)}

{brief && brief.pertinent_authorities.length > 0 && (
  <AuthoritiesList authorities={brief.pertinent_authorities} />
)}
```

---

## Naming

| Thing | Convention | Example |
|---|---|---|
| Component files | `PascalCase.tsx` | `AuthorityCard.tsx` |
| Lib files | `camelCase.ts` | `api.ts`, `types.ts` |
| Components | `PascalCase` | `AuthorityCard` |
| Functions | `camelCase` | `fetchBrief()` |
| Interfaces | `PascalCase` | `BriefResponse` |
| Props interfaces | `{ComponentName}Props` | `AuthorityCardProps` |
| Env vars (server) | `SCREAMING_SNAKE_CASE` | `BACKEND_URL` |
| Env vars (public) | `NEXT_PUBLIC_` prefix | `NEXT_PUBLIC_SHOW_DEBUG_TOGGLE` |

---

## Function and Component Length

If a component's JSX exceeds ~30 lines, it is likely doing two things.
Extract the second thing into its own component.

If a utility function exceeds ~20 lines, ask whether it has a second responsibility.
If it does, extract it. Don't split artificially just to hit a line count.