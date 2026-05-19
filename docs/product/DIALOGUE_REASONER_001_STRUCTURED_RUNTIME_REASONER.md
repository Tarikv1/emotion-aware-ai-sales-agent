# DIALOGUE-REASONER-001 Structured Runtime Reasoner

`DIALOGUE-REASONER-001` adds a runtime-owned structured reasoning layer for the supervised live demo failures that deterministic routing handled too narrowly.

The checkpoint does not replace the live-demo response path with freeform LLM speech. It creates the contract needed for broader reasoning:

```text
transcript + session state + campaign facts
-> runtime/core/dialogue_reasoner.py
-> strict intent/strategy JSON
-> future guarded response composer
-> existing safety/style/voice layers
```

## Scope

- Runtime module: `runtime/core/dialogue_reasoner.py`
- Frozen cases: `research/experiments/cases/dialogue-reasoner-001-live-demo-failures.json`
- Runner: `scripts/run_dialogue_reasoner_001_baseline.py`
- Validator: `scripts/validate_dialogue_reasoner_001.py`
- Generated evidence:
  - `research/experiments/generated/DIALOGUE-REASONER-001/result.json`
  - `research/experiments/generated/DIALOGUE-REASONER-001/report.md`

The reasoner returns only structured JSON fields:

- `dialogue_act`
- `buyer_intent`
- `resolved_topic`
- `sales_stage`
- `response_strategy`
- `must_include`
- `must_avoid`
- `safety_boundary`
- `confidence`

## Why This Exists

The live-demo failures were not only wording bugs. Several turns required understanding the buyer's dialogue act before selecting a response:

- `where were you calling from again?` is caller identity repair, not fit/price/topic routing.
- `I didn't understand what you asked before` is prior-question clarification, not a new campaign pitch.
- bare `no` is ambiguous rejection, not permission to advance the script.
- `missed callbacks happen more often` names a workflow gap, not a callback scheduling request.
- `what do you recommend I choose?` requires diagnosis and agency preservation, not the agent deciding for the buyer.

Hard-coded deterministic routing can patch each symptom, but it scales badly. This checkpoint freezes the cases and creates the structured decision layer that an LLM can later fill, while preserving deterministic guards around the customer-heard response.

## LLM Boundary

The runtime module includes `render_strict_json_reasoner_prompt(...)` and an `llm` mode that requires an explicit provider callable. That mode is default-off.

Baseline validation makes no provider calls, sends no transcript text to a provider, reads no private audio, stores no provider response, and does not require an API key. A later live/provider experiment must choose a provider, record latency/cost/privacy behavior, and compare the same frozen cases before using LLM reasoning in the demo.

`PROD-102 stays closed`.

## Baseline Coverage

The frozen 30-case set covers:

- sales-call opening and greeting
- caller identity recall
- previous-question clarification
- ambiguous negative replies
- callback scheduling and callback-time confirmation
- price, plan, product, workflow, fit, timing, and effort turns
- manual-tracking objections
- selected workflow gaps after price
- topic shifts after price
- repeated price follow-up without loop behavior
- generic qualification follow-up
- ASR fragment repair
- off-topic unclear turns
- recommendation requests with agency preservation
- integration, security, and human-handoff boundaries

## Acceptance

`DIALOGUE-REASONER-001` is accepted only if:

- the frozen case file has exactly 30 cases
- every case passes the structured reasoner expectation
- provider calls remain false
- text sent to provider remains false
- LLM reasoning remains default-off
- live-demo response behavior is not changed by the baseline reasoner run
- `runtime/runtime_manifest.json` lists `runtime/core/dialogue_reasoner.py`
- `LIVE-DEMO-001`, `LIVE-DEMO-002`, `PROD-101`, and the runtime manifest validators still pass separately

## Commands

Run the structured reasoner baseline:

```powershell
python scripts\run_dialogue_reasoner_001_baseline.py
```

Validate the checkpoint:

```powershell
python scripts\validate_dialogue_reasoner_001.py
```
