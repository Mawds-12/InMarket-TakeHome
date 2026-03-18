User: Here are some UI fixes which you need to implement. Please thoroughly and 
repeatedly reference documentation in order to perform the changes. This is where the 
bulk of your reference content will come from. First, please create a step by step 
guide on how to use this section. Second, the box text is light which poorly contrasts 
with a white ui, third, try to discern the end users ip in the request on the front 
end in order to set the proper state.

---

Model: I've created a comprehensive plan at frontend-ui-fixes-2084bd.md addressing 
all three issues.

Plan Summary:
1. Usage Instructions - Add a step-by-step guide component between header and form:
   - What the app does (AI legal research triage)
   - 4-step process walkthrough
   - "Not legal advice" disclaimer
   - Dismissible with localStorage

2. Text Contrast Fixes - Current issues found in app/page.tsx:
   - Authority date: text-gray-500 → text-gray-700
   - Kind badges: text-gray-500 bg-white → text-gray-700 bg-gray-100
   - Citation/court: text-gray-600 → text-gray-800
   - Body text: text-gray-700 → text-gray-800
   - Coverage note: text-gray-500 → text-gray-600

3. Enhanced IP Detection - Update app/api/detect-state/route.ts with:
   - More header checks: cf-connecting-ip, x-client-ip, true-client-ip
   - Option A: Add ipify.org API fallback
   - Option B: Just improve header checking (recommended)

Questions for Confirmation:
1. Usage Instructions: Dismissible card with "Don't show again" (uses localStorage) 
   or always visible?
2. IP Detection: Call external API (ipify.org) for fallback, or just improve header 
   checking?
3. Badge text: Keep short "Detected from network" or add "— change if wrong" per 
   README.md mockup?

---

User: 1) no always visible this is a guided process
2) we have configuration for this in the backend, please reference and develop an api 
endpoint if needed. Check before asking again
3) I am confused what you're talking about, I am simply saying the color scheme does 
not work - please try again

---

Model: I've simplified the plan based on your feedback.

Updated Plan Summary:
1. Always-Visible Instructions - Step-by-step guide that stays visible (no dismiss 
   button) - "this is a guided process"

2. Backend API Endpoint - New GET /api/detect-state endpoint using existing 
   _extract_ip() and infer_state_from_ip() functions - no more dev endpoint

3. Fix Text Colors - Simple color changes: replace light grays (gray-500, gray-600) 
   with darker, more readable shades (gray-700, gray-800)

Files to change:
- Backend/routers/analyze.py - Add GET /api/detect-state endpoint
- FrontEnd/app/page.tsx - Add instructions section + fix 5 color issues
- FrontEnd/app/api/detect-state/route.ts - Call new Backend endpoint

The plan is now straightforward: add instructions, darken text colors, create proper 
Backend endpoint. Ready to implement when you confirm.

[Implemented]

Frontend UI Fixes Complete ✓

1. Always-Visible Usage Instructions ✓
Added a blue info card between the header and form with:
- "How to Use" heading
- 4-step numbered guide
- Disclaimer: "Not legal advice. Always verify sources with qualified counsel."

2. Fixed Text Colors for Better Readability ✓
- Detection badge: gray-500 → gray-700
- Case/Bill label: gray-500 bg-white → gray-800 bg-gray-50
- Citation/Court: gray-600 → gray-800
- Date: gray-500 → gray-700
- Coverage note: gray-500 → gray-600

3. Created Proper Backend Endpoint ✓
- Backend: New GET /api/detect-state in routers/analyze.py using existing _extract_ip() 
  and infer_state_from_ip()
- Frontend: Updated app/api/detect-state/route.ts to call Backend's /api/detect-state 
  instead of dev endpoint, forwarding IP headers properly