# SOC 2 Copilot

Checks infrastructure config (Terraform state or live AWS) against SOC 2 +
CIS control text, verifies its own findings before surfacing them, and
opens a GitHub PR with a plain-English report.

**Two scan paths exist on purpose -- this is a deliberate architecture
decision, not an unfinished feature:**

| | `/scan` (the product) | `/scan/agentic` (the demo) |
|---|---|---|
| Control flow | Fixed: every resource, every relevant control, every time | Model decides which resources/controls to check and when it's done |
| Coverage guarantee | Complete and auditable | Not guaranteed -- the model could decide it's checked "enough" |
| Status | What you'd actually ship | A working demonstration of understanding tool-calling/agents |

For a compliance tool specifically, "the model decides what counts as
thorough" is close to the worst place to introduce unpredictability --
a missed check fails silently, and there's no guarantee of full coverage.
`/scan`'s fixed pipeline exists because compliance coverage shouldn't be
improvised. `/scan/agentic` exists to show the trade-off was understood
and deliberately not taken, not because it's what you'd run in production.
Say this explicitly in a demo -- it's a stronger signal than pretending
the agentic path is the "real" product.

## Architecture

```
Terraform state file ─┐
                       ├─→ Normalizer ─→ Retrieval ─→ Reasoning agent ─→ Self-check ─→ PR + Langfuse trace
Live AWS API ──────────┘                    ↑
                                   Vector store (pgvector)
                                   SOC2 + CIS control text only
```

- **Vector store**: holds only static policy text (SOC 2 TSC + CIS AWS
  benchmark), chunked per-control and embedded once via `ingest.py`,
  using the free local `sentence-transformers` model (`all-MiniLM-L6-v2`)
  -- no embedding API cost.
- **Infra data**: pulled fresh every scan (Terraform state parse or live
  boto3 calls), normalized into one shape, never embedded or persisted
  into the vector store.
- **Reasoning agent**: one Gemini call per (resource, retrieved control)
  pair -- decides violation + severity + reasoning. Uses the Gemini free
  tier (`gemini-2.5-flash` by default).
- **Self-check pass**: a second Gemini call verifies the first agent's
  reasoning actually follows from the cited control text, to catch
  hallucinated findings before they reach a human.
- **GitHub PR**: opens a PR with a markdown report of confirmed findings,
  each citing its control and reasoning.
- **Langfuse**: traces retrieval hits, reasoning output, and self-check
  results per scan run -- useful to show live in a demo.
- **Streamlit frontend**: one page, one button, one findings table.
- **Agentic variant** (`app/agent_loop.py`): uses Gemini's "Automatic
  Function Calling" -- real Python functions passed directly as tools,
  SDK handles the call/execute/loop cycle. See the table above for why
  this is a secondary path, not the main one.

## Setup (one day build)

1. `cp .env.example .env` and fill in your keys (Gemini API key from
   Google AI Studio, GitHub token + demo repo, Langfuse keys; AWS
   profile only needed if using the live_api source).
2. `docker compose up -d` -- starts Postgres with pgvector.
3. `pip install -r requirements.txt --break-system-packages`
4. `python -m app.knowledge_base.ingest` -- one-time: chunks + embeds the
   SOC2/CIS docs into pgvector.
5. `uvicorn app.main:app --reload` -- starts the API on :8000.
6. `streamlit run frontend/streamlit_app.py` -- starts the frontend.
7. Click "Run scan" with source = `terraform` to scan the seeded
   `seed_data/sample.tfstate.json`, which has 4 deliberate violations:
   a public S3 bucket, missing bucket encryption, an open SSH+Postgres
   security group, and a wildcard IAM policy.

## What's explicitly out of scope for day one

- CloudFormation input adapter (same pattern as Terraform -- roadmap item)
- GCP live API adapter (AWS only for now)
- Multi-tenant auth
- Fine-tuned severity classifier (LLM assigns severity directly for now)
- Automatic infra *fixes* -- the PR contains a findings report, not a
  generated Terraform diff. Safe auto-remediation is a bigger, riskier
  problem to solve properly rather than fake for a demo.

## Demo script (~90 seconds)

1. Show the seeded Terraform state file has real, plausible violations.
2. Click "Run scan" in Streamlit.
3. Point at the findings table -- each row cites the exact control it
   violates, in the control's own language.
4. Open the generated PR -- show the report, note the self-check step
   ran before anything reached this PR.
5. Open the Langfuse trace -- walk through one resource's full decision
   path: what was retrieved, what the reasoning agent said, what the
   self-check verified.
6. (Optional, if there's time / the founder is technical) Mention the
   agentic variant exists: *"I also built a version where the model
   itself decides which resources and controls to check, using function
   calling -- but I deliberately didn't make that the main path, because
   in compliance, coverage shouldn't be improvised. This fixed pipeline
   guarantees every resource gets checked against every relevant control,
   every time."* This shows the trade-off was understood, not avoided.
