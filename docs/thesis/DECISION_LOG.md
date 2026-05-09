# Decision Log

Record important thesis and implementation decisions here with enough context to justify them later.

## Template

### DEC-XXX - Title

- Date:
- Status: proposed | accepted | changed | dropped
- Decision:
- Why:
- Alternatives considered:
- Consequences:

## Decisions

### DEC-080 - Keep PROD-032 as the interactive trace review gate

- Date: 2026-05-09
- Status: accepted
- Decision: Treat PROD-032 as a review gate that classifies interactive trace findings before static route-gap cleanup, runtime-policy edits, demo polish, provider work, or client-facing promotion.
- Why:
  - PROD-032 reviewed `8` calls and `26` turns from PROD-031 and found `54` trace-level findings across `7` affected calls
  - product grounding remained clean with product grounding issues `0`, hard failures `0`, payment collection count `0`, unsupported claim count `0`, and leakage findings `0`
  - the biggest blocker is simulator terminal-control quality: callback requests converted to sale-ready state `5` times, repeated agent answers appeared `12` times, and repeated customer messages appeared `4` times
  - runtime decision traces still need alignment, but that work should follow a simulator terminal-control fix so later reviews measure real conversational behavior
- Alternatives considered:
  - fix the old static PROD-030 route gaps immediately
  - promote the safe PROD-031 headline metrics as demo-ready evidence
  - tune product facts even though product-grounding issues were `0`
- Consequences:
  - the next checkpoint is `PROD-033-interactive-simulator-termination-fix`
  - static route-gap cleanup remains deferred until callback and terminal loops are cleaned in reactive simulation
  - runtime behavior changes, retrieval defaults, composer-hook defaults, provider work, customer data, payment handling, and production promotion remain blocked

### DEC-079 - Keep PROD-031 as interactive evaluation evidence

- Date: 2026-05-09
- Status: accepted
- Decision: Treat deterministic interactive simulation as the stronger next evaluation lane before static route-gap cleanup or demo polish.
- Why:
  - customer replies now react to the previous agent answer and updated state
  - exact state transitions make trust, clarity, interest, friction, objections, and commitment inspectable
  - local deterministic simulation keeps provider, LLM, privacy, and runtime-promotion boundaries closed
  - PROD-031 ran `8` call seeds, `26` turns, and `18` reactive customer turns with hard failures `0`, payment collection count `0`, unsupported claim count `0`, and leakage findings `0`
- Alternatives considered:
  - fix static route gaps first
  - keep using static full-scenario replay as the primary evidence
  - add LLM customer simulation before deterministic simulation exists
- Consequences:
  - PROD-032 should review interactive traces before choosing runtime fixes
  - old static route gaps remain deferred until they are confirmed relevant in reactive calls
  - live/provider/voice/telephony/client-facing promotion remains blocked

### DEC-078 - Replace the static route-gap fix with interactive simulation

- Date: 2026-05-09
- Status: accepted
- Decision: Replace the planned `PROD-031-grounded-route-gap-fix` with `PROD-031-interactive-grounded-call-simulation`.
- Why:
  - the PROD-027 to PROD-030 scenario lane is multi-turn, but still scripted replay rather than a reactive conversation
  - a sales agent should be tested on how its answer changes customer trust, clarity, interest, objections, patience, and commitment
  - fixing static route gaps first risks optimizing for a weak benchmark instead of realistic conversational behavior
  - Tarik explicitly approved moving PROD-031 to an interactive simulator before route-gap cleanup
- Alternatives considered:
  - continue with the static route-gap fix
  - treat the `13/20` demo-ready static scenarios as enough for demo realism
  - jump to LLM-based customer simulation immediately
- Consequences:
  - PROD-031 should be a deterministic local simulator with customer state transitions after each agent answer
  - the static `10` PROD-030 route gaps are deferred until reactive simulation clarifies whether they still matter
  - provider calls, LLM simulation, voice, telephony, runtime promotion, retrieval defaults, composer-hook defaults, customer data, and payment handling remain blocked

### DEC-077 - Keep PROD-030 as a demo review gate

- Date: 2026-05-09
- Status: accepted
- Decision: Accept the PROD-029 grounded answer layer as a local demo wording candidate, but block full-demo and runtime campaign-profile promotion until the remaining route gaps are fixed.
- Why:
  - PROD-030 accepted `120/120` grounded answers with no revised or rejected answer text
  - safety stayed clean with hard failures `0`, payment collection count `0`, unsupported claim count `0`, and leakage findings `0`
  - route correctness is still not full-demo ready because `10` turns across `7` scenarios need policy or call-control review
  - the remaining misses are concentrated in `unknown-runtime-signal_policy_mismatch`, `autonomy-check_policy_mismatch`, and `scheduling-confirmation_call-control-mismatch`
- Alternatives considered:
  - promote the grounded answer layer directly into the runtime campaign profile
  - show the full `20`-scenario set as demo-ready despite route gaps
  - revise grounded answer text even though all answer text passed review
  - skip route-gap work and move to provider-backed voice or telephony
- Consequences:
  - this was changed by DEC-078; the route-gap fix is deferred behind `PROD-031-interactive-grounded-call-simulation`
  - a local subset of `13` full scenarios can be reviewed as demo-ready evidence
  - the full scenario set remains blocked until route gaps are fixed and rerun
  - provider-backed, voice, telephony, runtime-default, and client-facing promotion remain blocked

### DEC-076 - Keep PROD-029 as a grounded rerun of PROD-027

- Date: 2026-05-09
- Status: accepted
- Decision: Compare old PROD-027 exact answers against PROD-028 grounded campaign answers on the same `20` scenarios and `120` turns, while preserving PROD-027 as the route baseline and keeping route gaps as a separate issue.
- Why:
  - PROD-028 proved that synthetic campaign facts reduce question-only behavior on isolated product questions
  - the next useful test is whether the same fact layer improves full-scenario answers without changing the scenario set or hiding route weaknesses
  - using the exact PROD-027 set keeps the comparison fair and prevents accidental benchmark drift
  - the project still needs to separate answer usefulness from route-policy correctness before runtime promotion
- Alternatives considered:
  - overwrite PROD-027 with grounded answers
  - create a new unrelated scenario set before comparing
  - promote the grounded answers directly into runtime defaults
  - ignore the route gaps because answer quality improved
- Consequences:
  - the next checkpoint should be `PROD-030-grounded-demo-review`
  - grounded answers can be accepted, revised, or rejected for demo review with exact evidence
  - unchanged route gaps remain visible and should be handled as policy work, not hidden by better product wording
  - provider-backed, voice, telephony, runtime-default, and client-facing promotion remain blocked

### DEC-075 - Use a synthetic reality-based product campaign before demo polish

- Date: 2026-05-09
- Status: accepted
- Decision: Use a fictional but reality-patterned B2B CRM campaign as the next product brain before demo polishing, then test whether fact-grounded answers reduce question-only behavior.
- Why:
  - PROD-027 showed the agent can stay safe across full scenarios, but many answers were thin because the runtime had no real product facts to answer with
  - a real company campaign would create copying, licensing, brand, and liability risks before client approval
  - a fully invented product would be less useful because pricing, billing, setup, support, and security questions would not resemble real SaaS buyer concerns
  - PROD-028 uses public CRM/SaaS pages as inspiration only and keeps all campaign facts fictional and project-owned
- Alternatives considered:
  - use a real product/company directly
  - keep the current fact-thin B2B software campaign
  - create a fully arbitrary synthetic product with no reality grounding
  - jump directly to provider-backed voice or demo polish
- Consequences:
  - the next checkpoint should be `PROD-029-grounded-full-scenario-rerun`
  - product and pricing facts can be evaluated locally before runtime promotion
  - real-client, provider-backed, telephony, and payment-related work remain blocked

### DEC-074 - Keep PROD-027 as full-scenario route evaluation

- Date: 2026-05-09
- Status: accepted
- Decision: Keep PROD-027 as full-scenario route evaluation; use it to review route behavior before demo polishing, not to claim production readiness.
- Why:
  - the one-line PROD-026 trace cards were useful for visibility but too thin to judge real sales flow
  - PROD-027 expands the CallCenterEN-derived abstract scenario bank into `20` full scenarios and `120` evaluated customer turns
  - safety stayed clean with `0` hard failures, `0` payment collection findings, and `0` leakage findings
  - route correctness is not perfect: `110/120` turns were route-correct and only `13/20` scenarios passed every route turn
- Alternatives considered:
  - keep reviewing only one-line trace cards
  - jump directly to provider-backed voice/demo work
  - reconstruct source calls from CallCenterEN transcript text
  - hide route misses and show only polished answers
- Consequences:
  - the next checkpoint should be `PROD-028-full-scenario-demo-review`
  - route misses should be reviewed before changing local policy or creating a polished demo surface
  - provider-backed, voice, telephony, and client-facing demo work remain blocked

### DEC-073 - Keep PROD-026 as local trace harness

- Date: 2026-05-09
- Status: accepted
- Decision: Keep PROD-026 as local trace harness; use it for manual demo trace review, not production runtime promotion or live-provider demo work.
- Why:
  - PROD-026 builds directly from the accepted PROD-025 bounded demo readiness packet
  - the harness exposes exact synthetic customer questions, exact agent answers, policy actions, call controls, expected outcomes, source checkpoint, and safety flags
  - it stays static and local-only, with provider calls, LLM use, customer data, payment collection, runtime default changes, retrieval defaults, composer-hook defaults, and server start blocked
  - manual review is still required before any provider-backed, voice, telephony, or client-facing demo step
- Alternatives considered:
  - start a live demo server immediately
  - show only polished answer text without the decision process
  - promote the local trace harness as production readiness
  - skip manual trace review and move directly to voice/provider work
- Consequences:
  - the next checkpoint should be `PROD-027-manual-demo-trace-review`
  - the review should decide whether to keep the three trace cards as-is, revise card selection, or add a separate offline scripted-call simulation
  - provider-backed, voice, telephony, and client-facing demo work remain blocked until the manual trace review is accepted

### DEC-072 - Keep PROD-025 as bounded demo readiness packet

- Date: 2026-05-09
- Status: accepted
- Decision: Keep PROD-025 as bounded demo readiness packet; it authorizes local trace-only demo harness work, not production runtime promotion or live-provider demo work.
- Why:
  - PROD-024 passed the full post-fix live-shaped gate across `7` calls and `19` turns
  - PROD-025 preserves provider-off, customer-data-off, payment-off, retrieval-default-off, and composer-hook-default-off boundaries
  - the packet defines allowed local demo modes, blocked product claims, exact trace visibility, and required manual review gates
  - production-ready autonomous calling and customer-facing live runtime remain blocked claims
- Alternatives considered:
  - build a live provider demo immediately
  - treat the clean post-fix rerun as production readiness
  - move back to dataset expansion before making a local demo surface
  - hide the decision process and show only final answers
- Consequences:
  - the next checkpoint should be `PROD-026-local-demo-trace-harness`
  - the harness must show exact question, answer, policy action, call control, safety flags, and source checkpoint
  - manual trace review remains required before provider-backed, voice, telephony, or client-facing demos

### DEC-071 - Keep PROD-024 as post-fix evidence gate

