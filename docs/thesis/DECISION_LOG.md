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

### DEC-144 - Close the Atlas hosted phase with one post-final-write canary and explicit exclusions

- Date: 2026-07-14
- Status: accepted
- Decision: close the documented final-fingerprint gap with one existing, fixed CRM canary after the last behavior-changing provider write. Accept wrap-up of the covered hosted text/simulation phase only when the provider result, deterministic trace validator, independent transcript review, and fresh structural readback agree. Preserve the untested explicit repetition-complaint branch and all speech/real-customer domains as exclusions.
- Why:
  - the last prompt/KB patch was structurally read back but had no post-write behavior trace;
  - rerunning the full 036/040 suites would spend more credit while mixing stale test-contract conflicts into a narrow CRM repetition question;
  - the existing 040 direct-CRM canary exercises buyer-triggered pricing, scope progression, CTA suppression, and near-repeat behavior without changing a dashboard test;
  - one provider label is insufficient, so the captured transcript also requires deterministic and independent manual adjudication.
- Alternatives considered:
  - claim wrap-up from structural readback alone;
  - rerun every historical suite;
  - edit the 036 or 040 tests/evaluators to force agreement;
  - leave the phase open despite a bounded fixed case already covering the final changed lane.
- Consequences:
  - the final live fingerprint has targeted transcript evidence for the tested existing-site direct CRM progression;
  - the explicit "you already said that" complaint branch remains optional future regression work because this canary did not contain that buyer move;
  - no production, PSTN, ASR, latency, interruption, buyer-perception, conversion, or real-customer claim follows;
  - future provider tests should run only for a new bounded evidence objective, not to make historical dashboards universally green.

### DEC-143 - Reconcile hosted provider labels with independent transcript adjudication

- Date: 2026-07-14
- Status: accepted
- Decision: for hosted ElevenLabs evidence, treat provider evaluator labels as advisory. A thesis-ready result must reconcile provider labels with deterministic independent trace validators and manual transcript review, then classify failures as product defect, provider evaluator defect, stale test-contract defect, or incomplete simulation before deciding whether to patch the product, revise the test governance, or preserve the limitation.
- Why:
  - 039 showed that an earlier provider-labeled pass was not accepted until the test state and raw trace proved the exact terminal condition.
  - 040 full-suite evidence mixed provider labels, deterministic failures, and manual review; real product defects were repaired with focused multi-feature, CRM, and portal traces, while stale 036 dashboard expectations were not used to regress current product behavior.
  - provider labels alone can hide event-order problems, stale dynamic variables, collapsed buyer turns, or evaluator expectations that no longer match the active contract.
  - weakening dashboard criteria or Analysis definitions to obtain a green result would damage thesis validity.
- Alternatives considered:
  - accept provider pass/fail labels as final;
  - require every historical full suite to be green before recording evidence;
  - edit stale dashboard criteria immediately to match the latest behavior;
  - keep rerunning broad suites after credit restraint instead of reconciling existing evidence and running targeted checks.
- Consequences:
  - thesis claims must name which evidence is provider-labeled, independently validated, manually adjudicated, or structurally read back;
  - full 036/040 captures with historical failures remain useful evidence but cannot be called universally green;
  - real product defects should be fixed and rerun with targeted traces first;
  - test-contract revision is a separate governance change, not a way to retroactively manufacture readiness;
  - no outbound-call, PSTN audio, ASR, latency, interruption, buyer-perception, conversion, or real-customer proof is implied by hosted text/simulation evidence.

### DEC-142 - Use buyer-triggered pricing and one active price lane for Atlas detailed-pricing control

- Date: 2026-07-14
- Status: accepted
- Decision: Atlas paid pricing should be disclosed only after buyer price intent and should stay inside one applicable lane for the current scope. Capability, proof, process, and next-step turns should remain price-free unless the buyer asks about cost; once price is requested, the agent should choose the applicable lane rather than stacking multiple feature ranges or inventing unsupported quotes.
- Why:
  - the 040 evidence found real product defects around multi-feature price stacking, CRM CTA reopening/repetition, and portal number echoing before scope was known.
  - the repaired targeted traces show the intended behavior: multi-feature scope uses one whole-project band, CRM follow-up avoids repeated CTAs and narrows missing inputs, and portal/custom scope avoids speculative numbers before proof and scope are established.
  - buyer-triggered pricing keeps consultative discovery separate from premature quote behavior and reduces unsupported certainty.
  - one-lane pricing is easier to validate, safer for campaign truth, and less confusing in a voice-style sales conversation.
- Alternatives considered:
  - volunteer pricing during capability or mockup explanation;
  - list all possible feature add-ons in one response;
  - preserve the older 036 handoff-price/mockup-next-step expectation even when it conflicts with the active 040 contract;
  - quote portal or CRM work from buyer-provided numbers before scope is known.
- Consequences:
  - evaluation must check price intent, lane selection, no unsupported fixed quote or ceiling, no price stacking, and no CTA reopening while scope or price follow-up remains active;
  - stale tests that expect earlier handoff-price behavior should be treated as test-contract issues until deliberately revised;
  - product fixes should target real transcript defects, while current-contract disagreements should be documented rather than patched away;
  - pricing evidence remains product-policy evidence for Atlas, not a market-wide claim that all web providers charge the same amounts.

### DEC-141 - Use a three-layer sales knowledge architecture for universal RAG and campaigns

- Date: 2026-06-06
- Status: accepted
- Decision: separate sales knowledge into Universal Sales RAG, Campaign Sales Overlay, and Campaign Profile And Facts. Universal Sales RAG owns reusable sales method. Campaign Sales Overlay adapts that method to one campaign. Campaign Profile And Facts owns approved truth and has highest authority.
- Why:
  - Universal sales behavior should be reusable across campaigns without copying product facts, prices, proof, or guarantees into a global corpus.
  - Campaigns need a middle layer for adapting discovery, value framing, objections, proof use, next steps, and call-quality expectations without mutating the universal core.
  - ElevenLabs RAG retrieves relevant chunks from attached documents; it should not be treated as a deterministic cross-document import or routing system.
  - Prompt-level precedence is required so facts beat overlay guidance and overlay guidance beats universal advice when the provider retrieves mixed context.
- Alternatives considered:
  - one merged campaign/universal RAG, rejected because it would blur reusable method with factual truth
  - only two layers, universal RAG plus campaign profile, rejected because it lacks a safe place for campaign-specific sales adaptation
  - textual cross-references between uploaded knowledge-base files, rejected as too weak for provider-hosted RAG behavior
- Consequences:
  - provider packages should attach or compile separate universal, overlay, and profile documents
  - critical precedence rules must be in the agent prompt, not only in retrieved documents
  - Universal Sales RAG must not contain campaign prices, client names, guarantees, testimonials, or factual claims
  - future campaign onboarding should generate a Campaign Sales Overlay and Campaign Profile And Facts before live upload

### DEC-140 - Keep Ultravox as a promising but latency-limited hosted speech interface candidate

- Date: 2026-05-29
- Status: accepted
- Decision: keep Ultravox as an evaluated hosted speech-native interface candidate, not the current runtime path and not an ElevenLabs replacement. Ultravox may own hosted speech input/output, session transport, WebSocket flow, short-term session mechanics, and provider tool invocation. The project runtime must continue to own campaign truth, sales-brain decisions, canonical buyer memory, source/fact boundaries, verifier logic, and side-effect safety.
- Why:
  - `ULTRAVOX-TOOL-BOUNDARY-MOCK-001` and `ULTRAVOX-LOCAL-TOOL-ENDPOINT-001` passed 8/8 synthetic cases with auth and side-effect safety
  - cloudflared Quick Tunnel did not become the usable path because local DNS/trycloudflare resolution failed; ngrok worked after auth/config and public-endpoint preflight
  - `ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001` created a hosted session, connected by WebSocket, completed three synthetic text turns, and observed the project HTTP tool boundary without product-truth drift or fake side effects
  - `ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001` completed two manual-audio turns, observed user transcripts, received agent audio, called the local HTTP project tool, and kept product-truth drift, fake side effects, CRM/email/calendar claims, and source-boundary violations at zero
  - manual listening review classified audio quality as promising, with intelligibility 5/5, voice quality 5/5, naturalness 3/5, sales tone 3.5/5, pacing 4.5/5, artifact severity 1/5, thesis-demo suitability 4/5, and product-fallback suitability 5/5
  - warm-turn latency remained too slow: baseline warm p50 4.638s and p90 5.148s; optimized p50 4.69s and p90 6.073s
- Alternatives considered:
  - let Ultravox own sales logic, product truth, or canonical memory
  - treat successful WebSocket/audio sandbox evidence as live-production readiness
  - claim Ultravox replaces ElevenLabs before voice/voice-ID comparison and latency gates pass
  - continue provider latency probing immediately after the optimization probe did not improve results
- Consequences:
  - stop Ultravox provider latency testing for now
  - no live wiring, production call, outbound phone call, real customer use, CRM/email/calendar side effect, or final ElevenLabs replacement claim is allowed
  - Ultravox remains useful for thesis discussion as an alternative hosted speech-interface architecture path with a working tool boundary but unacceptable current latency for live production calls
  - revisit only if provider settings, model/voice options, or platform changes plausibly reduce latency

### DEC-139 - Accept cleaned prosody taxonomy and no-provider ElevenLabs mapping prototype as evidence only

- Date: 2026-05-29
- Status: accepted
- Decision: accept the cleaned Fish-inspired internal prosody taxonomy and no-provider ElevenLabs mapping prototype as thesis evidence and future delivery-control design input, while keeping the current live speech path unchanged.
- Why:
  - `PROSODY-TAXONOMY-CLEANUP-001` preserved 267 labels across 24 categories and 46 composition rules while reducing duplicate mapping signatures to 0, vague labels to 0, backend hint boilerplate to 0, mapping warnings to 0, and mapping failures to 0
  - sales-prosody mappings were reduced from 138 to 92 after cleanup
  - Fish tags remain internal only, raw Fish tags are still disallowed in ElevenLabs text, and Fish was not installed or run
  - `ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001` created 62 no-provider mapping examples
  - `ELEVENLABS-PROSODY-MAPPING-QUALITY-AUDIT-001` passed 62/62 examples with 0 warnings and 0 failures, no raw Fish tag leakage, no internal label leakage, no fake side effects, no raw URL speech, and no live wiring allowed
  - `ELEVENLABS-PROSODY-MAPPING-DECISION-001` recommends a future offline ElevenLabs sample-generation phase only after explicit provider-call approval
