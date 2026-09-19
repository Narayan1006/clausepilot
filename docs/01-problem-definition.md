# 01 — Problem Definition

## Problem Statement

Legal documents — employment contracts, NDAs, rental agreements, and business contracts — are written in dense, technical language that is difficult for most people to understand without professional legal training.

This creates a significant accessibility gap:

- **Information asymmetry**: One party (employer, landlord, counterparty) typically has professional legal support; the other often does not.
- **Decision paralysis**: Users face important decisions (accepting a job, signing a lease) without understanding what they are agreeing to.
- **Key clause blindness**: Critical terms (non-competes, IP assignment, service bonds, termination clauses) are buried in dense text.
- **Evidence deficit**: Even when users seek AI help, they cannot verify where the information came from or whether it is actually in the document.
- **Missing information**: Users cannot tell what *isn't* in the document — which is often as important as what *is*.

## Why Existing Approaches Are Insufficient

| Approach | Problem |
|---|---|
| Upload PDF → ChatGPT | No citation. No grounding. No verification. Hallucination risk. |
| General legal chatbot | Gives generic legal info, not specific to *your* document |
| Law firm consultation | Expensive. Not accessible. Overkill for basic document review |
| Plain-language summaries | No evidence trail. No citation. Cannot answer follow-up questions |
| PDF text search | No semantic understanding. Cannot identify what is *missing* |

## Who Is Affected

- Job seekers reviewing employment offers
- Renters reviewing lease agreements
- Freelancers reviewing service agreements
- Entrepreneurs reviewing NDAs and partnership agreements
- Anyone who receives an important legal document and needs to understand it quickly

## What Users Need

1. **Plain-language explanation** of what the document says
2. **Evidence** — exact quotes with page and clause references
3. **Identification of missing information** — what the document doesn't say
4. **Conflict detection** — inconsistencies within the document
5. **Actionable guidance** — what to ask, what to clarify, what to verify
6. **Comparison** — how does this offer compare to another?