- Date: 2026-05-09
- Status: accepted
- Decision: Keep PROD-024 as post-fix evidence gate; use it to justify a bounded demo-readiness packet, not production runtime promotion.
- Why:
  - PROD-024 reran the full live-shaped path across `7` calls and `19` turns after the PROD-023 fix
  - policy action correctness, call-control correctness, protected context preservation, non-sale correctness, safe-close correctness, and state reference completeness are all `1.0`
  - hard failures, payment collection findings, and leakage findings are all `0`
  - the legacy PROD-021 gate remains false because it was a hook-gain hypothesis, not the correct post-fix policy gate
  - retrieval and composer hooks remain disabled by default
- Alternatives considered:
  - treat the clean post-fix rerun as production runtime promotion
  - make composer hooks default because the original hook experiment had wording gains
  - move directly to provider/live demo work
  - broaden the scenario bank again before defining the bounded demo surface
- Consequences:
  - the next checkpoint should be `PROD-025-bounded-demo-readiness-packet`
  - bounded demo discussion is allowed
  - production runtime promotion remains blocked
  - provider and client-facing demo behavior still needs a separate manual review gate

### DEC-070 - Keep PROD-023 as local runtime-policy fix

- Date: 2026-05-09
- Status: accepted
- Decision: Keep PROD-023 as local runtime-policy fix; do not treat it as runtime promotion, retrieval promotion, composer-hook promotion, or provider readiness.
- Why:
  - PROD-023 closes the exact `PROD-022` gap packet with `10/10` policy-action misses fixed and `3/3` call-control misses fixed
  - policy action correctness and call-control correctness are both `1.0` after the local fix
  - protected context preservation, non-sale correctness, safe-close correctness, hard failures, payment collection count, and leakage findings stayed clean
  - the new `close-and-log-sale-ready` control is narrow and only logs a campaign-approved verbal next-step commitment
  - composer hooks remain wording-only and opt-in; they still do not own policy action or call-control correctness
- Alternatives considered:
  - promote the runtime immediately after the narrow gap fix
  - rerun only PROD-022 without changing the runtime policy
  - enable retrieval or composer hooks by default because the gap packet is clean
  - move back to voice or dataset expansion before rerunning the full live-shaped evidence path
- Consequences:
  - the next checkpoint should be `PROD-024-live-shaped-post-fix-rerun`
  - retrieval default remains off
  - composer hooks remain opt-in
  - no provider, live demo, or customer-facing claim should rely on PROD-023 alone

### DEC-069 - Keep PROD-021 hooks opt-in after review

- Date: 2026-05-09
- Status: accepted
- Decision: keep the `PROD-020`/`PROD-021` composer hooks as opt-in only after the PROD-022 review packet; fix runtime policy routing and call-control before any bounded demo or default-runtime discussion
- Why:
  - PROD-022 extracted the exact `PROD-021` gap turns instead of treating the failed gate as a generic failure
  - all `10` gap turns were policy action misses, and `3` were also call-control misses
  - the gap packet found `0` protected-context gaps, `0` hard failures, and `0` leakage findings
  - the four hook-gain turns remain useful wording evidence, but hooks do not own policy action or call-control correctness
  - the narrow fix targets are `runtime_policy_router_specialization`, `sale_ready_call_control_detector`, and `procurement_review_continuation_guard`
- Alternatives considered:
  - discard hooks because the PROD-021 gate stayed closed
  - promote hooks because four turns improved
  - broaden scenario generation before fixing the exact runtime-policy gaps
  - move to live or provider testing before policy and call-control are correct
- Consequences:
  - the next checkpoint should be `PROD-023-runtime-policy-call-control-fix`
  - retrieval and composer hooks remain disabled by default
  - runtime promotion stays blocked until a rerun closes policy-action and call-control gaps without safety regressions

### DEC-068 - Keep PROD-021 hooks opt-in and revise runtime policy first

- Date: 2026-05-09
- Status: accepted
- Decision: keep the `PROD-020` runtime composer hooks as an opt-in candidate only; do not promote retrieval or composer hooks by default; revise live-shaped runtime policy and call-control gaps before any bounded demo integration
- Why:
  - PROD-021 tested `7` synthetic live-shaped calls and `19` customer turns against the `PROD-011` hardened dialogue-policy expectations
  - opt-in hooks still improved wording on `4` turns, with opt-in total score `112` versus retrieval-only score `98`
  - safety stayed clean: hard failure rate `0.0`, payment collection count `0`, leakage finding count `0`, protected context preservation `1.0`, non-sale correctness `1.0`, safe-close correctness `1.0`, and state reference completeness `1.0`
  - the gate did not pass because policy action correctness was `0.4737` and call-control correctness was `0.8421`
  - the remaining issue is stateful runtime-policy coverage, not evidence that hooks should become default
- Alternatives considered:
  - promote the hooks because the opt-in score still beat retrieval-only
  - discard hooks because the live-shaped gate did not pass
  - move directly to a provider/live-call test despite policy-action and call-control misses
  - broaden the dataset bank before closing the policy gap
- Consequences:
  - retrieval and composer hooks remain explicit opt-in only
  - the next product artifact should be a compact PROD-021 review/gap packet with exact turn traces
  - any follow-up implementation should target policy-action and call-control coverage before new voice, provider, or dataset expansion work

### DEC-067 - Keep PROD-020 naturalized runtime hooks opt-in

- Date: 2026-05-09
- Status: accepted
- Decision: keep the naturalized customer-turn runtime composer hooks as an explicit opt-in candidate only; retrieval and composer hooks remain disabled by default
- Why:
  - PROD-020 reran the actual guarded composer over naturalized customer turns instead of rubric-like prompts
  - `120` source turns were rubric-like, `123` questions were changed, and the naturalized runtime prompts had `0` rubric-token findings
  - source-pattern refs and expected outcomes were preserved for `180/180` rows as metadata, not composer input
  - with retrieval and composer hooks explicitly enabled, `107` answers received hooks without passing evaluation labels into the composer
  - hooked total score was `1065` versus baseline score `734`, with `107` hooked wins, `0` baseline wins, and `73` ties
  - safety stayed clean: hard failures `0`, leakage findings `0`, payment collection findings `0`, expected outcome correctness `180/180`, non-sale correctness `1.0`, safe-close correctness `1.0`, and provider calls `false`
- Alternatives considered:
  - promote retrieval or composer hooks by default after the naturalized score gain
  - treat PROD-019 as enough and skip naturalized prompt evidence
  - change runtime hooks during the naturalization test instead of keeping runtime behavior fixed
  - move directly to provider/live-call testing before live-shaped local simulation
- Consequences:
  - `--composer-hooks-enabled` remains explicit opt-in and still requires guarded retrieval advisory hints
  - naturalized single-turn evidence can support the next local simulation gate, but not default promotion
  - the next product checkpoint should test live-shaped multi-turn behavior against the PROD-011 hardened dialogue policy

### DEC-066 - Keep PROD-019 runtime composer hooks opt-in

- Date: 2026-05-09
- Status: accepted
- Decision: keep the guarded runtime composer hooks as an explicit opt-in candidate behind `--composer-hooks-enabled`, with retrieval and composer hooks disabled by default
- Why:
  - PROD-019 ran through the actual `generate_guarded_response.py` composer rather than the offline PROD-018 substitution path
  - default-off answer drift was `0`, so the existing guarded response path stayed unchanged
  - with retrieval and composer hooks explicitly enabled, `98` answers received runtime hooks without passing evaluation labels into the composer
  - hooked total score was `916` versus current retrieval score `663`, with `92` hooked wins, `0` current wins, and `88` ties
  - safety stayed clean: hard failures `0`, leakage findings `0`, payment collection findings `0`, non-sale correctness `1.0`, safe-close correctness `1.0`, and provider calls `false`
  - the evidence still uses generated rubric-like customer turns, so it is not enough for default retrieval or production promotion
- Alternatives considered:
  - promote the runtime hooks as default because the score improved
  - keep only PROD-018 offline hooks and avoid touching the real composer
  - require the runtime hooks to match every PROD-018 label-aware gain
  - move straight to live/provider tests before naturalizing the customer turns
- Consequences:
  - `--composer-hooks-enabled` remains explicit opt-in and requires guarded retrieval to provide advisory hints
  - PROD-017 specificity scoring remains the promotion gate
  - default runtime retrieval and default composer hooks remain disabled
  - the next evidence checkpoint should test naturalized customer wording or live-shaped simulation before any broader runtime claim

### DEC-065 - Keep PROD-018 composer hooks as a runtime candidate only

- Date: 2026-05-09
- Status: accepted
- Decision: keep the `PROD-018` composer-hook layer as evidence for a guarded runtime-composer candidate test, not as a default retrieval or production-runtime promotion
- Why:
  - PROD-018 used unchanged `PROD-015` rows and changed only an offline composer-hook surface
  - hooked total score was `1421` versus current retrieval score `663` and old runtime score `652`
  - hooked answers won `174` turns versus current retrieval and `177` turns versus old runtime, while old runtime won `0`
  - safety stayed clean: hard failures `0`, leakage findings `0`, payment collection findings `0`, non-sale correctness `1.0`, safe-close correctness `1.0`, and runtime behavior changed `false`
  - the evidence is still label-aware and offline, so it cannot prove the actual runtime composer will make the same decisions in live-shaped turns
- Alternatives considered:
  - promote retrieval by default after the large score gain
  - treat PROD-018 as final product evidence instead of an offline candidate gate
  - skip runtime-composer tests and move directly to naturalized prompt variants
  - discard the hook idea because PROD-015 showed no original quality gain
- Consequences:
  - `PROD-019` should implement a red-first guarded runtime-composer candidate behind an explicit opt-in flag
  - PROD-017 specificity scoring remains the promotion gate
  - retrieval remains disabled by default
  - CallCenterEN-derived raw or transcript-like text remains blocked from commercial runtime prompts

### DEC-064 - Use PROD-017 as the gate for composer-hook experiments

- Date: 2026-05-09
- Status: accepted
- Decision: use the `PROD-017` specificity and objection-fit scorer as the evaluation gate for the next narrow retrieval composer-hook test, while still keeping retrieval disabled by default
- Why:
  - PROD-017 re-scored the same fixed `PROD-015` rows without changing prompts, answers, runtime behavior, or retrieval
  - the new scorer found `3` retrieval wins, `0` old-runtime wins, and `177` ties where PROD-015 had `180` ties
  - all `3` changed retrieval answers won under specificity scoring, confirming the earlier scoring blind spot
  - the result remains small: only `3/180` answers changed, absolute quality gap count is `177`, and generic-answer rates remain high
- Alternatives considered:
  - claim retrieval is better based on the `11` point specificity-score delta
  - change composer hooks before stabilizing the evaluator
  - run the full `240` scenario bank before fixing the generic-answer problem
  - discard retrieval because the improvement only appears on the changed answers
- Consequences:
  - `PROD-018` should be a narrow composer-hook experiment on fixed no-gain examples, not a runtime promotion
  - the pass condition should include higher PROD-017 specificity/objection-fit score plus unchanged hard-failure, non-sale, safe-close, and leakage boundaries
  - broad retrieval claims remain blocked until more answers improve under fixed-case scoring

### DEC-063 - Fix retrieval evaluation before changing runtime retrieval