- Alternatives considered:
  - treat the cleaned mapping prototype as a live ElevenLabs integration
  - generate provider audio immediately to validate mapping quality
  - inject bracket tags or internal labels into buyer-facing speech
  - retire the prosody taxonomy because it is not yet audio-validated
- Consequences:
  - this is design and evidence, not audio-quality proof
  - ElevenLabs remains the current live voice path
  - future provider sample generation requires explicit provider-call approval and listening review
  - runtime behavior, response text, and live speech wiring remain unchanged

### DEC-138 - Treat evidence validators and quality gates as separate instruments

- Date: 2026-05-29
- Status: accepted
- Decision: keep evidence-integrity validators, deterministic regressions, and quality gates separate. A validator pass can prove that an artifact is well formed, side-effect-safe, and regression-covered; it does not prove live sales quality, voice quality, or production readiness.
- Why:
  - post-baseline OpenAI, local LLM, Liquid, and prosody phases showed that structurally valid evidence can still reveal quality failures or cleanup needs
  - `LOCAL-QWEN-MIXED-REPLAY-QUALITY-GATE-001` failed usefully without authorizing live wiring
  - `PROSODY-TAXONOMY-QUALITY-DECISION-001` passed the decision artifact while recommending cleanup before mapping
  - live call review and manual listening review remain the strongest signals for actual sales and speech quality
- Alternatives considered:
  - treat any passing evidence validator as readiness
  - block evidence commits whenever quality gates fail
  - run the full historical validator ring for every phase
- Consequences:
  - failed quality gates can be committed as honest research evidence
  - docs must distinguish evidence pass, quality pass, thesis-demo readiness, live-demo readiness, and product readiness
  - focused validators remain the default unless broad runtime behavior changes

### DEC-137 - Keep ElevenLabs as the current voice path while prosody mapping remains plan-only

- Date: 2026-05-29
- Status: accepted
- Decision: keep ElevenLabs as the current live voice path. The Fish-inspired prosody layer and ElevenLabs mapping readiness plan remain architecture/config/evidence only, with no provider calls, no raw Fish tags in ElevenLabs text, and no live runtime wiring.
- Why:
  - `ELEVENLABS-PROSODY-MAPPING-READINESS-001` records `current_integration_status: not_wired`
  - Fish-style tags are internal only and not allowed in buyer-facing text
  - `PROSODY-TAXONOMY-QUALITY-DECISION-001` recommends targeted taxonomy and mapping cleanup before any ElevenLabs mapping prototype
  - replacing or changing the live TTS path without listening review would confuse architecture research with product quality
- Alternatives considered:
  - directly inject Fish-style bracket tags into ElevenLabs speech
  - wire the deterministic prosody planner into live speech immediately
  - replace ElevenLabs with Fish, Liquid, or Kokoro before comparative listening evidence
- Consequences:
  - ElevenLabs remains the operational voice path
  - future ElevenLabs prosody mapping must be prototype-only first, with no provider calls unless explicitly approved
  - no spoken response behavior changes from the prosody taxonomy

### DEC-136 - Build a Fish-inspired internal prosody taxonomy without importing Fish or its tag universe

- Date: 2026-05-29
- Status: accepted
- Decision: use Fish Audio S2's inline prosody/emotion-control concept as inspiration for an internal, backend-neutral, sales-safe prosody taxonomy and deterministic planner; do not install Fish, run Fish inference, import the 15,000+ tag universe, or leak Fish tags into active speech.
- Why:
  - Fish S2 provides a useful control-language pattern, but its hardware and commercial-license constraints make it unsuitable as a current local dependency
  - the project needs a curated sales delivery layer that maps buyer emotion, sales move, objection type, and conversation state to safe delivery guidance
  - `FISH-INSPIRED-PROSODY-TAXONOMY-001` records 267 internal labels, 24 categories, 46 composition rules, 138 mappings, and 45 examples, with tag injection disabled
- Alternatives considered:
  - create a tiny label list that would be too weak for sales delivery
  - scrape or import Fish's full tag universe
  - use Fish tags directly in ElevenLabs output
- Consequences:
  - prosody controls are internal project labels, not raw provider tags
  - future backend mappings must pass leakage and quality checks
  - 4I3 found warnings and cleanup needs before any mapping prototype

### DEC-135 - Retire Liquid Audio as a TTS or voice backend after manual listening review

- Date: 2026-05-28
- Status: accepted
- Decision: keep Liquid Audio as speech-to-speech architecture inspiration only. Do not use it as a thesis-demo TTS, product fallback TTS, live voice backend, ASR quality proof, or sales-brain replacement.
- Why:
  - Liquid setup, model load, and synthetic TTS smoke were mechanically successful, but manual listening review found all five generated TTS files unintelligible/gibberish with no recognizable words
  - the loopback ASR result was based on Liquid-generated audio and is not final ASR quality evidence
  - `LIQUID-AUDIO-LISTENING-REVIEW-DECISION-001` sets `liquid_architecture_inspiration_only: true`, `product_fallback_tts_allowed: false`, and `live_wiring_allowed: false`
- Alternatives considered:
  - compare Liquid immediately against Kokoro or ElevenLabs despite failed intelligibility
  - keep Liquid as a fallback because the setup worked
  - use Liquid as a broader local sales-brain candidate
- Consequences:
  - no Liquid runtime wiring
  - no Liquid audio is committed
  - Kokoro remains the optional future local TTS benchmark candidate if local TTS becomes thesis-relevant

### DEC-134 - Reject current local Qwen 7B and tested small local models for live per-turn use

- Date: 2026-05-28
- Status: accepted
- Decision: do not wire local Qwen2.5-7B, Qwen LoRA adapters, Ollama Qwen 7B, or the tested small Ollama models into live per-turn voice dialogue. Treat full local LLM response generation as not live-ready; keep action-id-only selection, distilled small selectors, and non-LLM classifier/action selectors as research paths.
- Why:
  - Qwen2.5-7B compact planner passed small smoke tests but failed the 80-case gold-set quality gate
  - QLoRA and tiny overfit experiments proved the pipeline can train, but curriculum and mixed-replay adapters did not pass quality gates
  - Qwen 7B latency remained far above the live target, including Ollama backend evidence
  - tested small Ollama models got closer, especially constrained/action modes, but did not meet strict live latency targets
  - a live voice turn still needs acceptable latency whenever an LLM is used, even if the LLM is called less often
- Alternatives considered:
  - wire Qwen 7B as the live conversation brain
  - keep training larger QLoRA datasets before simplifying the target
  - prune Qwen 7B immediately
  - use a small local model for full spoken response generation
- Consequences:
  - no local LLM live wiring
  - no model weights, adapters, or checkpoints are committed
  - future model work should test constrained action selection before full response generation
  - the live target remains roughly 2-3 seconds for any model-in-the-turn path

### DEC-133 - Keep the LLM as conversation planner, not fact owner or side-effect owner

- Date: 2026-05-28
- Status: accepted
- Decision: the desired long-term architecture is: LLM as conversational move planner; deterministic layer as memory ledger, verifier, source/fact boundary, safety guardrail, and anti-loop detector; campaign configs/source bundles as product truth; TTS/prosody layer as delivery control. The deterministic layer must not become the normal conversation brain except for hard safety fallback.
- Why:
  - a purely deterministic conversation brain becomes brittle and canned
  - a free LLM cannot own product facts, source truth, CRM/email/calendar side effects, or safety decisions
  - `LOCAL-QWEN-TWO-HEAD-ARCHITECTURE-001` records `llm_remains_conversation_brain: true` and `deterministic_layer_role: memory_and_verifier_only`
  - anti-loop memory should tell the planner what happened, while the verifier flags repetition and unsafe output
- Alternatives considered:
  - let the LLM generate final buyer-facing speech without deterministic verification
  - move all conversation planning into deterministic templates
  - let local LLM outputs alter campaign facts or side effects
- Consequences:
  - one replan is allowed for non-critical verifier issues
  - hard deterministic fallback is reserved for safety-critical or repeated verifier failure
  - buyer-facing uncertainty must be natural clarification, not internal classifier language
  - local LLM work remains isolated until quality and latency gates pass

### DEC-132 - Move from scenario patching toward semantic frame mapping

- Date: 2026-05-27
- Status: accepted
- Decision: stop treating exact dialogue-path patches as sufficient. Future sales-dialogue work should emphasize semantic frame mapping, buyer-state tracking, relation fidelity such as AND/OR and negation, ASR alias handling, memory progression, and generalized intent/action planning.
- Why:
  - OpenAI live-derived evidence showed that the agent could answer product questions yet still fail as a sales agent when it stalled, dumped information, repeated itself, or missed buyer intent
  - `PUBLIC-OPENAI-SEMANTIC-UNDERSTANDING-001` covers 630 scenarios and 590 multi-turn cases
  - `PUBLIC-OPENAI-LIVE-SEMANTIC-PIPELINE-001` covers ASR aliases, state transitions, terminal acceptance, and stability-guard ownership without provider calls
  - validators are regression tripwires, not proof that real buyers experience the conversation as intelligent
- Alternatives considered:
  - continue one-off patches for each observed phrase
  - expand scenario count without changing semantic representation
  - rely on broad menu fallback after uncertainty
- Consequences:
  - future evaluations should test paraphrases and meaning preservation, not only exact utterances
  - "I already told you" and repeated-question cases must use memory before asking again
  - buyer-facing clarification should sound natural and should not expose classifier uncertainty

### DEC-131 - Define sales-ready as active selling, not product explanation

- Date: 2026-05-25
- Status: accepted
- Decision: for this project, "sales-ready" means the agent can actively sell: move the buyer toward a decision, handle objections, recommend or disqualify based on fit, avoid loops and passive information dumping, and behave closer to a strong sales agent than a static FAQ reader.
- Why:
  - OpenAI plan-fit evidence showed that source-grounded product answers are necessary but not sufficient
  - `OPENAI-LIVE-SALES-SKILL-FAILURE-AUDIT-001` recorded missing sales-skill classes from private live evidence without copying raw transcript text
  - `PUBLIC-OPENAI-LIVE-SALES-READINESS-001`, `PUBLIC-OPENAI-DECISION-STAGE-SELLING-001`, `PUBLIC-OPENAI-COMMERCIAL-CLOSING-001`, and `COMMERCIAL-SALES-PERFORMANCE-GATE-001` extended evaluation toward decision-stage selling, commercial closing, and loop prevention
