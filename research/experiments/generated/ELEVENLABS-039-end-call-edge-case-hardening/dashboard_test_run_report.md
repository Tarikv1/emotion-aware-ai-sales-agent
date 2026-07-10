# ELEVENLABS-039 Dashboard Test Run

## Scope

- Agent: `agent_7801kt0g32zxf4f8x5zkykj7syty` (`web design`)
- Surface: authenticated ElevenLabs dashboard browser session
- Tests: exactly the four repo-owned ELEVENLABS-039 simulations
- Models: `gemini-2.5-flash` simulated user and evaluator
- Outbound calls: none
- Procedures: inactive throughout

## Baseline

The first complete batch passed `2/4`. Hard stop and gatekeeper callback passed. Delivery timing was repeated in the terminal message, and the accepted gatekeeper note did not terminate atomically.

## Fixes Tested

- Removed the remaining confirmation-only farewell conflict from the compact prompt and active offer facts.
- Made confirmation without goodbye a timing-only, non-terminal turn.
- Defined same-turn confirmation plus goodbye as one buyer utterance.
- Made the accepted gatekeeper callback and note phrases literal terminal states.
- Clarified that the dashboard-rendered agent line matching `system__message_to_speak` is the tool-bound message, not an additional farewell.

## Final Batch

All four tests passed:

| Test | Run ID | Result | Terminal message |
| --- | --- | --- | --- |
| Hard stop overrides pending email | `trun_6701kx5tnqcjeyhtg6nkcke6f9ha` | Passed | `Got it. Take care.` |
| Delivery timing not repeated | `trun_4801kx5tnqchfv7amx388r1bresw` | Passed | `Take care.` |
| Gatekeeper callback atomic close | `trun_6601kx5tnqckf918cgtr8nr4zyeg` | Passed | `Got it, I'll try then. Take care.` |
| Gatekeeper note atomic close | `trun_4701kx5tnqcmer4rf9kn2whsm08p` | Passed | `Got it, thank you. Take care.` |

The delivery-dedup case also passed three consecutive focused reruns before the final folder batch: `trun_3601kx5tfwnreet8f6eaqkh4t47r`, `trun_2501kx5thy6yee6sbjfrn6zj11jm`, and `trun_8801kx5tm4v7em0aycvbyajd3m63`.

One earlier run, `trun_6501kx5stjqjfpgb6g49mbg43az8`, produced the correct one-tool trace and `Take care.` tool message but was graded as a failure because the evaluator counted the dashboard-rendered tool message as a separate farewell. The test criterion was corrected to match ElevenLabs trace semantics.