- Date: 2026-05-09
- Status: accepted
- Decision: after `PROD-016`, improve evaluation specificity and objection-fit scoring before adding retrieval composer hooks or promoting retrieval runtime behavior
- Why:
  - `PROD-016` found retrieval matching was not the main bottleneck: matching success was `1.0` and no-match rate was `0.0`
  - the main high-severity blockers were composer influence gap (`174` retrieved-not-used turns and `177` unchanged answers) and scoring blind spot (`3` influenced answers still tied)
  - the current scorer rewards safe generic follow-up behavior, so it cannot reliably distinguish safe-specific retrieval answers from safe-generic old answers
  - classifier and evaluation-shape issues also exist: `180/180` turns were classified as unknown-runtime-signal, `120` prompts were rubric-like, and `8` domains were run through one B2B software campaign
- Alternatives considered:
  - add retrieval composer hooks immediately
  - run the full `240` scenario bank with the current scorer
  - promote retrieval because matching and safety passed
  - discard retrieval entirely because PROD-015 showed no score gain
- Consequences:
  - `PROD-017` should be an evaluation-only scoring refinement over the same fixed PROD-015 rows
  - retrieval stays disabled by default
  - composer changes should wait until the evaluator can reward answer specificity and objection fit
  - full-bank runs should wait until the diagnostic scoring blind spot is addressed

### DEC-062 - Treat PROD-015 as safe no-gain retrieval evidence

- Date: 2026-05-09
- Status: accepted
- Decision: keep retrieval disabled by default after `PROD-015` because the larger CallCenterEN-derived scenario slice showed safety but no quality gain over the old runtime
- Why:
  - the default `PROD-015` run evaluated the same `60` scenario / `180` turn stratified slice with both old runtime and retrieval runtime
  - retrieval and old runtime tied on all `180` turns under the current scorer, with total score `810` versus `810`
  - retrieval influenced only `3` responses and was retrieved-but-not-used `174` times, so the current retrieval composition path is not yet materially changing enough answers
  - hard failures, leakage findings, unsafe non-sale handling, and unsafe close behavior stayed at `0`, so the problem is usefulness rather than safety
- Alternatives considered:
  - promote retrieval because earlier smaller tests showed wins
  - ignore the no-gain slice and move straight to default runtime retrieval
  - rerun only hand-picked retrieval-friendly prompts
  - run the full `240`-scenario bank before diagnosing why retrieval rarely influences answers
- Consequences:
  - `PROD-015` becomes honest negative or neutral evidence, not promotion evidence
  - the next product step should diagnose retrieval query/composition/scoring or run a full-bank baseline before any retrieval-default claim
  - non-sale correctness and hard failure rate remain hard gates
  - commercial runtime prompts still must not receive CallCenterEN-derived source text

### DEC-061 - Generate scenarios from abstract multi-pattern recipes only

- Date: 2026-05-09
- Status: accepted
- Decision: use `PROD-014` to generate CallCenterEN-derived scenario packets only from abstract multi-pattern recipes, never from one transcript, copied transcript wording, transcript-derived runtime prompt text, company-specific wording, names, or long call summaries
- Why:
  - Tarik wants realistic call openings, intents, objections, emotion shifts, discovery, close attempts, and support boundaries grounded in the downloaded CallCenterEN corpus
  - `PROD-013` already gives enough abstract structure to build scenarios without copying source wording
  - the next old-runtime versus retrieval-runtime comparison needs exact synthetic customer prompts plus expected answer requirements, not raw calls
  - leakage controls need to be part of the generation artifact, not a later manual concern
- Alternatives considered:
  - continue using only the smaller hand-written PROD-012 scenario set
  - generate scenarios from one source call at a time
  - feed transcript-like text into commercial runtime prompts
  - promote retrieval before building a larger scenario bank
- Consequences:
  - each scenario cites at least five abstract pattern IDs across multiple pattern categories
  - safe close remains verbal commitment or sale-ready outcome without payment collection
  - support, cancellation, trust repair, and other non-sale boundaries remain first-class outcomes
  - the 2026-05-09 run produced `240` scenarios, `720` customer turns, `240` unique scenario recipes, and `0` leakage findings after a transient `5,000` sentence source scan
  - `PROD-014` changes no runtime behavior; `PROD-015` should use the bank to compare old runtime and opt-in retrieval on the same prompts

### DEC-060 - Extract CallCenterEN as abstract pattern banks only

- Date: 2026-05-09
- Status: accepted
- Decision: use `PROD-013` to extract abstract pattern banks from approved local CallCenterEN files, covering openings, intents, objections, emotion transitions, persuasion tactics, discovery questions, stages, close attempts, safety boundaries, timing signals, domain patterns, personas, scenario templates, and agent mistakes without storing exact scripts
- Why:
  - Tarik wants scenarios grounded in real call behavior instead of only hand-written synthetic patterns
  - the useful learning is structural: what customers say, how emotions shift, which tactics work, what fails, and when to stop or escalate
  - exact transcript wording, company names, agent/customer names, and long call summaries create leakage and licensing risk
  - the dataset is observed as `cc-by-nc-4.0`, so extraction must stay research-local and abstract until separate license clearance exists
- Alternatives considered:
  - copy real call text into scenarios or prompts
  - store long call summaries as training material
  - extract only objections and ignore openings, discovery, close attempts, timing, and agent mistakes
  - download and process the dataset automatically without an explicit local import step
- Consequences:
  - `PROD-013` produces `pattern-bank.json` and `report.md` from local ignored files
  - default runs do not download the dataset and do not call providers
  - after explicit approval, the full local bounded extraction scanned `95,946` source JSON payloads, parsed `95,934` conversations, produced `4,313,595` pseudo-turns, and kept high-volume sample records capped while aggregate counts covered the full scan
  - many source files provide word-level timestamps without reliable speaker labels, so speaker-role assignment is treated as inference for pattern mining only, not ground-truth diarization; the extractor uses role-specific sales/customer language signals before file-direction fallback
  - later scenario-generation checkpoints can consume abstract pattern labels instead of hand-written seed patterns
  - commercial runtime use remains blocked until leakage, license, and runtime-promotion gates are separately cleared

### DEC-059 - Keep CallCenterEN as pattern-grounding evidence, not commercial runtime data

- Date: 2026-05-09
- Status: accepted
- Decision: use `PROD-012` to evaluate CallCenterEN-grounded synthetic scenarios against old core and opt-in RAG-018 retrieval, while keeping the dataset out of commercial runtime prompts, training data, and default runtime retrieval
- Why:
  - Tarik wanted real-world call-center scripts to ground scenarios instead of fully synthetic examples
  - the dataset is observed as `cc-by-nc-4.0`, so it should not become commercial runtime training or prompt material without separate license clearance
  - leakage protections must be first-class metrics, not a note after the fact
  - retrieval should prove value on fixed scenarios before any broader runtime promotion
- Alternatives considered:
  - copy transcript sentences into generated scenarios
  - generate scenarios from one transcript at a time
  - put transcript-derived text into commercial runtime prompts
  - make retrieval default because it beat the old core on the fixed scenario set
- Consequences:
  - PROD-012 adds hard failure rate, non-sale correctness, leakage failure rate, scenario quality, sales/emotional handling score, and retrieval win rate in one local checkpoint
  - default runs require no dataset download and no provider call
  - ignored local ZIPs can be scanned transiently for leakage if Tarik later approves/downloads them into `data/external/callcenteren/raw/`
  - the decision remains `keep_retrieval_opt_in_for_callcenteren_grounded_scenarios`, not default retrieval

### DEC-058 - Keep dialogue-policy hardening as design evidence before runtime promotion

- Date: 2026-05-09
- Status: accepted
- Decision: use `PROD-011` as a local dialogue-policy hardening checkpoint over PROD-010 packet evidence, not as a live runtime promotion
- Why:
  - PROD-010 proved objection-state continuity, but policy-action selection still needed its own measurable gate
  - multi-turn sales safety depends on choosing the right action before drafting persuasive language
  - premature closes, unsafe reassurance, support-to-sales drift, and refusal pressure should be blocked at policy level
  - retrieval and providers should remain disabled until separate gates explicitly enable them
- Alternatives considered:
  - promote PROD-010 packet evidence directly into runtime behavior
  - test full transcript responses before policy actions were measurable
  - make RAG default for hard objections before the local policy can route them safely
  - focus on more voice variants before the sales decision layer is stable
- Consequences:
  - policy action correctness, blocked action avoidance, objection stack preservation, and state-reference completeness are now first-class metrics
  - the next gate should be live-shaped transcript or simulation behavior against the hardened policy
  - no provider call, private data read, dataset download, payment handling, checkout handling, commercial runtime prompt contamination, or live runtime change occurs
  - PROD-011 guides runtime design without changing runtime behavior

### DEC-057 - Require long-call objection continuity before dialogue-policy hardening

- Date: 2026-05-09
- Status: accepted
- Decision: use `PROD-010` as the long-call universal-objection gate before hardening the dialogue policy for multi-turn objection handling
- Why:
  - PROD-009 proved cross-domain packet generation on shorter calls, but not objection persistence across longer conversations
  - full-sale behavior is unsafe if repeated price, authority, privacy, support, anger, or technical-risk objections are collapsed into a close
  - the BRAIN-002 packet must carry turn position, total turn count, and objection stack so downstream policy work can reason over the call, not only the latest turn
  - retrieval and providers should remain disabled until separate gates explicitly enable them
- Alternatives considered:
  - jump directly from PROD-009 into live-runtime-shaped transcript tests
  - harden dialogue policy without first proving objection-state continuity
  - make RAG default for objections before the generated state packet handles them locally
  - focus on voice personality before the sales decision layer is stable on longer calls
- Consequences:
  - long-call state continuity and objection boundary correctness are now first-class metrics
  - dialogue-policy hardening can build on packet evidence instead of only final-response text
  - no provider call, private data read, dataset download, payment handling, checkout handling, commercial runtime prompt contamination, or live runtime change occurs
  - the next gate is dialogue-policy hardening, not production promotion

### DEC-056 - Require cross-domain generated packet evidence before harder objections

- Date: 2026-05-09
- Status: accepted
- Decision: use `PROD-009` as the first cross-domain generated BRAIN-002 gauntlet before moving into harder universal objections and longer calls
- Why:
  - PROD-008 proved generated packets only on the first SD-card/storage-shaped call set
  - the project should not mistake a narrow fixture win for domain-general behavior
  - source-pattern grounding and leakage boundaries need to remain active while the domain set expands
  - retrieval and providers should remain disabled until separate gates explicitly enable them
- Alternatives considered:
  - jump directly from PROD-008 into runtime promotion
  - add RAG by default before cross-domain packet stability
  - expand with generated text only and skip packet-completeness scoring
  - test more voices before the sales decision layer is robust across domains
- Consequences:
  - cross-domain coverage is now part of the evidence chain before harder objection work
  - every broader call still needs at least three source-pattern IDs and no copied transcript text
  - no provider call, private data read, dataset download, payment handling, checkout handling, commercial runtime prompt contamination, or live runtime change occurs
  - the next gate is harder universal objections and longer calls, not production promotion

### DEC-055 - Require generated BRAIN-002 packets before broader gauntlet expansion

- Date: 2026-05-09
- Status: accepted
- Decision: use `PROD-008` as the bridge from fixture-scored BRAIN-002 packet evidence to generated turn-by-turn packet evidence before expanding the full-call gauntlet across domains
- Why:
  - PROD-007 showed a useful fixture-level win but still embedded the expected state packet answer in the case file
  - the project-wide premortem risk is still evaluation theater if the runtime cannot produce the packet fields itself
  - broader scenario coverage should only happen after packet completeness, non-sale correctness, and hard-failure targets survive generated packet construction
  - retrieval and providers should remain disabled until separate gates explicitly enable them