- Alternatives considered:
  - define readiness as answering product questions accurately
  - optimize only for source-grounded factuality
  - defer sales momentum and objection handling to a human operator
- Consequences:
  - evaluation must include sales momentum, recommendation quality, objection handling, no-fit decisions, and terminal-close discipline
  - source grounding remains required, but factual correctness alone is not a sales-quality pass

### DEC-130 - Resolve the ElevenLabs voice issue as configuration precedence, not hardcoded voice logic

- Date: 2026-05-25
- Status: accepted
- Decision: treat the observed ElevenLabs voice mismatch as a runtime configuration/environment issue, not as a hardcoded voice-id bug in campaign logic. Voice diagnostics should avoid logging raw voice IDs and should preserve env/local-config precedence boundaries.
- Why:
  - `ELEVENLABS-VOICE-RESOLUTION-AUDIT-001` found no hardcoded voice-id findings and no raw voice-id logging
  - the active packet resolved the voice from local voice config, while stale process environment variables could affect a live server until restart
  - the audit made no live TTS or provider calls and copied no private transcript into public evidence
- Alternatives considered:
  - patch campaign voice IDs directly
  - assume ElevenLabs itself was broken
  - log raw voice IDs into public evidence for debugging convenience
- Consequences:
  - live voice fixes should check process environment, local config, and server restart state before changing runtime code
  - public evidence may record hashes/aliases but not raw private config values

### DEC-129 - Keep the OpenAI public fixture source-grounded and self-serve while improving live sales behavior

- Date: 2026-05-25
- Status: accepted
- Decision: preserve the OpenAI public fixture as a source-grounded self-serve plan-fit campaign while improving live sales flow, intent priority, decision-stage selling, memory progression, spoken naturalness, and commercial closing.
- Why:
  - post-baseline evidence (`PUBLIC-OPENAI-LIVE-SALES-FLOW-001`, `PUBLIC-OPENAI-INTENT-PRIORITY-001`, `PUBLIC-OPENAI-MEMORY-PROGRESSION-001`, `PUBLIC-OPENAI-SPOKEN-SALES-NATURALNESS-001`, and `PUBLIC-OPENAI-COMMERCIAL-CLOSING-001`) passed without provider calls, raw URL speech, fake side effects, or private transcript copying
  - the fixture must still avoid official OpenAI affiliation claims, email/calendar/CRM side effects, raw spoken URLs, payment collection, and Enterprise pricing overclaims
- Alternatives considered:
  - revert to appointment-style close semantics
  - weaken source constraints to make sales language easier
  - let universal dialogue absorb OpenAI product facts
- Consequences:
  - self-serve and contact-sales close semantics remain campaign-owned
  - universal dialogue stays product-agnostic
  - further sales improvements must not compromise source grounding or side-effect safety

### DEC-128 - Make self-serve close semantics campaign-owned for the OpenAI public fixture

- Date: 2026-05-24
- Status: accepted
- Decision: treat the public OpenAI/ChatGPT plan fixture as a self-serve plan-fit campaign, not an appointment-setting campaign. The fixture uses `objective: self_serve_plan_fit`, `close_mode: self_serve_purchase_link`, voice-ready spoken close labels, metadata-only raw URL exposure, and `contact_sales` for Enterprise.
- Why:
  - reading a raw URL aloud is poor voice behavior
  - saying a link was sent would be false because no email integration exists
  - Enterprise procurement and organization-level controls require the official contact-sales route, not a fake booking claim
  - a real product fixture should not inherit appointment/review framing from synthetic campaigns when the product journey is self-serve
- Alternatives considered:
  - keep `appointment_setting` as the fixture objective for schema compatibility
  - speak the raw official pricing URL in final responses
  - request an email address and imply link sending
- Consequences:
  - individual plan closes point to the official self-serve route without speaking raw URLs
  - raw URL metadata remains available for packets and UI output
  - `can_send_email` remains false
  - no email, calendar, CRM, payment collection, OpenAI affiliation, or Enterprise pricing claim is introduced
  - `PUBLIC-OPENAI-CLOSE-SEMANTICS-001` covers individual, business, Enterprise, no-fit, negative-control, and cross-campaign close behavior

### DEC-127 - Add a source-grounded public OpenAI product fixture without contaminating universal dialogue

- Date: 2026-05-24
- Status: accepted
- Decision: add `public-openai-chatgpt-plans` as an internal public-data simulation using only official OpenAI public sources, with every allowed product, pricing, privacy, sign-up, API-boundary, and feature claim represented as a source-grounded claim object. Keep OpenAI facts out of universal sales runtime files.
- Why:
  - synthetic campaigns had become acceptable fixtures but still mostly sold generic reviews or fit checks instead of rich real product value
  - a real source-grounded product benchmark is needed to test whether the agent can answer buyer questions about plans, upgrades, teams, privacy, API separation, and next steps
  - product facts are campaign knowledge, while response shape, buyer-move handling, and side-effect safety are universal behavior
- Alternatives considered:
  - add ChatGPT plan facts directly to universal response rules
  - keep using only synthetic product fixtures
  - use non-OpenAI web sources to enrich the fixture
- Consequences:
  - OpenAI product knowledge lives in `runtime/campaigns/examples/public-openai-chatgpt-plans.json`, `research/sources/public_openai_chatgpt_plans/`, and public OpenAI generated evidence
  - protected universal files remain OpenAI-fact-free
  - source validators check official domains, retrieved timestamps, claim backing, and side-effect flags
  - campaign dialogue and contamination validators prove OpenAI facts do not leak into RouteSignal or synthetic campaigns
  - the fixture is explicitly not an official OpenAI sales agent and must not claim affiliation or authorization

### DEC-126 - Reduce routine validation budget to focused affected checks

- Date: 2026-05-24
- Status: accepted
- Decision: stop running the full historical validator ring for every phase. Use focused validators, directly affected validators, runtime manifest, project drift guard, and `git diff --check` by default; reserve the full ring for broad universal runtime changes, major milestones, or release-readiness sweeps.
- Why:
  - the validator suite is now large enough that full-ring execution on every narrow phase creates slow feedback and hides the relevant signal
  - most phases touch a bounded area with specific evidence needs
  - focused budgets still preserve side-effect, manifest, and drift checks while reducing unnecessary generated-evidence churn
- Alternatives considered:
  - keep the full historical ring as the default for every phase
  - run only the new validator and skip manifest/drift checks
  - refresh unrelated evidence packets for every documentation or campaign change
- Consequences:
  - phase prompts should state the validation budget explicitly
  - additional validators must be justified when run
  - documentation-only phases should not run runtime dialogue validators unless runtime files change
  - "all validators passed" must not be claimed when the budget was intentionally targeted

### DEC-125 - Use replay-first live failure methodology before broad runtime patches

- Date: 2026-05-23
- Status: accepted
- Decision: convert live-call failures into focused deterministic replay tests before patching, classify whether evidence is current or stale, then patch only reproduced current defects with exact regressions, generalized variants, and negative controls.
- Why:
  - live calls revealed failures that earlier dry-run validators missed: unanswered direct questions, ASR near-miss misroutes, stability guards reopening broad menus, repeated response loops, missed stop variants, and confusion between product/offer value and appointment/review targets
  - broad validator patching can make stale issues look current or create new regressions
  - private transcripts should not become public thesis content; only sanitized lessons and generated evidence should be cited
- Alternatives considered:
  - patch directly from raw live transcript observations
  - expand validators broadly without reproducing the failure
  - treat all historical live feedback as equally current
- Consequences:
  - `CURRENT-LIVE-TRANSCRIPT-REPLAY-001` and related live-demo replay artifacts are the public-safe bridge from live observation to deterministic regression
  - private raw transcript text remains excluded from thesis files
  - current defects can be generalized without copying private dialogue
  - live testing remains necessary for ASR, TTS, latency, and voice realism even when replay validators are green

### DEC-124 - Treat the live-inspired adversarial matrix as a regression net, not a sales-quality proof

- Date: 2026-05-24
- Status: accepted
- Decision: use `LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001` as the broad deterministic regression surface for buyer challenges, ASR near-misses, stop/refusal handling, campaign contamination, menu loops, stability-guard failures, and response progression, while keeping human review and live calls as separate quality gates.
- Why:
  - the matrix reached 729/729 dry-run pass across 398 multi-turn conversations, 30 scenario families, and 6 campaigns after focused response-progression and no-menu repairs
  - deterministic pass/fail coverage catches repeatable failure classes faster than ad hoc live bug discovery
  - the matrix cannot measure actual microphone capture, speech timing, provider audio quality, latency, buyer perception, or real sales effectiveness
- Alternatives considered:
  - rely primarily on supervised live calls for regression detection
  - treat the matrix pass as enough to claim live or commercial readiness
  - keep only narrow one-off replay tests
- Consequences:
  - adversarial evidence supports the thesis methodology for regression hardening
  - "validator pass" and "sales-quality pass" remain distinct claims
  - live rehearsal and human review remain mandatory before stronger product-readiness claims

### DEC-123 - Move customer-facing campaign wording out of universal runtime

- Date: 2026-05-23
- Status: accepted
- Decision: remove or reduce hardcoded synthetic campaign ids, vertical-to-phrase branches, RouteSignal-specific customer-facing phrases, and hardcoded gap wording from universal runtime. Universal dialogue owns response shapes and sales behavior; campaign configs/adapters own product-specific facts, customer-facing offer wording, plan/value language, and campaign next-step targets.
- Why:
  - universal runtime had started to accumulate campaign wording and fixture assumptions
  - that drift made cross-campaign generalization fragile and risked leaking one campaign's claims into another
  - validators should test universal behavior against fixtures, not make fixture wording part of the universal layer
- Alternatives considered:
  - keep expanding universal runtime with campaign id branches
  - create separate runtimes per campaign
  - tolerate RouteSignal-specific wording as "generic enough"
