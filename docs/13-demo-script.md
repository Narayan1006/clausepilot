# 13 — Demo Script

## Hackathon Demo Flow (2–4 minutes)

### Step 1: Landing Page (15 seconds)
Open ClausePilot in browser.
Point to:
- Tagline: "Understand the contract. Verify the evidence. Know what to ask next."
- Feature highlights: Attention Map, Evidence Citations, NOT_FOUND detection
- Legal disclaimer (concise, non-scary)

### Step 2: Upload (30 seconds)
- Click "Get Started"
- Upload `employment-contract-a.pdf` (synthetic document)
- Select decision context: **"Accept a job offer"**
- Click "Analyze"
- Show progress / extraction confirmation
- Mention: "The system extracted 4 pages and preserved every page boundary"

### Step 3: Attention Map (30 seconds)
Analysis page loads. Point to:
- 🔴 **HIGH**: Notice Period — "60 days required by employee"
- 🔴 **HIGH**: Non-Compete — "12-month restriction post-employment"
- 🟡 **CLARIFY**: Bonus Formula — "discretionary, formula not specified"
- ⚠️ **CONFLICT**: Work Arrangement — "Clause 4.2 vs Clause 9.1 inconsistency"
- ❓ **MISSING**: Stock Option vesting details

### Step 4: Click High-Attention Clause (20 seconds)
Click the "Notice Period" HIGH item.
- Evidence panel opens on the right
- Shows exact quote: *"The Employee may terminate this Agreement by providing sixty (60) calendar days written notice to the Company."*
- Shows: Clause 6.1 · Page 2
- Click "View in document" → PDF viewer opens to page 2

### Step 5: Ask a Grounded Question (30 seconds)
Type in the chat box:
> "What is my notice period?"

Response:
```
Your notice period is 60 calendar days.

GROUNDED  HIGH CONFIDENCE
Clause 6.1 · Page 2

"The Employee may terminate this Agreement by providing sixty (60) 
calendar days written notice to the Company."

[View evidence]
```

### Step 6: Ask a NOT_FOUND Question (30 seconds)
Type:
> "What happens to my stock options if I resign?"

Response:
```
I cannot determine this from the uploaded document.

NOT_FOUND

The agreement grants 10,000 stock options (Clause 2.3, Page 1) but 
refers to a separate Stock Option Agreement for vesting details.
That agreement was not uploaded.

Missing information:
• Vesting schedule
• Cliff period
• Post-termination exercise window
• Treatment of unvested options

Questions to ask HR:
• "Can you provide the Stock Option Agreement referenced in Clause 2.3?"
• "What happens to unvested options if I resign before the cliff?"
```

### Step 7: Questions for Lawyer (20 seconds)
Click "Questions" tab. Show:
```
For a legal professional:
□ Does the 12-month non-compete in Clause 10.1 apply in my state?
□ Is the service commitment in this agreement enforceable?
□ Can the variable bonus discretion in Clause 2.2 be legally limited?

For HR:
□ Can you clarify the bonus calculation formula?
□ Please provide the Stock Option Agreement (referenced in Clause 2.3)
□ Which clause controls remote work — 4.2 or 9.1?
```

### Step 8: Contract Comparison (40 seconds)
Click "Compare" tab.
Upload `employment-contract-b.pdf`.

Show side-by-side:
| Topic | Contract A | Contract B |
|---|---|---|
| Base Salary | $145,000 | $155,000 |
| Bonus | 20%, discretionary | 15%, formula-based |
| Notice | 60 days | 30 days |
| Non-Compete | 12 months | None |
| Remote | Hybrid (conflicted) | Fully remote |
| Stock Options | Vesting: separate doc | 4yr/1yr cliff |

### Closing Line
> "ClausePilot doesn't just answer questions — it shows you *where* the answer came from, tells you *what's missing*, and helps you prepare the *right questions* before you sign."

## Key Demo Points

- Every answer has evidence — no hallucination
- NOT_FOUND is a feature, not a failure
- Conflict detection is presented as "possible inconsistency" — not legal conclusion
- Legal disclaimer is always visible but not intrusive