- Alternatives considered:
  - expand domains immediately from PROD-007
  - treat fixture-scored packets as enough proof for runtime behavior
  - make retrieval default before generated packet scoring is stable
  - run live/provider calls before the local generated-packet contract is validated
- Consequences:
  - PROD-008 becomes the required handoff from state-schema design to broader full-call evaluation
  - generated packet completeness is now a first-class metric
  - no provider call, private data read, dataset download, payment handling, checkout handling, or live runtime change occurs
  - the next gate is broader generated full-call coverage, not production promotion

### DEC-054 - Keep PROD-007 as fixture evidence, not runtime promotion

- Date: 2026-05-09
- Status: accepted
- Decision: use `PROD-007` as the first fixed full-call gauntlet comparing the old core against the BRAIN-002/full-sale candidate, but do not promote the candidate to live runtime from fixture-scored evidence alone
- Why:
  - the project-wide premortem identified evaluation theater as a risk
  - BRAIN-002 needs call-level scoring before broader runtime changes
  - the first gauntlet should test the decision contract under fixed cases before connecting it to generated runtime packets
  - safe close rate is only meaningful if hard failure rate stays `0.0` and non-sale correctness stays strong
- Alternatives considered:
  - move directly to live/provider testing
  - treat the BRAIN-002 schema as enough evidence without a call-level gauntlet
  - optimize close rate before testing support, escalation, refusal, and unclear-fit cases
  - make RAG default before proving full-sale call-control behavior
- Consequences:
  - PROD-007 reports a fixture-level BRAIN-002 candidate win, not a production-readiness claim
  - retrieval remains disabled by default
  - no provider call, private data read, dataset download, payment handling, checkout handling, or live runtime change occurs
  - the next gate is a generated full-call packet test where runtime logic creates BRAIN-002 fields from turns

### DEC-053 - Make BRAIN-002 the runtime state contract before the full-call gauntlet

- Date: 2026-05-09
- Status: accepted
- Decision: define `BRAIN-002` as the per-turn runtime state schema before implementing the full-call old-core-versus-full-sale comparison
- Why:
  - the project-wide premortem identified convergence risk as the most likely failure mode
  - final response text alone is not enough to evaluate a sales agent
  - safe full-sale behavior needs explicit `sale_ready`, `non_sale_correct`, safety, call-control, retrieval, voice, and evidence-log fields
  - retrieval must remain disabled by default until a separate RAG-017/RAG-018 promotion path
  - voice should carry delivery metadata only, not choose sales strategy or infer hidden emotion
- Alternatives considered:
  - build the full-call gauntlet directly without a shared state schema
  - keep using the older output contract as the only runtime packet
  - make RAG or voice the next primary implementation focus
  - optimize close rate before making non-sale correctness first-class
- Consequences:
  - full-sale simulations can now score structured state decisions, not only wording quality
  - `close-and-log-sale-ready` is the explicit full-sale call-control value
  - non-sale correctness is a required output for support, escalation, refusal, unclear fit, and trust-repair cases
  - BRAIN-002 changes no live runtime behavior by itself
  - the next implementation target is the fixed full-call gauntlet

### DEC-052 - Use CallCenterEN only for pattern-grounded full-sale scenarios

- Date: 2026-05-08
- Status: accepted
- Decision: use the Hugging Face `AIxBlock/92k-real-world-call-center-scripts-english` / CallCenterEN dataset only as a pattern-grounding source for the full-sale MVP scenario bank, not as copied script text, commercial runtime prompt text, or commercial model-training data
- Why:
  - Tarik wants scenarios grounded in real call-center conversations rather than fully synthetic scripts
  - the dataset is useful for domains, call directions, objections, escalation, support-only patterns, and close resistance
  - the observed license is `cc-by-nc-4.0`, and the dataset/paper frame use as non-commercial research
  - copied transcript text or close paraphrases would weaken both license safety and thesis defensibility
  - the first full-sale MVP needs explicit sub-metrics: hard failure rate and non-sale correctness, not only close rate
- Alternatives considered:
  - keep scenarios completely synthetic
  - use direct transcript excerpts as evaluation cases
  - train or fine-tune a commercial runtime model on the dataset
  - generate scenarios from one source transcript at a time
- Consequences:
  - PROD-006 uses project-owned scenario rewrites and multi-source pattern grounding
  - every generated scenario must use at least three source patterns
  - leakage tests become hard gates: no exact transcript sentence, no high-similarity paraphrase, no single-source scenario, and no transcript-derived commercial runtime prompt
  - dataset ZIP downloads remain explicit-approval, ignored local-only inputs
  - safe close rate cannot be optimized unless hard failure rate remains zero and non-sale correctness stays strong

### DEC-051 - Keep RESP-007 as a pacing-only German follow-up

- Date: 2026-05-08
- Status: accepted
- Decision: implement RESP-007 as a same-question, same-answer-content German pacing-stability checkpoint and keep the voice-personality selector blocked until human listening review
- Why:
  - RESP-006 found pacing instability, not a need to change voice identity or sales strategy
  - changing the question, answer, campaign, or strategy would make the listening result hard to interpret
  - `old_plain_guarded` needs an opening rush guard and late-drag prevention
  - `new_shaped_runtime` needs a late speed cap and later answer spacing
  - provider calls and quality claims still require explicit opt-in and listening evidence
- Alternatives considered:
  - promote the English RESP-005 personalities immediately despite the German pacing issue
  - rewrite the German answer to sound more natural
  - change voice identity or provider settings broadly
  - make BRAIN-002 or RAG promotion the next active checkpoint before resolving the current voice blocker
- Consequences:
  - RESP-007 changes only provider-facing break tags and bounded speed settings
  - the German answer content remains fixed after delivery tags are stripped
  - no provider call, private audio read, transcription, voice cloning, or customer audio upload occurs by default
  - the next user-facing step is to listen to RESP-007 audio and record a human decision before the voice-personality selector

### DEC-050 - Define the project brain as a bounded runtime architecture

- Date: 2026-05-08
- Status: accepted
- Decision: define the project brain through `BRAIN-001` as a compact runtime decision architecture instead of a single giant prompt, hidden memory dump, or slow multi-agent chain
- Why:
  - recent RAG and voice work created useful knowledge, but not all of it is ready for default runtime use
  - the live call path must stay low-latency and campaign-grounded
  - buyer emotion should guide repair and strategy cautiously, not become hidden-state persuasion
  - RAG-020 and RAG-021 are still advisory-only until a separate RAG-017/RAG-018 promotion path
  - the voice-personality selector remains blocked until the German pacing-stability follow-up resolves the RESP-006 issue
- Alternatives considered:
  - merge all RAG and voice notes into one large system prompt
  - make retrieval default after the retrieval-vs-core simulation
  - treat the accepted English voice personalities as ready for all languages
  - put private/raw call memory directly into the runtime brain
- Consequences:
  - the always-on brain remains the reusable sales-agent core, `SalesCampaign`, short-term call state, conservative buyer-state estimate, strategy selector, safety checks, and voice delivery profile
  - optional retrieval remains explicitly gated and disabled by default
  - raw private audio, raw private transcripts, identifiers, copied source excerpts, and provider secrets are excluded
  - `BRAIN-002` can later define a strict runtime state schema without changing these boundaries

### DEC-049 - Revise German pacing before voice-personality selector

- Date: 2026-05-08
- Status: accepted
- Decision: do not promote RESP-006 German variants into the voice-personality selector yet; run a narrow German pacing-stability revision first
- Why:
  - Tarik's German listening review found the old variant starts a bit fast and then becomes a bit slow
  - Tarik's German listening review found the new variant starts strong but becomes a bit too fast later
  - the issue is pacing stability rather than a need to change voice identity or broaden personality design
  - the English RESP-005 personality decision should not be generalized to German until German pacing is stable
- Alternatives considered:
  - accept both German variants as direct equivalents of the English personality lanes
  - choose the newer shaped runtime because it starts stronger
  - choose the older plain runtime because it avoids the later fast shaped-runtime section
- Consequences:
  - the next checkpoint should keep the RESP-006 German question/content fixed and change only pacing-related delivery surfaces
  - the voice-personality selector remains blocked until the German pacing follow-up is reviewed
  - no production-wide claim is made for either German style across all campaigns, providers, voice IDs, or real leads

### DEC-048 - Treat RESP-005 variants as accepted voice personalities

- Date: 2026-05-08
- Status: accepted
- Decision: keep both `old_plain_guarded` and `new_shaped_runtime` as accepted voice personality directions instead of selecting a single universal winner
- Why:
  - Tarik's listening review found both versions strong
  - `old_plain_guarded` feels like a real laid-back salesperson
  - `new_shaped_runtime` feels more serious and lower-energy
  - the useful difference is now listener and campaign preference, not a clear quality failure in either path
  - the comparison reframes voice work as selectable personality design rather than endless polishing toward one generic voice
- Alternatives considered:
  - promote only the old plain runtime because it sounded more like a relaxed salesperson
  - promote only the newer shaped runtime because it carries the latest provider-facing delivery polish
  - continue tuning both until one becomes objectively better
- Consequences:
  - the next voice/runtime checkpoint should define bounded style or personality profiles
  - future listening checks should evaluate campaign fit, listener preference, and safety instead of only asking which version is better
  - no production-wide claim is made for either voice across all campaigns, providers, voice IDs, or real leads

### DEC-047 - Keep RAG-018 retrieval opt-in after retrieval-vs-core call simulation

- Date: 2026-05-08
- Status: accepted
- Decision: keep RAG-018 retrieval opt-in for the four validated objection paths, but do not make retrieval the default response path yet
- Why:
  - the fixed retrieval-vs-core call simulation compared the older retrieval-disabled core path against opt-in retrieval across `4` synthetic calls and `12` turns
  - retrieval won `4` turns, the older core won `0`, and `8` turns tied
  - retrieval total score was `12` versus core total score `4`, for a `+8` delta on the fixed scoring rubric
  - protected turns were preserved `6/6`, and the run used no provider calls, private customer data, vector database, embedding provider, or LLM reranker
- Alternatives considered:
  - make retrieval default immediately after winning the scripted comparison
  - keep the older core path for all turns until a live provider or human review is available
  - expand retrieval to additional unvalidated objection categories
- Consequences:
  - retrieval is better than the older core path on the currently validated synthetic objection turns
  - the default runtime path remains retrieval-disabled unless explicitly enabled
  - making retrieval default still needs a larger call-outcome simulation or human review focused on appointment-setting quality and pressure risk

### DEC-046 - Accept authority and trust as narrow RAG-018 opt-in influence paths

- Date: 2026-05-08
- Status: accepted
- Decision: keep guarded runtime retrieval opt-in, but allow safe English authority/boss and trust turns to use retrieved objection guidance for one low-pressure clarifying question
- Why:
  - `RAG-018-SIM-C04` and `RAG-018-SIM-C05` failed the red test as retrieved-but-unused quality gaps
  - the authority response offers a shareable boss summary or one concern to address first
  - the trust response asks which proof-oriented information would be useful first without inventing claims or social proof
  - the scripted simulation now reports `4` retrieval-influenced responses, `4` objection-resolution improvements, `4` next-step quality improvements, and `4/4` protected contexts preserved