- Consequences:
  - `UNIVERSALIZATION-DRIFT-CLEANUP-001` resolved or reduced UDR findings to acceptable test-fixture-only status
  - RouteSignal wording belongs in the adapter/playbook layer
  - generic campaign wording belongs in config facts
  - the same separation later enabled the OpenAI fixture without contaminating protected universal files

### DEC-122 - Widen universal sales dialogue architecture before adding richer campaigns

- Date: 2026-05-22
- Status: accepted
- Decision: add a universal sales conversation knowledge contract and universal policy runtime frame for buyer moves, response shapes, ASR repair boundaries, campaign fact slots, forbidden patterns, call control, repair rules, next-step discipline, rapport, trust/privacy boundaries, social contexts, and high-confidence buyer-move priority.
- Why:
  - the project needed a reusable sales-agent core rather than campaign-specific route patches
  - buyer questions, objections, trust challenges, stop variants, confusion, regulated-scope questions, hardship, and social interruptions are cross-campaign behavior
  - product facts, plan names, prices, and campaign wording must stay campaign-owned
- Alternatives considered:
  - continue patching the live voice policy directly for each observed phrase
  - let campaign configs define both facts and universal response behavior
  - move final speech generation to an unchecked LLM planner
- Consequences:
  - direct product/value answers, objections, trust/privacy handling, challenge repair, no-menu suppression, pain progression, appointment readiness, rapport relevance, and next-step discipline are now universal dialogue responsibilities
  - campaign adapters supply the facts and customer-facing terms needed by those shapes
  - future controlled LLM response planning remains possible only behind strict guardrails and replay coverage

### DEC-121 - Split universal sales knowledge from campaign playbooks before non-RouteSignal live routing

- Date: 2026-05-21
- Status: accepted
- Decision: keep RouteSignal as one campaign playbook behind `campaign_playbook_adapter`, add product-agnostic `universal_sales_knowledge`, add vertical-level playbook defaults, and require a separate runtime integration gate before any non-RouteSignal campaign affects live speech.
- Why:
  - the contextual buyer semantics, dialogue manager action contract, call-control state, send-info/contact state, callback timing state, and right-person handoff state are reusable core behavior
  - RouteSignal gaps, Northstar wording, Starter/Growth plan facts, `$29`/`$59` pricing, inbound-demo callbacks, manual tracking, handoffs, routing, duplicates, and visibility are campaign-specific facts, not universal sales knowledge
  - synthetic cross-vertical resolution is useful evidence only if it does not silently change the accepted RouteSignal live-demo behavior
  - regulated verticals need explicit caution and blocked-claim metadata before any live customer-facing routing
- Alternatives considered:
  - keep extending the RouteSignal diagnostic playbook as if it were universal
  - integrate generic campaign configs directly into live routing after adapter smoke tests
  - create separate hard-coded runtimes per vertical
- Consequences:
  - `runtime/core/universal_sales_knowledge.py`, `runtime/core/vertical_sales_playbooks.py`, `runtime/core/sales_diagnostic_playbook.py`, and `runtime/core/campaign_playbook_adapter.py` form the current abstraction chain
  - `runtime/runtime_manifest.json` and `scripts/validate_project_drift_guard.py` now track the expanded dialogue-core and campaign-playbook surface for project drift evidence
  - `CONTEXTUAL-BUYER-SEMANTICS-001` through `010` remain valid RouteSignal-shaped/runtime-state evidence, not proof of every vertical
  - `CAMPAIGN-PLAYBOOK-ADAPTER-002` proves generic synthetic campaign config resolution in memory only
  - live non-RouteSignal routing, provider calls, local LLM calls, CRM writes, email sending, calendar events, real customer data, production promotion, full autonomous sale closure, and `PROD-102` remain blocked until an explicit integration checkpoint

### DEC-120 - Promote only safe English wording in PROD-053E

- Date: 2026-05-15
- Status: accepted
- Decision: promote the `PROD-053D` accepted-as-written, safe wording-only, and approved-with-edit-note English responses as `PROD-053E-english-runtime-wording-patch`.
- Why:
  - the reviewed phrase-level English responses are actionable evidence, while voicemail action-only behavior, coverage policy knowledge, and autonomy context sensitivity are different runtime/design problems
  - promoting all `needs_rework` items would mix wording improvements with call-control and knowledge-policy behavior changes
  - `PROD-054` needs a stable single-turn English runtime baseline before multi-turn naturalness stress testing
- Alternatives considered:
  - include voicemail action-only behavior in the same patch
  - include coverage knowledge-policy behavior in the same patch
  - wait for `PROD-054` before promoting any English wording
- Consequences:
  - `26` English responses are promoted in `runtime/core/realtime_turns.py`
  - `prod-053c-voicemail`, `prod-053c-coverage-boundary-route`, and `prod-053c-autonomy-check` stay unpromoted
  - retrieval, providers, LLM calls, private data, voice playback, demo use, payment collection, contract signing, German phrase promotion, German naturalness claims, and production runtime promotion remain blocked

### DEC-119 - Import English review before runtime patch

- Date: 2026-05-15
- Status: accepted
- Decision: import Tarik's `PROD-053C` English review export as `PROD-053D-english-review-import` before changing runtime text.
- Why:
  - the review contains both exact approvals and open rework notes, so treating every `approved` status as exact phrase acceptance would be unsafe
  - one approved row, `prod-053c-existing-provider-gap`, includes a material wording note to use `won't` instead of `will not`
  - several notes are not simple phrase edits: voicemail should become action-only, coverage needs a policy-knowledge vs advice decision, and autonomy wording depends on previous call context
- Alternatives considered:
  - patch all approved and rework items directly into runtime
  - ignore notes attached to approved rows
  - move immediately to multi-turn testing
- Consequences:
  - `15` items are accepted as-written
  - `1` approved item is separated as approved-with-edit-note
  - `13` items are marked needs-rework
  - `14` patch candidates are recorded without runtime promotion
  - the next patch should be narrow and should separate plain wording updates from voicemail action-only behavior, coverage policy-knowledge behavior, and context-sensitive autonomy wording
  - runtime behavior, response text, German exact-phrase promotion, German naturalness claims, retrieval, providers, LLM calls, private data, voice playback, demo use, payment collection, contract signing, and production promotion remain blocked

### DEC-118 - Build English response expansion without duplicate review

- Date: 2026-05-15
- Status: accepted
- Decision: create `PROD-053C-english-spoken-response-expansion-review` as a broader English-only exact phrase review packet, while excluding already-approved carry-forward responses from `PROD-053B`.
- Why:
  - Tarik should not spend time re-reviewing English responses already accepted or carried forward
  - the current runtime has more reachable English response types than the four English items separated in `PROD-052`
  - the compact `PROD-053B` psychology rules are useful as review criteria, but not yet approved as runtime response text
- Alternatives considered:
  - reopen all four `PROD-052` English cases
  - skip the broader single-turn review and go directly to multi-turn testing
  - apply the compact policy directly to runtime responses
- Consequences:
  - `prod-045-price-first` and `prod-045-send-info` are excluded as already-approved carry-forward items
  - `prod-045-manager` and `prod-045-spouse` are included because they were flagged for customer-category echoing and weak no-commitment relief
  - `27` previously unreviewed reachable English deterministic runtime response types are added to the review packet
  - `provider-comparison` remains out of exact phrase review because the current classifier has no distinct reachable English branch for it
  - runtime behavior, response text, German exact-phrase promotion, German naturalness claims, retrieval, providers, LLM calls, private data, voice playback, demo use, payment collection, contract signing, and production promotion remain blocked

### DEC-117 - Audit thesis paths after runtime move

- Date: 2026-05-15
- Status: accepted
- Decision: after moving runtime-affecting files under `runtime/`, update thesis references to the current canonical paths and treat ignored local files such as `runtime/config/local/voice_ids.json` as valid location references even when the local file is not present.
- Why:
  - the thesis should be writable from current project artifacts, not stale historical paths
  - old product-doc stubs and compatibility wrappers can keep commands working, but thesis evidence should point to canonical runtime locations where possible
  - ignored local config paths may be correct even when absent from the working tree
- Alternatives considered:
  - leave old references because compatibility wrappers still exist
  - update only command docs and leave thesis logs unchanged
  - create a broad rewrite of historical methodology entries
- Consequences:
  - stale tracked references to moved SQLite schema, product prompt, provider boundary docs, generated-audio log, and local voice config examples are updated to `runtime/` paths
  - historical checkpoint script paths remain valid when compatibility wrappers still exist
  - the thesis reference registry and update gates remain the source checks, while path existence is reviewed as a separate hygiene step

### DEC-116 - Review compact English psychology before expansion

- Date: 2026-05-15
- Status: accepted
- Decision: use `PROD-053B-compact-english-psychology-layer-review` as the gate between the deep `PROD-053A` research packet and the broader `PROD-053C` English spoken-response expansion.
- Why:
  - adding more psychology research before testing the existing rules would increase complexity without proving better response quality
  - the compact layer must stay deterministic, English-only, low-latency, and non-LLM-dependent
  - some candidate rules are useful only with constraints, especially mirroring, friction questioning, and autonomy language
- Alternatives considered:
  - add more broad human psychology sources before implementation
  - skip directly to the broader English response packet
  - import the compact policy directly into runtime behavior
- Consequences:
  - all `8` PROD-053A candidate rules are accepted for PROD-053C review use, with `3` accepted only under constraints
  - all rejected/deferred tactics remain blocked
  - current English stakeholder/partner review responses are flagged for PROD-053C rewrite because they echo customer categories and need clearer no-commitment relief
  - runtime behavior, response text, German exact-phrase promotion, German naturalness claims, retrieval, providers, LLM calls, private data, voice playback, demo use, payment collection, contract signing, and production promotion remain blocked

### DEC-115 - Move runtime source under runtime with wrappers

- Date: 2026-05-15
- Status: accepted
- Decision: move runtime-affecting source modules, runtime assets, and canonical runtime-facing Markdown under `runtime/`, keep thin `scripts/*` compatibility wrappers plus product-doc stubs for historical paths, and validate the boundary with `runtime/runtime_manifest.json` plus `scripts/validate_runtime_manifest.py`.
- Why:
  - Tarik needs to see which files affect actual runtime behavior before continuing response-layer work
  - many historical command docs, checkpoint validators, and local scripts reference exact `scripts/*` paths
  - a physical move without compatibility wrappers would break validators and confuse the evidence trail
