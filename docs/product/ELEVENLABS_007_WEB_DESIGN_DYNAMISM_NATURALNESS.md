# ELEVENLABS-007 Web Design Dynamism And Naturalness

Package ID: `ELEVENLABS-007-web-design-dynamism-naturalness`

## Decision

Passing the previous tests did not prove naturalness.

`ELEVENLABS-005` was useful for boundary checks, but too weak as a quality
gate. It judged the final response after scripted prior agent turns. That can
pass while the wider call still sounds repetitive, checklist-driven, or
overfitted to exact rubric language.

## Critique

- The old scenarios rewarded inclusion of required details more than natural
  spoken flow.
- Several scripted prior agent turns used phrases we should not train toward,
  including `customer action path`.
- The live agent temperature was `0.0`, which is consistent but too rigid for a
  conversational sales call. A trial at `0.35` improved variation but was too
  unstable on callback/pass-along constraints, so the target is `0.25`.
- The prompt included useful examples but did not clearly say that examples are
  patterns, not scripts.
- The agent should not list menu, hours, location, and reservation calls in
  every answer. It should pick the relevant detail for the buyer's latest
  concern.

## What This Adds

- stronger prompt rules against checklist stuffing, repeated acknowledgements,
  verbatim example copying, and invented price or outcome claims
- a shorter first message
- automation support for `--agent-temperature`
- `runtime/providers/elevenlabs_agents/tests/web_design_mikes_kitchen_naturalness_tests.json`
- `runtime/providers/elevenlabs_agents/manifests/web_design_mikes_kitchen_naturalness_tests.package.json`
- `scripts/validate_elevenlabs_007_web_design_dynamism.py`

## Test Target

The new naturalness tests target folder:

```text
Atlas Web Studio - Naturalness Stress
```

They check eight 8-10 turn situations:

- plain ask after website-pitch suspicion
- busy callback without overexplaining
- free-offer skepticism
- short staff pass-along note
- defensive Google/Instagram objection
- phone-reservation boundary
- price question without invention
- take-off-list stop rule

## Provider Patch

The intended live patch keeps the same agent, KB, and RAG configuration, but
changes:

- prompt naturalness rules
- first message
- dynamic-variable placeholder wording
- LLM temperature `0.25`

## Boundary

- No new KB document is uploaded.
- No private customer data is used.
- No API key value is logged.
- Passing these tests is not proof of real production naturalness; it is a
  stricter dashboard gate before human call review.
- Real customer calls remain blocked.

## Live Result

Run date: 2026-06-04

- Live agent PATCH applied to `agent_7801kt0g32zxf4f8x5zkykj7syty`.
- Read-back confirmed model `gemini-2.5-flash`, temperature `0.25`, prompt
  length `6445`, KB document `OyjSKNJnQTc84pyk1Yu0`, and RAG enabled.
- Created eight naturalness tests in folder
  `Atlas Web Studio - Naturalness Stress`
  (`tfld_5201kt9ygzm2ftrtxq679h0qyw6z`).
- Final naturalness suite `suite_3001kt9zb024empvd0bjqvbchv5e`: `8/8`
  passed.
- Final original scenario suite `suite_3901kt9zb05hee395szz5jrb7g65`: `6/6`
  passed.

Intermediate failure signal was useful:

- At temperature `0.35`, the model was more variable but less reliable on
  callback/pass-along constraints.
- Removing quotable examples fixed checklist-style overexplaining.
- Callback handling needed a hard rule that includes the mockup purpose but
  does not ask another time question after a usable window.