- Alternatives considered:
  - leave authority and trust as known gaps
  - broaden all unknown objections into RAG-shaped wording
  - make retrieval default after closing the scripted gaps
- Consequences:
  - price objection, send-me-info, authority/boss, and trust are the only validated influence paths
  - retrieval remains disabled by default and requires explicit `--retrieval-enabled`
  - default retrieval still needs broader multi-turn evidence, not just scripted single-turn success

### DEC-045 - Accept RAG-018 send-me-info as the second opt-in influence path

- Date: 2026-05-08
- Status: accepted
- Decision: keep guarded runtime retrieval opt-in, but allow a safe English send-me-info turn to use retrieved send-info/qualification hints for one clarifying question before sending follow-up information
- Why:
  - `RAG-018-SIM-C03` failed the new red test as a retrieved-but-unused quality gap
  - the implemented response asks what information would be relevant instead of inventing product claims or forcing a meeting
  - the scripted simulation now reports `2` retrieval-influenced responses, `2` objection-resolution improvements, `2` next-step quality improvements, and `4/4` protected contexts preserved
  - retrieval remains disabled by default and campaign facts still override RAG
- Alternatives considered:
  - leave send-me-info as a known quality gap
  - add broader generic unknown-objection rewriting
  - make all RAG-019 objection hints change runtime wording
- Consequences:
  - price objection and send-me-info are the only validated influence paths
  - authority/boss and trust objections remain retrieved-but-unused quality gaps
  - each further expansion still needs its own failing scripted-call expectation first

### DEC-044 - Keep RAG-018 opt-in after broader scripted-call simulation

- Date: 2026-05-08
- Status: accepted
- Decision: keep guarded runtime retrieval opt-in and do not make it default after the 10-case RAG-018 scripted-call simulation
- Why:
  - the simulation preserved `10/10` safe cases and `4/4` protected contexts
  - only the German price-objection case improved objection resolution and next-step quality
  - send-me-info, authority, and trust objections retrieved useful hints but did not yet change runtime wording
  - default retrieval would add complexity before broader measurable improvement exists
- Alternatives considered:
  - make retrieval default after the first safe influence path
  - expand all retrieved response-wording hints into runtime wording immediately
  - return to metadata-only retrieval and remove the first influence path
- Consequences:
  - RAG-018 remains live-capable only behind explicit `--retrieval-enabled`
  - the current validated influence path stays narrow
  - the next expansion should target one remaining quality gap with a failing test first

### DEC-043 - Keep RAG-018 opt-in while allowing one validated safe influence path

- Date: 2026-05-08
- Status: accepted
- Decision: keep guarded runtime retrieval disabled by default, but allow opt-in RAG-018 hints to influence the German price-objection composer when the response remains non-protected, validated, and different from the no-retrieval core-playbook baseline
- Why:
  - the previous RAG-018 path proved safe retrieval but produced zero runtime influence
  - the first influence should be narrow enough to inspect and validate directly
  - objection-diagnosis and autonomy hints can improve a clarifying question without adding product claims, urgency, or hidden-emotion inference
  - the runtime still needs stronger evidence before any default retrieval decision
- Alternatives considered:
  - keep retrieval as metadata-only until a larger simulation exists
  - let all retrieved response-wording hints freely rewrite candidate responses
  - make retrieval default for safe cases after the first successful A/B run
- Consequences:
  - `retrieval_used_in_runtime=true` is now expected for the validated safe German price-objection case only
  - blocked/protected contexts still return `retrieval_used_in_runtime=false`
  - the next gate is a larger scripted call simulation with scored objection resolution and next-step quality

### DEC-042 - Keep the VOICE-044 listening check separate as RESP-004

- Date: 2026-05-08
- Status: accepted
- Decision: create RESP-004 for the VOICE-044 polished-baseline listening check instead of overwriting or repurposing RESP-003
- Why:
  - RESP-003 is already the runtime live-capable TTS bridge and has its own evidence trail
  - the VOICE-044 follow-up answers a new test question: whether the polished baseline should be heard before returning to RAG-018
  - keeping a separate checkpoint prevents confusion between core TTS capability and a specific listening-review experiment
- Alternatives considered:
  - append the new test to RESP-003 artifacts
  - rename the existing RESP-003 A/B harness
  - skip the listening-check harness and move directly to RAG-018
- Consequences:
  - RESP-004 owns the VOICE-044 listening-check runner, validator, product doc, and generated artifact folder
  - RESP-003 remains the TTS bridge used by RESP-004 under the hood
  - live RESP-004 runs still require explicit provider approval and human listening review before any quality claim

### DEC-041 - Improve accepted baseline voice with narrow provider-facing polish

- Date: 2026-05-08
- Status: accepted
- Decision: add VOICE-044 after VOICE-043 to polish the accepted baseline shaped runtime directly, without promoting VOICE-041 private-pattern settings
- Why:
  - Tarik preferred baseline shaped runtime over the private-pattern profile
  - later listening feedback pointed to specific baseline artifacts, not a need to copy private speech patterns
  - the safest improvement is narrow cleanup of brittle filler/connector cases while preserving provider settings and protected text
- Alternatives considered:
  - promote VOICE-041 despite the baseline winning the A/B
  - keep baseline unchanged and only collect more audio
  - change guarded `final_response` text instead of provider-facing TTS input
- Consequences:
  - VOICE-044 removes narrow fast filler/connector artifacts in eligible English/German freeform provider text
  - provider voice identity, style, and speed settings remain unchanged
  - protected campaign, compliance, handoff, hangup, and do-not-call text stays exact
  - future private-pattern variants still must beat the VOICE-043/VOICE-044 baseline before promotion

### DEC-040 - Lock baseline shaped runtime as the current preferred voice path

- Date: 2026-05-08
- Status: accepted
- Decision: add VOICE-043 to lock RESP-002 baseline shaped runtime as the preferred voice path and prevent VOICE-041 private-pattern settings from being treated as promoted runtime behavior
- Why:
  - Tarik preferred baseline shaped runtime over the softened private-pattern profile in VOICE-042 listening
  - the project needs a checkpoint that turns that listening result into a runtime guard
  - future personalization experiments should compare against baseline instead of replacing it by assumption
- Alternatives considered:
  - leave the decision only in the listening note
  - remove VOICE-041 entirely
  - keep testing private-pattern settings without a baseline acceptance marker
- Consequences:
  - VOICE-043 verifies English, German, and protected do-not-call baseline behavior
  - default runtime keeps `voice_private_pattern_profile.enabled` and `applied` false
  - private-pattern work must remain experimental unless a later A/B beats baseline

### DEC-039 - Do not promote the private-pattern voice profile after baseline wins A/B

- Date: 2026-05-08
- Status: changed
- Decision: do not promote VOICE-041 as a runtime voice improvement after Tarik preferred baseline shaped runtime in VOICE-042 listening; keep the softened profile only as an experimental A/B harness
- Why:
  - Tarik's first VOICE-042 listening review found the private-pattern direction useful
  - the stronger profile sounded too loud and made roboticness more obvious
  - after softening the profile, baseline shaped runtime still sounded better
  - private-pattern personalization should not be promoted unless it beats the current shaped runtime in listening review
- Alternatives considered:
  - keep the stronger `0.12` profile
  - promote the softer `0.06` profile because it was less aggressive
  - disable VOICE-041 entirely
  - alter text, pacing, or filler placement in the same A/B checkpoint
- Consequences:
  - default runtime remains baseline shaped RESP-002 delivery
  - VOICE-041 remains opt-in and experimental only
  - no private-pattern quality improvement claim is allowed from this checkpoint
  - future private-pattern work must test against baseline and win before promotion

### DEC-038 - Isolate VOICE-041 listening tests by keeping A/B text identical

- Date: 2026-05-08
- Status: accepted
- Decision: use VOICE-042 as a live-capable A/B listening harness that compares baseline shaped runtime against VOICE-041 profile-enabled runtime while keeping provider-facing TTS text identical
- Why:
  - Tarik needs to know whether the private speech-pattern profile improves the voice
  - if the text, pause tags, or pacing seed changes between variants, listening cannot isolate the profile effect
  - VOICE-041 should first prove value through bounded provider settings before changing rhythm or wording
  - live TTS calls must remain explicit, bounded, and review-gated
- Alternatives considered:
  - compare the full VOICE-041 pipeline with a different seed
  - immediately apply rhythm-density changes to pacing
  - run live audio without a dry-run validator
- Consequences:
  - VOICE-042 uses one shared seed for both variants
  - `baseline_shaped_runtime` and `private_pattern_profile` send the same text to TTS
  - the profile variant changes only provider settings such as ElevenLabs `style` and `stability`
  - audio quality claims remain blocked until Tarik records a listening review

### DEC-037 - Apply private speech patterns only as accepted abstract provider-setting hints

- Date: 2026-05-08
- Status: accepted
- Decision: add VOICE-041 as an opt-in RESP-002 layer that applies only human-accepted abstract private speech-pattern hints to eligible freeform provider delivery settings
- Why:
  - Tarik wants recurring speech patterns to improve the agent, but not through raw audio upload or voice cloning
  - VOICE-030D/VOICE-031 now identify useful abstract hints: higher rhythm density, higher expressiveness variation, and lower vocal presence that should not be copied
  - provider setting changes can influence protected text, so protected or ineligible segments must block the profile completely
  - accepted pacing from recent listening checks should not be changed silently
- Alternatives considered:
  - read the private VOICE-030D/VOICE-031 files directly during every runtime turn
  - clone or train on Tarik's voice samples
  - hard-code private speech findings globally into the reusable sales core
  - use rhythm density to alter speed immediately
- Consequences:
  - VOICE-041 is disabled by default
  - accepted abstract profiles can raise bounded ElevenLabs expressiveness settings for eligible freeform segments
  - rhythm density is metadata-only until a listening checkpoint proves it should change phrasing or pacing
  - low presence is explicitly blocked from direct copying
  - no raw private audio, transcription, provider upload, voice cloning, or `final_response` rewrite occurs

### DEC-036 - Extract recurring private speech patterns from usable feature files, not pre-wrapped candidates only

- Date: 2026-05-08
- Status: accepted
- Decision: VOICE-030D must read all available private VOICE-030C feature files, count them for coverage, exclude only feature files with no measurable speech from recurring-pattern summaries, and derive candidate values from `features` when `runtime_learning_candidates` is absent
- Why:
  - the first VOICE-030D private review summarized only 8 runtime-candidate-wrapped files even though 121 feature files existed
  - Tarik wants recurring speaking patterns across the sample set, not isolated single-sample candidates
  - feature-only files contain the same acoustic measurements needed for aggregate rhythm, expressiveness, and presence review
  - no-measurable-speech files should not teach the agent silence or flatness
- Alternatives considered:
  - keep using only explicitly wrapped runtime candidates
  - include silent/no-measurable-speech files in the pattern averages
  - apply private speech patterns directly to runtime voice settings
- Consequences:
  - VOICE-030D now reports feature files read, usable recurring-pattern files, and exclusions
  - recurring pattern summaries include normalized speech-burst rhythm and plain-language interpretation
  - pause duration and silence metrics remain diagnostic-only
  - runtime voice behavior still requires human review and a later mapping/application gate

### DEC-035 - Keep voice-listening fixes narrow and case-protected