- Alternatives considered:
  - keep only a manifest and defer the physical move
  - leave the current folder structure and rely on memory
  - only update README text without a machine-checkable manifest
- Consequences:
  - runtime-affecting files now have a real `runtime/` home instead of being mixed with checkpoint runners and validators
  - existing commands keep working through `scripts/` wrappers
  - moved local config examples, campaign examples, prompts, and persistence schema now live under `runtime/`
  - canonical runtime Markdown for architecture, realtime CLI behavior, call termination, bilingual runtime behavior, provider run boundaries, generated-audio logging, and SQLite persistence now lives under `runtime/`
  - historical generated artifacts may still mention old paths, but active docs, validators, and setup checks should use `runtime/` paths
  - runtime behavior, response text, retrieval defaults, provider calls, LLM calls, private-data reads, voice playback, demo use, payment collection, contract signing, and production promotion remain unchanged or blocked

### DEC-114 - Research deeply before compact English psychology layer

- Date: 2026-05-15
- Status: accepted
- Decision: insert `PROD-053A-english-sales-psychology-deep-dive` before the compact English conversation psychology layer and broader English spoken-response expansion.
- Why:
  - the runtime layer must remain small for live-call latency, but the rule set should be distilled from deeper sales psychology and human communication research
  - Tarik wants actually useful sales psychology, not generic tricks or a shallow rule list
  - source-backed research can separate useful mechanisms from manipulative or risky tactics before any response wording changes
- Alternatives considered:
  - add a small psychology layer directly from intuition
  - build a large live psychology planner
  - continue to the broader English phrase review without researching the underlying conversation rules
- Consequences:
  - PROD-053A remains research-only and changes no runtime behavior or response text
  - PROD-053B should review compact English rule candidates before any broad English response expansion
  - PROD-053C should then create the broader English spoken-response review packet, excluding already-approved items unless explicitly reopened
  - false scarcity, hidden emotion diagnosis, commitment traps, broad customer-category echoing, and generic unsourced persuasion tricks remain rejected or deferred
  - providers, LLM judging, private data, retrieval defaults, voice/demo/customer use, payment collection, contract signing, and production promotion remain blocked

### DEC-113 - Expand English review before multi-turn stress testing

- Date: 2026-05-15
- Status: accepted
- Decision: keep a broader English spoken-response expansion before English multi-turn naturalness stress testing, now sequenced as `PROD-053C-english-spoken-response-expansion-review` after the compact psychology layer review.
- Why:
  - PROD-052 has only the four English cases inherited from the PROD-051 call-control update
  - the broader English policy surface contains more answer types that should be reviewed before testing conversation continuation
  - Tarik can judge English wording directly, so English should be the active phrase-quality lane while German remains pending native/source-backed review
- Alternatives considered:
  - keep `PROD-053` as multi-turn stress testing immediately
  - add unrelated German wording into the active acceptance lane
  - inflate PROD-052 with extra cases outside its source checkpoint
- Consequences:
  - PROD-052 remains a language-lane separation checkpoint, not the full English review packet
  - PROD-053B should first review the compact English psychology layer from PROD-053A
  - PROD-053C should build a broader English-only spoken-response review surface from existing English runtime cases
  - multi-turn English testing moves to `PROD-054`
  - German exact phrase acceptance remains blocked

### DEC-112 - Separate phrase acceptance by language

- Date: 2026-05-15
- Status: accepted
- Decision: create `PROD-052-language-lane-review-separation` and treat English exact spoken responses as the current owner-review lane while keeping German exact wording pending native German or source-backed wording review.
- Why:
  - deterministic checks can constrain style and safety, but they do not prove that a specific German phrase sounds natural to a native speaker
  - Tarik can currently review English phrase naturalness directly, so near-term product learning should focus there
  - older mixed English/German review pages can confuse acceptance status if they are reused as current human review surfaces
- Alternatives considered:
  - rewrite old German responses from memory
  - delete or mutate historical mixed generated artifacts
  - continue treating PROD-051 German exact wording as accepted because deterministic checks passed
- Consequences:
  - English exact responses can move into Tarik review and later English multi-turn stress testing
  - German exact responses remain separated and unaccepted until fresh native/source-backed evidence exists
  - shared multilingual rules remain valid only as policy constraints such as answer-first, low-pressure continuation, short spoken shape, and no internal jargon
  - older mixed review pages are inventoried as historical evidence or superseded surfaces, not active exact phrase acceptance pages
  - runtime behavior, response text, providers, LLM judging, private data, voice/demo/customer use, payment collection, contract signing, and production promotion remain unchanged or blocked

### DEC-111 - Validate naturalness before accepting live call-control softening

- Date: 2026-05-14
- Status: accepted
- Decision: apply `PROD-051-safe-call-control-runtime-update` only with a deterministic naturalness audit over the same fixed cases used for the runtime change.
- Why:
  - changing `call_control` alone can pass shallow validators while the spoken response still sounds terminal or internal
  - naturalness needs baseline comparison on fixed cases, not visual inspection of generated artifacts
  - selected non-refusal cases should continue only when the response answers first, stays optional, avoids pressure, and avoids customer-facing internal jargon
- Alternatives considered:
  - accept PROD-050 proposal evidence without live naturalness gates
  - use LLM judging or provider calls for naturalness scoring
  - wait for human/native review before any deterministic runtime update
- Consequences:
  - `PROD-051` updates live runtime only for `price-first-direct`, `written-info-request`, `stakeholder-review`, and `partner-review`
  - `answer-and-continue` becomes the narrow runtime action that maps to `bridge-then-continue`
  - the naturalness gate requires direct answer, optional low-pressure continuation, no terminal close, no internal jargon, spoken sentence shape, customer-fit, language-fit, and no pressure/payment/contract/unsupported claim
  - provider calls, LLM judging, private data, voice/demo/customer use, payment collection, contract signing, and production promotion remain blocked

### DEC-110 - Prove call-control softening before runtime migration

- Date: 2026-05-14
- Status: accepted
- Decision: run `PROD-050-safe-call-control-softening-regression` as proposed-softening evidence before editing the live deterministic runtime.
- Why:
  - selected bridge-then-continue cases need regression evidence before historical runtime expectations are migrated
  - bridge-then-continue cannot be applied as a control flag alone if the response text still sounds terminal
  - older validators still encode the current `end-call` behavior for German price-first, written-info, and review paths
  - separating proposed evidence from the runtime update keeps the product history auditable and prevents accidental broad softening
- Alternatives considered:
  - change live runtime call-control immediately after PROD-049
  - leave safe-but-abrupt end-calls unchanged indefinitely
  - bundle runtime behavior changes into the same checkpoint as the review decision
- Consequences:
  - `PROD-050` proves all `22` selected non-refusal candidates can be proposed as `bridge-then-continue` with low-pressure continuation text and without pressure, payment, contract, or unsupported-claim violations
  - support, cancellation, do-not-call, human-request, email-only, payment/scam safety, sale-ready, and callback boundaries remain unchanged
  - a separate `PROD-051` checkpoint is required before live runtime call-control or response-text behavior changes
  - retrieval, providers, private data, voice/demo/customer use, payment collection, contract signing, and production promotion remain blocked

### DEC-109 - Park German follow-up review and move to call-control softening evidence

- Date: 2026-05-14
- Status: accepted
- Decision: park `PROD-048D` until a corrected native German reviewer export exists, and move the local product track to `PROD-049-safe-end-call-bridge-continue-review`.
- Why:
  - `PROD-048D` cannot be completed without external reviewer input
  - PROD-046 already identified `45` safe-but-abrupt call-control findings that can be reviewed offline
  - call-control softening is product-relevant and can move forward without provider calls, private data, voice listening, or native German approval
- Alternatives considered:
  - wait for the German reviewer export before doing more project work
  - start a voice/personality selector while `RESP-007` listening remains unresolved
  - resume RAG/source hygiene instead of product-runtime quality
- Consequences:
  - `PROD-049` selects only non-refusal candidate groups for future bridge-then-continue testing
  - support, cancellation, do-not-call, human-request, email-only, payment/scam safety, sale-ready, and callback boundaries remain protected
  - runtime behavior and call-control behavior are not changed until a future regression checkpoint proves the softening is safe
  - voice/demo/customer use, payment collection, contract signing, and production promotion remain blocked

### DEC-108 - Apply only reviewed German price wording before follow-up review

- Date: 2026-05-12
- Status: accepted
- Decision: apply only the PROD-048B reviewed German price-first wording correction and send a corrected grouped follow-up packet before making any broader German wording claim.
- Why:
  - reviewer Diro marked the price answer phone-acceptable but only partially natural and flagged the final payment sentence as creating a sales-pressure effect
  - payment/no-contract safety wording is still required in scam, payment, sale-ready, and explicit safety contexts, but it should not be repeated in a plain price-first answer
  - only `5` rows were reviewed, so a broader native German approval claim would overstate the evidence
- Alternatives considered:
  - apply wording changes to all German answers
  - remove no-payment/no-contract language globally
  - treat the partial review as full native approval
- Consequences:
  - the German plain price-first answer is shortened
  - payment, scam, and sale-ready boundary wording remains available and tested
  - the corrected reviewer HTML marks `Preisfrage` for re-check and keeps unreviewed groups visible
  - full native German approval, legal compliance, voice/demo/customer use, payment collection, contract signing, and production promotion remain blocked

### DEC-107 - Treat partial native German feedback as partial evidence only

- Date: 2026-05-12
- Status: accepted
- Decision: import reviewer feedback as partial evidence, recompute reviewed rows from filled fields, and keep blank rows classified as unreviewed rather than accepted or rejected.
- Why:
  - the returned reviewer JSON summary reported `0` checked rows even though `5` rows contained ratings, comments, or flags
  - the returned file contained `99` individual rows while the current grouped PROD-048A packet has `22` visible groups
  - overclaiming the blank rows would create false native German approval evidence
- Alternatives considered:
  - trust the exported summary blindly
  - treat blank rows as rejection
  - treat the `5` reviewed rows as full native German approval