- Date: 2026-05-08
- Status: accepted
- Decision: preserve the strong English objection and next-step shaped-runtime behavior, repair the English trust transition with connected-speech phrasing plus a livelier bounded speed, and apply only a tiny German pacing lift after the improved German voice ID reduced roboticness.
- Why:
  - Tarik judged English objection and next-step shaped runtime as very close to the intended result
  - the English trust issue appeared to be a swallowed transition, not a general filler-rule problem
  - lowering English trust speed too far made the voice more robotic, so speed alone was the wrong fix
  - the new German voice ID removed most roboticness, so broad German rewrites or pause changes would be unnecessary churn
  - preserving language-specific checks prevents German tuning from silently weakening English
- Alternatives considered:
  - slow all English shaped-runtime output
  - remove fillers or connected-speech joins globally
  - add or remove German pause tags in the objection case
  - leave the live feedback as notes without validator-backed tuning
- Consequences:
  - RESP-003 validation now checks specific shaped-runtime speed bands for English objection, English next-step, English trust, and German objection
  - VOICE-034 carries a dedicated English trust-repair reassurance band of `1.13-1.14`
  - VOICE-035 removes the brittle English `.<break> That's why...` trust transition from provider-facing text
  - German VOICE-034 speed bounds move from `0.97-1.04` to `0.975-1.04`
  - Tarik accepted the corrected RESP-003 live shaped-runtime samples for English trust, English objection, English next-step, and German objection as the current checkpoint
  - broader campaign coverage and production readiness still require later review

### DEC-034 - Keep generated experiment artifacts grouped by checkpoint folder

- Date: 2026-05-07
- Status: accepted
- Decision: move generated experiment artifacts out of the flat `research/experiments/generated/` root and keep future outputs inside milestone or run folders, with only `README.md` allowed at the generated root.
- Why:
  - the flat generated folder had become too large to audit quickly before GitHub checkpoints
  - grouped artifacts make RAG, voice, response, guard, language, and product evidence easier to review independently
  - live-provider audio must stay ignored unless it is deliberately curated
  - the drift guard needs a concrete rule that catches accidental new flat files instead of relying on manual inspection
- Alternatives considered:
  - keep all generated artifacts in the root and depend on filename prefixes
  - exclude all generated artifacts from Git
  - reorganize only new artifacts while leaving older artifacts flat
- Consequences:
  - existing generated reports/results are preserved under checkpoint folders where practical
  - `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports/README.md` records the convention
  - `check_project_drift.py` now fails on unexpected flat generated-root files
  - generated `.wav` and `.mp3` files under nested output folders remain ignored by default
  - thesis and product claims should cite the checkpoint folder, not an unstable flat filename

### DEC-033 - Enable guarded local RAG retrieval only as explicit opt-in

- Date: 2026-05-07
- Status: accepted
- Decision: finish RAG-016B voice/prosody acceptance, build RAG-017 as a local registry of accepted project-owned rules, and connect retrieval to RESP-001 only behind explicit CLI enablement.
- Why:
  - the remaining voice/prosody material is useful as delivery guidance but unsafe as hidden-emotion or buying-intent inference
  - source-mapping blockers and latent quote follow-ups are still unresolved and must stay out of retrieval
  - the product needs traceable runtime hints without adding a vector DB, embedding provider, private data access, or provider dependency
  - campaign guardrails, protected text, refusal handling, do-not-call, and human escalation must outrank retrieved guidance
- Alternatives considered:
  - keep all RAG artifacts review-only until every source-mapping blocker is resolved
  - enable retrieval globally once the registry exists
  - add an embedding/vector retrieval service now
- Consequences:
  - RAG-017 registry artifacts still mark runtime retrieval as disabled by default
  - RESP-001 emits retrieval status for every run, but only uses retrieval when `--retrieval-enabled` is passed
  - refusal, do-not-call, human escalation, protected text, pressure-sensitive, and private-data contexts block retrieval influence
  - voice/prosody retrieval can produce advisory hints only and cannot alter protected text or claim hidden emotion

### DEC-032 - Automate NotebookLM extraction prompts but keep local coverage gates

- Date: 2026-05-06
- Status: accepted
- Decision: implement `RAG-002` as a local NotebookLM extraction automation bridge that generates bounded per-topic prompts and rejects incomplete or small-batch outputs before any RAG promotion.
- Why:
  - Tarik already has real sources organized in NotebookLM, but manual extraction is tedious
  - NotebookLM may return a short batch or summary instead of exhaustive topic coverage
  - prompts must stay under a configurable character limit to avoid UI input failures
  - the product needs source-tracked chunks, not unverified chat notes
  - local validation should enforce completion markers, source IDs, topic IDs, and no-private-data boundaries
- Alternatives considered:
  - manually prompt NotebookLM until each topic feels complete
  - automate the personal NotebookLM UI through browser scraping
  - wait for NotebookLM Enterprise API integration before doing any extraction
- Consequences:
  - RAG-002 creates two prompts per topic: a primary exhaustive report/chunk prompt and a gap-check prompt
  - the default prompt character limit is `4500`
  - tiny outputs are rejected unless NotebookLM explicitly marks source material as insufficient
  - NotebookLM remains an extraction helper, not permanent product memory or runtime retrieval

### DEC-031 - Use NotebookLM as an extraction helper, not product memory

- Date: 2026-05-06
- Status: accepted
- Decision: implement `RAG-001` as a local NotebookLM source-intake bridge that produces source-tracked, paraphrased chunks for the Emotion Aware sales RAG base. NotebookLM is not the permanent memory store and runtime retrieval is not enabled yet.
- Why:
  - Tarik is collecting many public sources across sales, persuasion, speech, and dataset topics
  - the thesis needs a durable path from sources to references and extracted lessons
  - NotebookLM can speed up extraction, but the product should not depend on NotebookLM as its memory layer
  - every future RAG chunk needs source IDs, topic IDs, usage boundaries, compliance notes, and citation notes
  - raw copied source text, full transcripts, private call-center data, and unsourced claims must be blocked
- Alternatives considered:
  - keep a manual list of links in chat
  - use NotebookLM notebooks as the permanent product memory
  - jump directly to runtime retrieval before source validation
- Consequences:
  - RAG now has a 10-topic taxonomy and source-slot manifest
  - future NotebookLM output can be imported only if it validates against the chunk schema
  - RAG runtime retrieval is deferred until `RAG-002` or later
  - thesis source traceability improves because extracted knowledge can be tied back to manifest records

### DEC-030 - Correct low-pressure emphasis through provider-facing wording

- Date: 2026-05-06
- Status: accepted
- Decision: implement `VOICE-040` as a runtime layer that rewrites the provider-facing English phrase `You don't need to change anything today` to `No changes needed today` only when the text is freeform and prosody-eligible.
- Why:
  - Tarik's VOICE-039 listening review found that the selected English voice is now strong enough to keep using
  - the remaining issue is wrong emphasis inside a specific low-pressure phrase, not the guarded sales decision
  - the original phrase has too many tempting emphasis targets for a TTS model
  - shortening the phrase keeps the same sales meaning while reducing unnatural stress placement
  - protected campaign/compliance/handoff/do-not-call text and German text must stay locked
- Alternatives considered:
  - keep the VOICE-039 wording unchanged and rely on the provider voice
  - add markup or emphasis tags around the phrase
  - rewrite the guarded `final_response` directly
- Consequences:
  - RESP-002 now includes `voice_low_pressure_focus`
  - RESP-003 may speak the corrected provider-rendered text only when validation passes
  - the next checkpoint is a short live VOICE-040 listening check with the preferred English voice
  - broader semantic-emphasis expansion should wait for RAG/source-tracked sales knowledge and more listening evidence

### DEC-029 - Promote clear/simple wording as provider-facing TTS only

- Date: 2026-05-06
- Status: accepted
- Decision: implement `VOICE-039` as a runtime candidate that promotes the `VOICE-038` clear/simple worth-your-time phrase into provider-facing English TTS text while preserving the original guarded `final_response`.
- Why:
  - Tarik preferred the clear/simple VOICE-038 variant and also accepted the baseline as a control
  - the remaining issue is phrase-level naturalness, not sales policy or campaign strategy
  - changing only provider-facing TTS text lets us test naturalness without changing what the agent officially decided to say
  - protected campaign/compliance/handoff/do-not-call text must remain exact
  - German should not be rewritten by an English semantic-emphasis rule
- Alternatives considered:
  - rewrite the guarded final response directly
  - keep VOICE-038 as a diagnosis only and postpone runtime testing
  - continue searching for more voices before testing the selected wording pattern
- Consequences:
  - RESP-002 now includes `voice_semantic_emphasis`
  - RESP-003 may speak the promoted provider-rendered text only when the response is freeform and validation passes
  - the next checkpoint is a short live RESP-003 listening check with a longer script
  - future semantic-emphasis expansion should stay pattern-based and campaign-safe unless a broader RAG/LLM layer is reviewed

### DEC-028 - Keep the preferred English voice and promote clear/simple wording next

- Date: 2026-05-06
- Status: accepted
- Decision: keep the current preferred English ElevenLabs voice candidate in active use and make `clear_opening_simple_clause` the lead runtime-promotion candidate, with `baseline_original_clause` retained as an acceptable fallback/control.
- Why:
  - Tarik reported that all VOICE-038 variants sounded good and several steps above earlier outputs
  - the current preferred English voice made one of the strongest improvements in the project so far
  - roboticness is no longer the main English bottleneck for this voice
  - `clear_opening_simple_clause` is shorter and simpler, so it is less likely to create awkward emphasis in future runtime responses
  - `baseline_original_clause` also sounded good, which confirms the voice candidate solved much of the original issue
- Alternatives considered:
  - keep searching for another English voice immediately
  - promote the original baseline wording only
  - add more filler, pause, or pacing randomness before selecting a wording pattern
- Consequences:
  - the next checkpoint should test runtime promotion of the clear/simple wording pattern
  - the baseline should remain available as a control when comparing runtime changes
  - broader voice hunting should pause unless later runtime checks reveal a voice-specific limitation

### DEC-027 - Diagnose semantic emphasis before promoting new English wording

- Date: 2026-05-06
- Status: accepted
- Decision: implement `VOICE-038` as a diagnostic listening checkpoint before changing the runtime response wording or prosody rules for the preferred English voice.
- Why:
  - the preferred English voice mostly solved roboticness
  - the remaining issue is a specific rhythm/emphasis break around a single clause
  - changing runtime wording without an A/B listening diagnosis could trade one unnatural phrase for another
  - a dry-run/live-capable checkpoint keeps provider calls explicit and keeps quality claims tied to human listening
- Alternatives considered:
  - immediately rewrite the runtime response template
  - keep searching for more voices before testing wording
  - add emphasis tags or markdown-like instructions directly to TTS text
- Consequences:
  - VOICE-038 compares six synthetic English variants with the same voice
  - the checkpoint is dry-run by default and live only with `--live`
  - no runtime behavior changes until Tarik selects a winning variant
  - future semantic-emphasis rules should be based on the winning listening pattern, not assumptions

### DEC-026 - Prioritize English voice candidate selection before adding more prosody rules