- Consequences:
  - PROD-048B records partial native German evidence only
  - the price-first row becomes a targeted revision candidate for a later patch checkpoint
  - follow-up review should continue with the grouped HTML
  - legal compliance, runtime promotion, voice playback, public demo use, and real customer use remain blocked

### DEC-106 - Group repeated German answers before native review

- Date: 2026-05-12
- Status: accepted
- Decision: group repeated German answers in the native review packet and review shorter customer-facing answer variants before asking for a native German wording decision.
- Why:
  - early human feedback said the previous packet made the German answers look too AI-like because they were long, forced, complete, and repetitive
  - many different customer utterances received the exact same answer, making per-case review tiring without adding reviewer value
  - grouping repeated German answers preserves traceability while giving the reviewer a realistic wording-quality task
- Alternatives considered:
  - keep one full card per original German case
  - change runtime policy immediately before human review
  - claim the source-informed German wording is already acceptable
- Consequences:
  - all original case IDs remain in the machine-readable packet and export
  - the visible review HTML shows grouped answer cards
  - runtime policy and call-control behavior remain unchanged
  - native German approval and legal compliance remain unclaimed

### DEC-105 - Collect native German wording review before German promotion claims

- Date: 2026-05-12
- Status: accepted
- Decision: create a native German review packet before making any German wording-quality, voice/demo, public-demo, or customer-facing promotion claim.
- Why:
  - PROD-046 accepted German responses only for synthetic regression evidence and internal product review
  - PROD-047 made German campaign fields contract-guarded but did not provide native speaker approval
  - a native German review packet can collect structured human feedback without changing runtime behavior
- Alternatives considered:
  - claim German wording readiness from deterministic validators alone
  - wait for voice/demo work before gathering human wording feedback
  - ask a reviewer to inspect technical JSON artifacts directly
- Consequences:
  - the native German review packet becomes the next evidence gate
  - reviewer feedback should be imported in a later checkpoint before any German wording approval claim
  - legal compliance remains explicitly unclaimed
  - voice/demo/customer use remains blocked until separate promotion gates pass

### DEC-104 - Require campaign-profile contracts before voice/demo/customer use

- Date: 2026-05-12
- Status: accepted
- Decision: require deterministic campaign-profile contracts for language, field shape, source boundary, review status, policy-group coverage, and hard safety defaults before any campaign field can support voice/demo/customer-facing promotion.
- Why:
  - PROD-046 found campaign fields are the main product bottleneck after the deterministic policy surface passed regression
  - malformed German interpolation and internal-sounding English/German wording came from treating campaign fields as interchangeable strings
  - voice/demo/customer use needs stronger profile contracts than offline regression evidence
- Alternatives considered:
  - proceed directly to native German wording review without a reusable campaign contract
  - rely on runtime templates to sanitize campaign fields dynamically
  - allow valid profiles to unlock voice/demo/customer use immediately
- Consequences:
  - valid profiles remain offline/internal-review only by default
  - malformed, internal, unsafe, or under-reviewed profile fields fail deterministically
  - `blocked_for_voice`, `blocked_for_public_demo`, and `blocked_for_customer_use` remain the default readiness state
  - retrieval, providers, LLMs, private data, payment collection, contract signing, public demo, voice playback, and production runtime promotion remain blocked

### DEC-103 - Accept core sales-policy surface for offline regression only

- Date: 2026-05-12
- Status: accepted
- Decision: accept the PROD-045 through PROD-046D core sales-policy surface for offline regression evidence and internal product review, but keep it blocked from voice playback, public demo use, real customer use, retrieval defaults, provider calls, LLM calls, private-data reads, payment collection, contract signing, and production runtime promotion.
- Why:
  - PROD-045 through PROD-046D validators pass and show deterministic handling of English and German required-boundary moves
  - review evidence still finds product-readiness risks: English internal policy wording, German native-review need, possible `Verkaufsteil` awkwardness, abrupt end-call behavior, and campaign-field shape dependency
  - a regression-passing deterministic surface is not the same as customer-facing readiness
- Alternatives considered:
  - promote the current policy surface to voice/demo use after PROD-046D
  - run native German review before adding campaign-profile contracts
  - continue German wording rewrites without first formalizing campaign-field shape rules
- Consequences:
  - PROD-046 remains review-only and does not change runtime behavior
  - the next implementation checkpoint should be `PROD-047-campaign-profile-contract-validator`
  - native German review remains required before German voice, demo, or real customer use
  - future call-control softening should be tested separately so safety boundaries remain intact

### DEC-102 - Source-inform German runtime wording without using sales scripts

- Date: 2026-05-12
- Status: accepted
- Decision: use regulator, consumer-protection, public-service, and plain-language sources as source-informed wording guidance for German runtime responses, and reject cold-call scripts, sales guru blogs, aggressive closing scripts, affiliate SEO pages, and copied competitor wording as German wording sources.
- Why:
  - PROD-046C fixed malformed interpolation, but German customer-facing output still contained internal-sounding language such as overused `freigegeben`, `Vertriebsteil`, and log-centric callback wording
  - the German B2C path includes trust, refusal, written-info, scam/payment, support/cancellation, and regulated-advice boundaries where pressure-oriented sales scripts are the wrong source model
  - source-informed plain-language and consumer-protection guidance can improve wording without claiming legal compliance or copying external scripts
- Alternatives considered:
  - proceed directly to human review after PROD-046C
  - use German cold-call or sales scripts for more natural sales phrasing
  - call an LLM or provider to rewrite German responses
  - broaden product/legal/insurance claims during the wording pass
- Consequences:
  - PROD-046D narrows German customer-facing wording and campaign-field shape only
  - accepted external source URLs are recorded in the thesis reference registry and generated source traceability map
  - no legal-compliance claim is made
  - retrieval, providers, LLMs, private data, payment collection, contract signing, voice playback, public demo polish, and production runtime promotion remain blocked

### DEC-101 - Add German interpolation guard before human policy review

- Date: 2026-05-12
- Status: accepted
- Decision: create `PROD-046C-german-campaign-field-interpolation-guard` before PROD-046 human review to block malformed German campaign-field interpolation while preserving the PROD-045/046A/046B regression surface.
- Why:
  - PROD-046B removed banned internal terms, but actual generated German runtime outputs still included malformed strings such as `Preisrahmen bei beim Starter-Paket` and `Ich rufe kurz an, um ein kurzer Abgleich`
  - the root cause is campaign fields being inserted into fixed German templates without field-shape awareness
  - these deterministic grammar failures should be removed before asking a human reviewer to judge broader German wording quality
- Alternatives considered:
  - proceed directly to human review and let the reviewer catch the interpolation bugs
  - broaden German response realism or add new customer utterance data
  - use an LLM or provider to rewrite German responses
- Consequences:
  - only German interpolation/template handling and German campaign fixture field shapes are changed
  - PROD-046C adds guard cases and validator checks for known malformed German interpolation classes
  - false-positive unknown/generic counts are reported separately from positive required-boundary counts
  - retrieval, providers, LLMs, private data, payment collection, contract signing, voice playback, public demo polish, and production runtime promotion remain blocked

### DEC-100 - Add German wording-quality gate before human policy review

- Date: 2026-05-11
- Status: accepted
- Decision: create `PROD-046B-german-response-wording-quality-pass` before PROD-046 human review to remove internal-policy-sounding German customer-facing response text while keeping PROD-046A routing intact.
- Why:
  - PROD-046A proved German intent routing and false-positive behavior, but routing correctness does not prove that the German agent wording is customer-facing
  - terms such as `sale-ready`, `Support-Warteschlange`, `Kündigungs-Warteschlange`, `freigegebener Spezialistenweg`, and `sichere Passungsfrage` expose implementation language to customers
  - Tarik cannot personally judge final German wording quality, so the project needs a deterministic wording-risk pass before human/product review
- Alternatives considered:
  - proceed directly to human review with the PROD-046A wording
  - broaden German phrase triggers or call-control behavior
  - use an LLM or provider to rewrite German responses
- Consequences:
  - only German localized responses and German campaign fixture wording are changed
  - PROD-046B records before/after examples and banned-term counts
  - English PROD-045 and German PROD-046A regressions must keep passing
  - retrieval, providers, LLMs, private data, payment collection, contract signing, voice playback, public demo polish, and production runtime promotion remain blocked

### DEC-099 - Add German naturalized regression before human policy review

- Date: 2026-05-11
- Status: accepted
- Decision: create `PROD-046A-german-naturalized-policy-regression` as a sub-checkpoint before human review to prove the PROD-045 runtime-policy surface on natural German de-DE utterances.
- Why:
  - PROD-045 passed English regression, but German runtime behavior was not proven
  - literal translations would not test real German phone-call phrasing
  - German false-positive cases are needed so phrase matching does not over-trigger cancellation, scam, support, security, provider, or payment routes
- Alternatives considered:
  - proceed directly to PROD-046 human review
  - translate the English PROD-045 cases literally
  - defer German until voice playback work
- Consequences:
  - narrow German phrase triggers and localized responses are added to the deterministic runtime policy surface
  - English PROD-045 regression must keep passing
  - retrieval, provider calls, LLMs, private data, payment collection, contract signing, voice playback, public demo polish, and production runtime promotion remain blocked

### DEC-098 - Apply targeted core sales-policy changes only after evaluator hardening

- Date: 2026-05-11
- Status: accepted
- Decision: create `PROD-045-core-sales-policy-regression-rerun` to harden required-action evaluation and apply the PROD-044 justified runtime-policy updates behind deterministic regression cases.
- Why:
  - PROD-044 exposed that generic clarification could incorrectly pass required-boundary moves
  - direct-answer, channel-boundary, payment-safety, support/cancellation, specialist-handoff, provider-gap, review-summary, and sale-ready cases need explicit deterministic checks
  - reusable sales-agent behavior must still be driven by campaign-approved facts rather than hard-coded product claims
- Alternatives considered:
  - accept the PROD-044 evaluator as sufficient
  - make broader runtime rewrites
  - enable retrieval or playbook lookup by default
- Consequences:
  - runtime policy behavior changes only in the deterministic realtime turn classifier/response map
  - retrieval, providers, LLMs, private data, voice playback, public demo polish, payment collection, contract signing, and production runtime promotion remain blocked
  - the next checkpoint should be human review of the targeted policy change evidence before broader promotion

### DEC-097 - Prepare PROD-044 as review/design before runtime sales-policy edits

- Date: 2026-05-11
- Status: accepted
- Decision: create `PROD-044-core-sales-policy-update` as an offline review/design packet that identifies evidence-backed candidate core sales-policy updates from PROD-043 without applying runtime changes.
- Why:
  - PROD-043 showed the playbook/evaluator can classify customer moves and evaluate single-turn responses, but runtime edits should be gated by deterministic regressions
  - current runtime probes expose targeted gaps such as price-first directness, written-info/email-only boundaries, identity repair, payment/scam safety, support/cancellation routing, specialist handoff boundaries, existing-provider gap isolation, and decision-maker review paths
  - campaign-approved facts are required before the reusable core can safely answer price, identity, support, cancellation, technical, security, coverage, healthcare, or review-summary turns
- Alternatives considered:
  - directly edit `scripts/run_realtime_turn_simulation.py`
  - enable retrieval-backed playbook guidance by default
  - resume synthetic conversation generation
- Consequences:
  - runtime behavior remains unchanged in PROD-044
  - candidate policy updates are explicitly marked `candidate_not_applied`
  - blocked updates and required campaign-fact guards are now visible in generated review artifacts
  - next checkpoint should apply only selected policy changes behind deterministic regression tests

### DEC-096 - Add offline PROD-043 playbook adapter before runtime policy changes

- Date: 2026-05-11
- Status: accepted
- Decision: create `PROD-043-sales-playbook-runtime-adapter` as an offline checkpoint that consumes PROD-042 playbook/evaluation artifacts for deterministic single-turn classification, playbook retrieval, and agent-response evaluation before any core runtime policy update.
- Why:
  - PROD-042 created reusable turn-level rules, but those rules needed an adapter/evaluator layer before they could justify runtime behavior changes
  - the project should test rule satisfaction offline without generating another synthetic conversation simulator
  - retrieval, provider calls, LLM judging, transcript copying, and runtime modification remain out of scope
- Alternatives considered:
  - directly modify the core sales agent from PROD-042 rules
  - build another multi-turn customer simulator
  - enable retrieval-backed guidance by default
- Consequences:
  - PROD-043 produces only single-turn classifier, retrieval, and evaluation artifacts plus a review surface
  - PROD-042 remains the source playbook layer and is not regenerated by PROD-043
  - PROD-044 becomes the earliest checkpoint where targeted core sales-policy changes may be considered
  - runtime behavior, retrieval defaults, provider usage, and LLM usage remain unchanged

### DEC-095 - Enforce tactic integrity and move-specific deterministic gates in PROD-042

- Date: 2026-05-10
- Status: accepted
- Decision: keep PROD-042 checkpoint scope unchanged, but harden quality gates by enforcing valid recovery tactic IDs, move-specific playbook/evaluation rules, safe next-best-action behavior after rejection/boundary reactions, explicit unsupported-target tactic flags, and support-count method/limitation disclosure.
- Why:
  - generic playbook/evaluation output could pass while recommending tactically unsafe or weak sequences
  - invalid recovery tactic IDs (`next_step_close`, `brevity_reset`) broke reference integrity
  - support counts needed explicit wording to avoid overclaiming source certainty
- Alternatives considered:
  - redesign the checkpoint
  - add synthetic conversations to prove rule quality
  - remove unsupported tactics from taxonomy entirely
- Consequences:
  - PROD-042 remains offline, deterministic, and non-runtime
  - unsupported target tactics are preserved but explicitly flagged and counted
  - validator now blocks unsafe rejection/boundary NBA entries and non-specific evaluation rule sets
  - support-count semantics are now explicit in result/report/review artifacts

### DEC-094 - Shift from synthetic scenario expansion to turn-level playbook extraction

- Date: 2026-05-10
- Status: accepted
- Decision: create `PROD-042-callcenteren-turn-pattern-playbook` as a new checkpoint that extracts leakage-safe, deterministic turn-level sales patterns from raw CallCenterEN zip aggregates plus existing abstract checkpoints, instead of continuing synthetic scenario generation in PROD-041A.
- Why:
  - synthetic conversation expansion produced diminishing realism value for this phase
  - the next useful evidence is reusable turn-level customer-move/tactic/reaction/state/failure/recovery structure
  - runtime and retrieval defaults must remain unchanged while stronger offline intelligence is prepared
- Alternatives considered:
  - continue repairing/expanding PROD-041A dialogues
  - add another synthetic simulator lane
  - use LLM judging or provider calls for pattern scoring
- Consequences:
  - PROD-042 outputs only abstract pattern artifacts and a review surface; no synthetic trace scripts are generated
  - raw transcript text and source-sequence reuse remain blocked
  - coverage gaps are reported explicitly instead of hallucinating unsupported categories
  - next checkpoint becomes `PROD-043-sales-playbook-runtime-adapter` (offline first, no runtime promotion)

### DEC-093 - Add agent reactivity gates to PROD-041A

- Date: 2026-05-10
- Status: accepted
- Decision: PROD-041A must validate agent reactivity in addition to customer reactivity. Every post-opening agent turn records the immediately previous customer text, deterministic customer intent tags, reactivity tags, intent-addressing status, repetition status, new-information status, progression status, looping-question status, and ignored-input status.
- Why:
  - the interactive simulator could still produce long traces where the customer changed but the agent repeated the same broad response
  - repeated agent answers can make safe closes look earned when the agent actually ignored the latest customer input
  - human review needs to inspect why the agent response was considered reactive, not just why the customer responded
- Alternatives considered:
  - add more banned phrases
  - add more scripted customer pushback
  - accept the current local sales-agent harness as contextual despite repeated stage responses
- Consequences:
  - validator gates now require `0` repeated agent answers, `0` ignored customer inputs, `0` looping questions, and `0` false safe closes
  - repeated or ignored agent behavior would reduce customer trust/patience and can force rejection instead of a positive terminal outcome
  - the current local sales-agent harness is still called, but the checkpoint truthfully records it as unavailable for final contextual text because it is single-turn/stage-classified
  - the review surface exposes agent reactivity metadata per exchange and trace-level reactivity counters

### DEC-092 - Rewrite PROD-041A as interactive conditional customer simulation

- Date: 2026-05-10
- Status: accepted
- Decision: Rewrite `PROD-041A-conditional-scenario-diversity-expansion` around interactive conditional customer simulation rather than fixed scripted dialogue.
- Why:
  - static three-exchange scripts did not test whether customer behavior changes in response to what the agent actually says
  - the checkpoint needs seeded variations, variable conversation lengths, customer state transitions, branch policies, and terminal policies before human review
  - the final review surface should show generated traces after the current local sales-agent turn harness runs against the simulator
- Alternatives considered:
  - patch more phrases in the fixed script generator
  - expand beyond 40 scenarios
  - use LLM scoring or provider calls
- Consequences:
  - `customer_reaction_policy_bank.json` is now the core scenario-behavior artifact
  - `interactive_scenario_profiles.json` stores persona, state, hidden objections, branch policies, seeds, terminal policies, and safety boundaries, not full scripts
  - `interaction_traces.json` stores `120` generated traces from `40` profiles x `3` seeds
  - every customer response records selected `reaction_rule_ids`, prior `agent_action_tags`, and customer state before/after
  - PROD-041A remains offline, deterministic, no-provider, no-LLM, no transcript-copying, and no runtime promotion
  - the next checkpoint remains `PROD-041-conditional-simulation-review`

### DEC-091 - Repair PROD-041A with recipe-grounded concrete scenario frames only

- Date: 2026-05-10
- Status: accepted
- Decision: Keep PROD-041A at exactly 40 scenarios and repair dialogue generation by inserting a leakage-safe abstract recipe layer (`scenario_recipes.json`) before concrete fictional frames (`concrete_scenario_frames.json`) and spoken traces.
- Why:
  - scenario labels plus concern-text scaffolding were still producing unnatural, evaluator-like dialogue
  - human review needs concrete real-world context per scenario without transcript text, source sequences, names, provider names, or dataset-specific phrasing
  - the fix target is realism quality, not checkpoint expansion
- Alternatives considered:
  - add more scenarios
  - add LLM judging for realism
  - leave frame metadata out of visible review artifacts
- Consequences:
  - recipes may cite only abstract source pattern IDs and generalized call-center structures
  - `spoken_trace_authoring` must treat scenario frames as semantic inputs only, not strings to inject into speech
  - every trace must reference one unique `scenario_frame_id`
  - every trace must reference one unique `recipe_id`
  - validator now enforces frame-quality gates, banned phrase checks, bridge-repeat limits, short-response and challenge coverage, and frame-context usage
  - PROD-041A remains offline, deterministic, leakage-safe, and locked as the diversity checkpoint
  - the next checkpoint remains `PROD-041-conditional-simulation-review`

### DEC-090 - Complete PROD-041 human review without expanding PROD-041A

- Date: 2026-05-10
- Status: accepted
- Decision: Complete `PROD-041-conditional-simulation-review` as a human realism review over the locked `PROD-041A-conditional-scenario-diversity-expansion` traces, without expanding or regenerating PROD-041A.
- Why:
  - PROD-041A already satisfies the structural diversity and safety coverage needed for the scenario-diversity checkpoint
  - the next useful evidence is manual realism judgment, not another scenario-generation pass
  - voice playback and demo use need targeted customer-turn rewrites where safe-close outcomes do not yet feel earned
- Alternatives considered:
  - continue expanding PROD-041A with more scenarios
  - unblock voice playback directly from the structurally valid PROD-041A packet
  - rewrite PROD-041A in place
- Consequences:
  - PROD-041A stays offline, deterministic, and locked as the diversity checkpoint
  - PROD-041 records that remaining deterministic phrasing is acceptable for offline review only
  - voice playback, scenario branching, public demo polish, runtime defaults, provider calls, customer data, payment handling, and production promotion remain blocked
  - any future voice/demo readiness work should rewrite selected customer turns in a separate targeted checkpoint

### DEC-089 - Add PROD-041A before the PROD-041 human review