- Date: 2026-05-06
- Status: accepted
- Decision: keep the current preferred English ElevenLabs candidate in active testing and treat the next English naturalness step as semantic emphasis diagnosis before adding more filler, pause, pacing, or emotion-smoothing rules.
- Why:
  - Tarik's live RESP-003 check with a new English ElevenLabs voice candidate reduced the obvious robotic voice quality by about 95%
  - Tarik rated sales trust as good enough to keep working with this voice
  - this suggests the previous English voice identity/model choice was a major cause of the AI-generated sound
  - the new candidate still broke rhythm/emphasis around a specific clause, so the remaining issue is semantic emphasis alignment rather than general roboticness alone
  - more local filler/pacing randomization could hide the problem without solving the actual emphasis mismatch
- Alternatives considered:
  - keep tuning VOICE-035/VOICE-036/VOICE-037 rules first
  - add a broader phrase-believability rewrite layer immediately
  - compare multiple TTS providers before selecting a better English voice
- Consequences:
  - the current preferred English candidate should be tested with the current RESP-003 runtime path before runtime-rule changes
  - voice IDs remain in environment variables or ignored local config, not tracked source
  - the next checkpoint should compare candidate voices and then decide whether `VOICE-038` needs semantic emphasis selection

### DEC-025 - Smooth vocal emotion with provider settings before rewriting text

- Date: 2026-05-06
- Status: accepted
- Decision: implement `VOICE-037` as an emotion-transition smoothing layer after VOICE-036 and before live TTS.
- Why:
  - Tarik identified that the agent's vocal emotion can jump too sharply between phrases
  - human speech usually has emotional inertia rather than instant mood changes
  - the issue should be solved as delivery control before adding more filler words or rewriting guarded sales text
  - provider settings can reduce theatrical swings while preserving speed and rendered words
- Alternatives considered:
  - change response wording to include more emotional transition phrases
  - add more filler or pause rules
  - retune the ElevenLabs voice identity again before runtime control
- Consequences:
  - VOICE-037 raises provider stability only within a bounded range when sharp transitions are detected
  - VOICE-037 caps style/exaggeration when over-emotional cues appear
  - speed, final response, and protected text stay unchanged
  - live audio still needs human listening review before claiming quality improvement

### DEC-024 - Read raw audio locally before transcription or runtime personalization

- Date: 2026-05-05
- Status: accepted
- Decision: implement `VOICE-030A` as a local WAV audio feature reader before adding local ASR transcription or mapping personal speech patterns into runtime voice settings.
- Why:
  - raw audio contains the pause, rhythm, energy, and speech-burst information that transcript text cannot capture
  - Tarik specifically wants the agent to learn from speech patterns, not just words
  - extracting acoustic features can be done without provider calls, transcription, voice cloning, or raw transcript export
  - keeping ASR as a separate checkpoint makes privacy and failure modes easier to review
- Alternatives considered:
  - jump directly to local ASR transcription
  - upload recordings to a cloud ASR provider
  - apply inferred personal style directly to runtime voice settings
- Consequences:
  - `VOICE-030A` supports WAV only until a local decoder/conversion path is reviewed
  - private raw-audio analysis requires `--allow-private-read`
  - private-input outputs must stay under `data/private/`
  - runtime personalization still requires later human review and validation

### DEC-023 - Start personal speech learning as local abstract profiles, not audio training

- Date: 2026-05-05
- Status: accepted
- Decision: implement `VOICE-029` as a local-only abstract speech-profile extractor before any raw audio transcription, voice cloning, or runtime personalization.
- Why:
  - Tarik wants the agent to learn from how he speaks, especially imperfections, phrasing, pauses, and repair patterns
  - the privacy boundary must be stronger than the feature excitement
  - raw personal recordings and transcripts should not leave `data/private/`
  - runtime changes should be reviewed before the agent starts copying a personal style
- Alternatives considered:
  - directly train/fine-tune on recordings
  - send recordings to an external ASR provider
  - immediately wire personal profile outputs into the live runtime
- Consequences:
  - default VOICE-029 runs use synthetic fixtures and generate public-safe aggregate artifacts
  - actual Tarik speech inputs require `--allow-private-read`
  - private-input outputs stay under `data/private/`
  - the profile is not applied to runtime by default
  - future checkpoints must add local transcription and reviewed runtime mapping separately

### DEC-022 - Add controlled delivery imperfections before personal speech-pattern learning

- Date: 2026-05-05
- Status: accepted
- Decision: implement an opt-in `VOICE-028` controlled delivery imperfection layer before building a local Tarik speech-pattern learning workflow.
- Why:
  - listening feedback showed that machine-perfect delivery is still a realism problem even after better custom voices, spoken-text normalization, filler placement, and interaction prosody
  - imperfections must be bounded and professional, not random stutters or sloppy delivery
  - protected campaign questions, disclosures, handoff scripts, hangup lines, and regulated claim boundaries must stay exact
  - the later Tarik speech-learning idea needs a clear local-only privacy boundary before any samples are collected
- Alternatives considered:
  - tune provider pacing first
  - jump directly into learning from Tarik speech samples
  - rely on ElevenLabs voice remixing alone
- Consequences:
  - `VOICE-028` is campaign opt-in and disabled by default for existing campaigns
  - visible imperfections are suppressed in unsafe claim, stop-intent, anger, and protected-text contexts
  - future Tarik speech samples should live only under `data/private/tarik-speech-samples/`
  - only reviewed abstract speech-pattern notes may leave `data/private/`; no raw audio, no raw transcript export, no provider upload, and no voice cloning by default

### DEC-021 - Add interaction-prosody separation before the next live voice comparison

- Date: 2026-05-04
- Status: accepted
- Decision: implement a `VOICE-026` interaction-prosody/backchannel checkpoint before treating VOICE-025 as ready for the next serious live ElevenLabs comparison
- Why:
  - the deep English/German speech-pattern review showed that filler placement alone cannot solve robotic speech
  - speaker fillers, discourse markers, listener backchannels, latency acknowledgments, speech rate, pitch/intonation, and provider prosody controls have different conversational functions
  - German tokens such as `ja`, `okay`, `genau`, and `also` can sound natural but can also imply agreement if used in the wrong context
  - regulated or campaign-exact text must remain protected from casual hesitation, emotion, and speed variation
- Alternatives considered:
  - run VOICE-025 live audio immediately
  - keep adding more fillers to VOICE-023/VOICE-025
  - rely on ElevenLabs custom voice/remixing alone
- Consequences:
  - the next voice checkpoint should add separate English/German rules for backchannels, discourse markers, pause/prosody cues, and faster-but-bounded sales pace
  - live audio comparison should include `VOICE-026` output against boundary-aware fillers and pause-only cues
  - thesis claims should frame this as literature-informed design until native/proficient listening evaluation and private call-pattern analysis support stronger conclusions
- Implementation note: `VOICE-026` was implemented on 2026-05-04 as an offline/runtime layer for lookup acknowledgements, neutral backchannels, bounded sales-pace cues, unsafe-agreement guards, protected-text locks, and a listening rubric.
- Follow-up note: `VOICE-027` was added on 2026-05-05 as the live-capable A/B harness for comparing the current `VOICE-025` baseline against `VOICE-026` interaction prosody.

### DEC-016 - Use turn-based simulation before product telephony integration

- Date: 2026-04-28
- Status: accepted
- Decision: create a structured turn-based simulation case set for the client MVP before building real outbound calling, calendar integration, or a UI
- Why:
  - the product workflow needs testable behavior before external integrations add complexity
  - simulation cases can exercise interest classification, strategy selection, scheduling triggers, and escalation guardrails
  - this keeps the product track aligned with the thesis habit of small, repeatable experiments
- Alternatives considered:
  - start directly with a telephony prototype
  - build a dashboard before the qualification logic is testable
  - reuse only the thesis prompt-comparison cases for product validation
- Consequences:
  - the next product implementation can target structured `CallOutcome` generation
  - the simulation is not evidence from real client calls and should be labeled as product-synthetic
  - later client or expert feedback can replace or extend these cases

### DEC-001 - Start with a public-data-first baseline

- Date: 2026-04-27
- Status: accepted
- Decision: build the first thesis baseline using public datasets before depending on private call-center data
- Why:
  - private data is not currently in hand
  - the thesis needs a reproducible baseline
  - this reduces risk and keeps early progress unblocked
- Alternatives considered:
  - wait for private data before starting
  - assume private data will become available soon and design around it
- Consequences:
  - the first experiment will optimize for clarity and feasibility rather than direct domain realism
  - later adaptation to private German call-center data remains possible as a documented extension

### DEC-002 - Treat the proposal as directional, not binding

- Date: 2026-04-27
- Status: accepted
- Decision: do not freeze the architecture, metrics, or dataset plan based solely on the initial thesis proposal
- Why:
  - parts of the methodology section were drafted as estimations rather than confirmed implementation choices
  - locking them too early would create unnecessary rigidity
- Alternatives considered:
  - mirror the proposal exactly in the repo and implementation plan
- Consequences:
  - the repo structure remains flexible
  - the written thesis will need to distinguish early proposal assumptions from final implementation choices

### DEC-003 - Use MELD and Persuasion for Good as phase-1 anchors

- Date: 2026-04-27
- Status: accepted
- Decision: use `MELD` and `Persuasion for Good` as the most actionable phase-1 public datasets while treating `IEMOCAP` as pending verification
- Why:
  - both are already available locally in usable extracted form
  - they cover the emotion and persuasion sides of the first baseline
  - the current `IEMOCAP` download appears to be a derivative export rather than the official corpus structure
- Alternatives considered:
  - delay dataset work until all three datasets are equally ready
  - start with larger phone-conversation corpora such as Switchboard or Fisher
- Consequences:
  - the first experiment will likely be text-forward or dialogue-structure-first rather than audio-first
  - an audio-focused phase may still be added later

### DEC-004 - Use MELD sentiment for the first compact emotion taxonomy

- Date: 2026-04-27
- Status: accepted
- Decision: use the `Sentiment` column in `MELD` as the primary phase-1 emotion signal instead of collapsing the raw seven-way `Emotion` labels directly
- Why:
  - it already provides a compact three-way label space
  - it avoids arbitrary treatment of `surprise`
  - it is easier to align with the first adaptive baseline
- Alternatives considered:
  - collapse the raw `Emotion` column directly into three classes
  - exclude `MELD` and wait for a cleaner speech-emotion dataset
- Consequences:
  - the first baseline will be broader in affective meaning than a fine-grained emotion classifier
  - raw emotion labels remain available for later secondary experiments

### DEC-005 - Use a five-part persuasion taxonomy for phase 1

- Date: 2026-04-27
- Status: accepted
- Decision: compress the persuader labels in `Persuasion for Good` into five strategy groups: `rapport`, `inquiry`, `evidence-or-benefit`, `emotional-appeal`, and `direct-ask-or-commitment`
- Why:
  - the original label set is too granular for the first adaptive baseline
  - the reduced taxonomy remains interpretable and close to the dataset's annotation intent
  - the dataset does not strongly justify forcing `reassurance` as a primary phase-1 category
- Alternatives considered:
  - use the full original label space
  - use a four-part taxonomy that merges emotional appeal into another category
- Consequences:
  - the first experiment stays manageable
  - later experiments may refine or expand the strategy space

### DEC-006 - Start with a rule-based adaptive baseline comparison

- Date: 2026-04-27
- Status: accepted
- Decision: define the first experiment as a comparison between a non-adaptive baseline and a rule-based adaptive baseline that changes strategy selection based on compact emotion state
- Why:
  - it creates a clear and implementable first comparison
  - it tests the core thesis idea without requiring full end-to-end agent complexity
  - it keeps the adaptation logic transparent for analysis and writing
- Alternatives considered:
  - jump directly to a learned strategy policy
  - delay baseline definition until full model architecture is chosen
- Consequences:
  - the first implementation can focus on interpretable strategy shifts
  - later work can replace the rule-based policy with learned components if justified

### DEC-007 - Use prompt templates plus rubric-based comparison for the first runnable evaluation

- Date: 2026-04-27
- Status: accepted
- Decision: operationalize the first baseline through paired prompt templates and a lightweight qualitative evaluation rubric
- Why:
  - it gives the project a runnable experiment format quickly
  - it keeps the first evaluation interpretable and easy to document
  - it avoids premature commitment to a heavy metric stack before the response behavior is even tested
- Alternatives considered:
  - delay prompt work until a coded pipeline exists
  - define only quantitative evaluation at this stage
- Consequences:
  - the next implementation step can focus on generating paired responses for test cases
  - early thesis evidence can include concrete side-by-side examples and rubric outcomes

### DEC-008 - Start with curated synthetic seed cases for the first prompt comparison pass

- Date: 2026-04-27
- Status: accepted
- Decision: use a small set of project-authored synthetic cases as the first evaluation inputs before moving to dataset-derived cases
- Why:
  - it lets the project test the prompt comparison workflow immediately
  - it keeps the first cases tightly aligned with the phase-1 strategy and emotion taxonomy
  - it reduces setup friction while the data-driven case extraction path is still being shaped
- Alternatives considered:
  - wait until dataset-derived cases are prepared
  - mix synthetic and dataset-derived cases from the start
- Consequences:
  - the first evaluation pass will be useful for workflow and behavior validation, not final thesis claims
  - later experiments should extend the case set with stronger empirical grounding

### DEC-009 - Adapt modular voice analytics as a later sales-agent module

- Date: 2026-04-27
- Status: accepted
- Decision: incorporate the concept of modular interpretable voice-feature analysis from collaborative thesis work with Shehzeb Iftakhar as a later module in the sales-agent emotion engine
- Why:
  - voice features are directly relevant to customer emotion and conversational state
  - the idea strengthens the multi-modal direction of the sales-agent thesis
  - the collaborator relationship and supervisor approval allow concept sharing with proper attribution
- Alternatives considered:
  - keep the sales-agent project text-only
  - import the full creative-expression analytics framework
- Consequences:
  - phase 1 remains focused on text and strategy baselines
  - phase 2 can compare text-only adaptation against text-plus-voice adaptation
  - attribution and conceptual boundaries should be documented clearly in the thesis

### DEC-010 - Document supervisor-approved AI use for the technical workflow

- Date: 2026-04-27
- Status: accepted
- Decision: explicitly document that AI usage is supervisor-approved for the technical part of the thesis project
- Why:
  - it clarifies the legitimacy of AI-assisted technical development
  - it creates a transparent record for later thesis writing and defense
  - it separates technical assistance from final thesis authorship responsibility
- Alternatives considered:
  - leave AI usage undocumented
  - document it only informally outside the project
- Consequences:
  - the thesis record now includes a clear statement on AI-assisted technical workflow
  - future write-up can reference this permission without reconstructing the policy from memory

### DEC-011 - Use structured JSON case files plus a generated prompt packet as the repeatable execution path

- Date: 2026-04-27
- Status: accepted
- Decision: operationalize repeatable prompt comparisons through structured JSON case files and a small runner script that generates markdown prompt packets
- Why:
  - it reduces manual prompt assembly
  - it keeps the case inputs explicit and reusable
  - it creates a consistent bridge between case design, prompt execution, and scoring
- Alternatives considered:
  - keep using markdown-only case packs with manual copying
  - jump directly to a heavier end-to-end automated evaluation system
- Consequences:
  - future case sets can be added more cleanly
  - the current workflow remains lightweight while becoming more reproducible

### DEC-012 - Scope the first client MVP around qualification and scheduling, not autonomous closing

- Date: 2026-04-27
- Status: accepted
- Decision: define the first client MVP as an autonomous lead-qualification and appointment-setting agent with fallback and escalation guardrails
- Why:
  - it matches the actual client need more closely than a full autonomous closer
  - it creates a more realistic early product scope
  - it lets the thesis adaptation logic support a concrete and defensible workflow
- Alternatives considered:
  - aim immediately for full sales-closing behavior
  - make the launch workflow permanently human-in-the-loop for normal cases
- Consequences:
  - qualification questions and interest classification become first-class product artifacts
  - human sales agents remain the closing path for interested leads

### DEC-013 - Treat the project as both thesis and real product

- Date: 2026-04-27
- Status: accepted
- Decision: explicitly steer the project as both an academic thesis and a real product intended for client use
- Why:
  - a potential client is ready to buy when the product launches
  - product usefulness creates constraints that pure thesis planning would miss
  - the thesis evidence can strengthen the product, while product requirements can keep the thesis grounded
- Alternatives considered:
  - continue treating productization as a distant future step
  - focus only on the client product and weaken the thesis evidence trail
- Consequences:
  - the roadmap now includes a product MVP track
  - early implementation should target autonomous behavior while preserving fallback and escalation guardrails
  - product claims must remain separate from thesis experiment claims until evidence supports them

### DEC-014 - Use sales-expert feedback as a product training loop

- Date: 2026-04-27
- Status: accepted
- Decision: incorporate feedback from experienced salespeople during development so the agent can learn from expert ratings, rewrites, labels, and strategy corrections
- Why:
  - sales experts can provide domain judgment that public datasets cannot capture
  - expert feedback can improve response quality before client launch
  - this creates a practical learning path beyond static prompt comparisons
- Alternatives considered:
  - rely only on public datasets and synthetic cases
  - attempt model fine-tuning before collecting expert preference data
- Consequences:
  - the product track should include a feedback capture format
  - early learning should start with prompt/rule updates and example retrieval before fine-tuning
  - expert feedback data must be stored and attributed carefully

### DEC-015 - Define the first product as lead qualification and appointment setting

- Date: 2026-04-27
- Status: accepted
- Decision: scope the first client-facing product to autonomous outbound lead qualification and appointment setting with human sales-agent follow-up
- Why:
  - this matches the client's actual initial request
  - it is narrower and more launchable than a full autonomous closing agent
  - it still benefits from emotion-aware strategy adaptation
- Alternatives considered:
  - build directly toward a full autonomous sales closer
  - build only a human-reviewed sales copilot
- Consequences:
  - the first product workflow should focus on call initiation, qualification questions, interest detection, and scheduling
  - the thesis baseline remains relevant because strategy adaptation supports qualification and objection handling
  - calendar/availability integration becomes a product requirement

### DEC-016 - Treat English/German voice naturalness as speech mechanics, not stereotypes

- Date: 2026-05-04
- Status: accepted
- Decision: design future English and German speech-realism profiles around fillers, pauses, breath, rhythm, repairs, and warmth cues, while keeping language mechanics separate from campaign persona and cultural stereotypes
- Why:
  - the agent needs to sound less robotic in both English and German
  - human speech uses language-specific timing, filler, and interaction patterns
  - random fillers would reduce trust and could make the system sound fake
  - stereotype-like language behavior would be product-risky and academically weak
- Alternatives considered:
  - use one generic filler system for all languages
  - rely only on provider voice remixing and avoid local speech-realism rules
  - make the voice more casual without language-specific constraints
- Consequences:
  - `VOICE-023` should use language-aware profiles
  - protected campaign text remains exact and filler-free
  - English and German profile rules should cite `SPEECH_REALISM_REFERENCES.md`
  - future listening evaluation should include naturalness, trust, professionalism, and overacting risk

### DEC-017 - Maintain a central thesis reference registry

- Date: 2026-05-04
- Status: accepted
- Decision: keep a thesis-level source registry that separates academic sources, dataset sources, provider documentation, sales-practice articles, privacy references, and open-source inspiration
- Why:
  - many useful sources were found across different checkpoints
  - chat history is not a reliable bibliography
  - not all sources have the same evidential weight
  - thesis writing needs fast access to source URLs and usage boundaries
- Alternatives considered:
  - keep references only inside each experiment note
  - put all sources into `SPEECH_REALISM_REFERENCES.md`
  - rely on `third-party-inspirations.md` only
- Consequences:
  - `THESIS_REFERENCE_REGISTRY.md` becomes the first stop for source lookup
  - `SPEECH_REALISM_REFERENCES.md` stays focused on speech-realism literature
  - product engineering implications belong in product docs such as `VOICE_023_SPEECH_REALISM_LAYER.md`
  - final thesis citations still need formatting and source verification before submission

### DEC-018 - Use visible thesis traceability checks instead of a hidden Git hook

- Date: 2026-05-04
- Status: accepted
- Decision: add explicit local scripts that check source-reference coverage and thesis-documentation coverage before GitHub checkpoints, but do not install a Git hook by default
- Why:
  - the project is both a product and a thesis workspace
  - meaningful changes should remain explainable later during thesis writing
  - hidden hooks are local-only, easy to forget across machines, and can become frustrating if they block work invisibly
  - visible scripts make the rule auditable and portable
- Alternatives considered:
  - rely on manual memory during each push
  - install a pre-push hook immediately
  - auto-edit thesis docs from a script
- Consequences:
  - `check_thesis_reference_registry.py` should pass before pushing source-backed work
  - `check_thesis_update_gate.py` should pass before GitHub checkpoints
  - scripts report and recommend, but do not auto-write thesis content
  - an optional hook can be added later if the command-based workflow proves stable

### DEC-019 - Insert speech realism after spoken-text normalization and before prosody

- Date: 2026-05-04
- Status: accepted
- Decision: apply VOICE-023 after VOICE-022 spoken-text normalization, then pass the resulting realistic freeform text into prosody and provider rendering
- Why:
  - fillers and thinking behavior should operate on the text that will actually be spoken
  - protected text must already be identified and preserved before naturalness layers run
  - prosody should see the final delivery text so pauses and provider tags align with filler placement
- Alternatives considered:
  - add fillers before spoken-text normalization
  - fold VOICE-023 into VOICE-015 prosody only as metadata
  - rely only on ElevenLabs voice design/remixing instead of local guardrails
- Consequences:
  - provider `plain_text` may differ from VOICE-022 `tts_text` when VOICE-023 inserts safe fillers
  - validators must compare provider input against the latest runtime delivery layer, not only the spoken-normalization layer
  - `final_response` remains unchanged and is still the guarded source of truth

### DEC-020 - Evaluate VOICE-023 with an A/B listening harness before claiming quality

- Date: 2026-05-04
- Status: accepted
- Decision: compare the same improved ElevenLabs English/German voices with and without VOICE-023 before deciding whether speech realism should be strengthened, reduced, or moved partly into provider voice design
- Why:
  - user listening feedback is currently the strongest signal for perceived naturalness
  - provider voice quality and local speech-realism rules must not be mixed into one unclear result
  - live provider calls need explicit API-key, timeout, local voice-ID, and redaction gates
- Alternatives considered:
  - immediately tune VOICE-023 based on dry-run text only
  - rely only on ElevenLabs remixing prompts
  - compare multiple providers before isolating the local speech-realism layer
- Consequences:
  - `VOICE-024` becomes the current listening checkpoint
  - default runs remain dry-run and provider-safe
  - live MP3s are local ignored artifacts and are not thesis evidence until Tarik records listening observations