- Date: 2026-05-10
- Status: accepted
- Decision: Insert `PROD-041A-conditional-scenario-diversity-expansion` before the existing `PROD-041-conditional-simulation-review`.
- Why:
  - the PROD-040 simulator proved conditional customer responses, but the human review needs broader coverage than eight calls
  - the next evidence should cover mixed B2B/B2C scenarios, diverse openings, terminal outcomes, objections, emotions, and strategy requirements
  - strategy and emotion scoring must stay deterministic and offline for this checkpoint rather than relying on LLM judging
- Alternatives considered:
  - proceed directly to PROD-041 using only the PROD-040 eight-call packet
  - expand directly into voice playback or public demo polish
  - use LLM-based judging for strategy and emotion handling
- Consequences:
  - PROD-041A creates a 40-call offline review packet with one curated scenario label per scenario
  - PROD-041 remains the human review checkpoint after the expanded traces exist
  - provider calls, live runtime defaults, retrieval defaults, composer-hook defaults, customer data, payment handling, and production promotion remain blocked

### DEC-088 - Keep PROD-040 as the CallCenterEN-conditioned customer simulator

- Date: 2026-05-10
- Status: accepted
- Decision: Replace the simple hardened-trace surface rerun with a conditional customer simulator where every customer response is driven by the immediately preceding agent answer and grounded in abstract CallCenterEN pattern IDs.
- Why:
  - Tarik's review found that better one-line customer phrasing was not enough; the customer must react to what the agent actually says
  - CallCenterEN should inform interaction patterns without copying real transcript text into generated scenarios or runtime prompts
  - the demo needs full conversations that end by customer acceptance or rejection, not isolated question-answer snippets
- Alternatives considered:
  - only rebuild the PROD-037 surface with PROD-039 hardened lines
  - add more fixed one-line scenarios
  - use raw transcript wording directly as customer replies
- Consequences:
  - PROD-040 uses PROD-013/PROD-014 abstract CallCenterEN pattern banks and keeps raw transcript text out of artifacts
  - every turn records agent answer signals, customer response condition, state delta, and pattern basis
  - the next checkpoint is `PROD-041-conditional-simulation-review`
  - voice playback, public demo polish, retrieval defaults, composer-hook defaults, customer data, payment handling, and production promotion remain blocked

### DEC-087 - Keep PROD-039 as the customer-realism hardening checkpoint

- Date: 2026-05-10
- Status: accepted
- Decision: Improve the simulated customer phrasing on the same fixed calls while preserving agent answers, decision snapshots, safety flags, and terminal outcomes.
- Why:
  - PROD-038 rejected the conversation content because customers sounded artificial and over-cooperative
  - changing only customer phrasing creates a clean experiment: same cases, one editable surface, clear before/after comparison
  - preserving agent answers and decision traces prevents the project from hiding runtime behavior changes inside a simulator realism fix
- Alternatives considered:
  - add more call seeds before fixing realism
  - add voice playback to the weak customer lines
  - rewrite the agent answers together with the customer simulator
- Consequences:
  - the next checkpoint is `PROD-040-customer-realism-demo-surface-rerun`
  - voice playback and public demo polish remain blocked until the hardened traces are reviewed in the actual demo surface
  - provider calls, live runtime defaults, retrieval defaults, composer-hook defaults, customer data, payment handling, and production promotion remain blocked

### DEC-086 - Keep PROD-038 as the customer-realism rejection gate

- Date: 2026-05-10
- Status: accepted
- Decision: Accept the local trace surface structure but reject the current conversation content because the customer responses are too artificial for a credible sales-agent demo.
- Why:
  - Tarik's review found that no realistic customer would talk like the current examples
  - the root issue is in the deterministic customer simulator, where responses are templated state transitions rather than natural buyer speech
  - moving to voice playback or public demo polish would amplify the weakness instead of fixing it
- Alternatives considered:
  - polish the UI first
  - add voice playback to make the same weak responses sound better
  - add more seeds before improving response realism
- Consequences:
  - the next checkpoint is `PROD-039-customer-realism-simulator-hardening`
  - voice playback, scenario branching, more seeds, and public demo polish stay blocked
  - provider calls, live runtime defaults, retrieval defaults, composer-hook defaults, customer data, payment handling, and production promotion remain blocked

### DEC-085 - Keep PROD-037 as a local synthetic trace replay surface

- Date: 2026-05-10
- Status: accepted
- Decision: Build the first local demo as a static synthetic trace replay surface, not as a live customer runtime or provider-backed demo.
- Why:
  - PROD-037 exposes `8` selectable calls and `14` selectable turns from the accepted PROD-036 readiness packet
  - cold openings, exact customer text, exact agent answers, customer follow-up responses, decision snapshots, state transitions, safety flags, and terminal outcomes are visible in one browser-openable artifact
  - static HTML is enough for Tarik's immediate inspection workflow and avoids unnecessary server, provider, or runtime-promotion risk
- Alternatives considered:
  - start a local web server for the demo
  - add voice playback before reviewing the text trace surface
  - build a customer-facing demo from the same evidence
- Consequences:
  - the next checkpoint is `PROD-038-local-demo-surface-review`
  - voice playback, scenario branching, more call seeds, and public demo polish remain later decisions
  - provider calls, live runtime defaults, retrieval defaults, composer-hook defaults, customer data, payment handling, and production promotion remain blocked

### DEC-084 - Keep PROD-036 as the local interactive demo readiness gate

- Date: 2026-05-10
- Status: accepted
- Decision: Treat the aligned PROD-035 traces as ready for a local synthetic trace demo surface, while keeping live/customer/provider promotion blocked.
- Why:
  - PROD-036 reviews `8` aligned calls and `14` turns with demo-ready calls `8` and demo blocker count `0`
  - exact customer text, exact agent answers, decision process, state transitions, terminal outcomes, safety flags, and cold openings are all visible
  - decision snapshot mismatches are `0`, unknown-objection decisions are `0`, hard failures are `0`, payment collection count is `0`, unsupported claim count is `0`, and leakage findings are `0`
  - a local replayable trace surface directly answers Tarik's need to inspect the exact question, exact answer, and decision process
- Alternatives considered:
  - build a live demo immediately
  - keep reviewing static reports without a UI
  - wait for voice/provider integration before creating any demo surface
- Consequences:
  - the next checkpoint is `PROD-037-local-interactive-trace-demo-surface`
  - the demo must stay local and synthetic until a separate promotion gate exists
  - provider calls, live runtime defaults, retrieval defaults, composer-hook defaults, customer data, payment handling, and production promotion remain blocked

### DEC-083 - Keep PROD-035 as the opt-in runtime decision-trace alignment fix

- Date: 2026-05-10
- Status: accepted
- Decision: Add an opt-in decision-trace alignment path that corrects logged runtime decision snapshots without changing the accepted PROD-033 spoken answers or global runtime defaults.
- Why:
  - PROD-034 showed the simulator mechanics were fixed but the visible decision process still had decision snapshot mismatches `13` and unknown-objection decisions `6`
  - PROD-035 clears those review blockers with decision snapshot mismatches after `0` and unknown-objection decisions after `0`
  - spoken answer changed count is `0`, customer response changed count is `0`, and terminal outcome changed count is `0`
  - keeping the alignment opt-in avoids rewriting older checkpoint evidence or silently changing all runtime traces before the next review
- Alternatives considered:
  - change guarded response decision traces globally by default
  - rerun and overwrite PROD-033/PROD-034
  - leave the trace mismatch for demo review notes only
- Consequences:
  - the next checkpoint is `PROD-036-interactive-demo-readiness-review`
  - PROD-035 can be used as the clean decision-trace evidence for demo readiness review
  - provider calls, live runtime defaults, retrieval defaults, composer-hook defaults, customer data, payment handling, and production promotion remain blocked

### DEC-082 - Keep PROD-034 as the post-fix review gate

- Date: 2026-05-10
- Status: accepted
- Decision: Treat PROD-034 as the review gate that accepts the PROD-033 simulator mechanics and routes the next work to runtime decision-trace alignment, not full demo review yet.
- Why:
  - the cold-opening and outcome-driven termination fixes stayed clean: cold opening fix passed `true`, outcome-driven termination passed `true`, fixed turn limit used `false`, loop guard triggered `false`, and max-turn terminal count `0`
  - callback conversion, repeated agent answers, and repeated customer messages remain `0`
  - safety and grounding stayed clean with hard failures `0`, payment collection count `0`, unsupported claim count `0`, leakage findings `0`, and product grounding issues `0`
  - the visible decision trace is still misleading: decision snapshot mismatches are `13`, and unknown-objection decisions are `6`
- Alternatives considered:
  - move straight into local interactive demo review
  - rerun PROD-033 with looser turn generation
  - fix product facts despite product grounding issue count `0`
- Consequences:
  - the next checkpoint is `PROD-035-runtime-decision-trace-alignment`
  - PROD-033 evidence should remain intact and not be rewritten
  - provider calls, live runtime changes, retrieval defaults, composer-hook defaults, customer data, payment handling, and production promotion remain blocked

### DEC-081 - Keep PROD-033 as the cold-opening and outcome-driven termination fix

- Date: 2026-05-10
- Status: accepted
- Decision: Expand the PROD-033 simulator fix so calls start with real outbound cold-call entrances and end only by customer acceptance or rejection, not by a fixed turn target.
- Why:
  - Tarik identified two realism failures: repeated answers and conversations starting midstream instead of from cold-call entrances
  - the fixed simulator starts all `8` calls with greeting, identity disclosure, company disclosure, reason for call, and permission to continue
  - all calls end by customer decision, with fixed turn limit used `false`, loop guard triggered `false`, and max-turn terminal count `0`
  - the fix removes the PROD-032 simulator blockers: callback converted to sale-ready `0`, repeated agent answers `0`, and repeated customer messages `0`
- Alternatives considered:
  - only fix termination loops and leave cold-call openings for a later checkpoint
  - keep a fixed four-turn minimum for consistent benchmark length
  - treat callback acceptance as equivalent to accepting the deal
- Consequences:
  - the next checkpoint is `PROD-034-interactive-post-fix-review`
  - post-fix review should judge whether the cleaner simulator is strong enough for runtime-policy alignment work
  - provider calls, live runtime changes, retrieval defaults, composer-hook defaults, customer data, payment handling, and production promotion remain blocked

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
