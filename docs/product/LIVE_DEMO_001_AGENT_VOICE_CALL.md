# LIVE-DEMO-001 Agent Voice Call

## Purpose

LIVE-DEMO-001 is a supervised local demo where Tarik talks to the repository-owned sales agent and hears the response through ElevenLabs TTS.

It is not an ElevenLabs agent, not an UltraVox agent, and not a production runtime promotion.

## Architecture

```text
browser microphone
-> browser SpeechRecognition transcript
-> local Python server
-> repo-owned guarded runtime agent
-> RESP-002 voice delivery
-> RESP-003 ElevenLabs TTS
-> browser audio playback
```

The conversation brain stays in this repository. ElevenLabs receives only the final TTS text when the server is started with `--live-tts` and environment gates are present.

The demo now exposes the audible runtime-upgrade path instead of only recording it in private metadata. RESP-003 selects the provider-shaped TTS input from RESP-002 when it is safe, and the browser fallback voice uses the same shaped text after stripping provider markup. That means dry-run fallback speech can still carry bounded fillers, contractions, pacing/naturalization, and low-pressure delivery wording instead of speaking the raw `final_response`.

## Interaction Model

The browser page starts in the English B2B software campaign by default (`campaign-prod-005-b2b-software`) and exposes the campaign selector for controlled comparison with the German B2C campaigns.

`Start Conversation` now makes the repo-owned agent speak first through a runtime-owned `agent-open` turn before browser speech recognition starts. The opening uses the campaign `caller_identity` and `target_account_context`: `Hi, this is Maya calling from Northstar Workflow Labs, the team behind RouteSignal CRM...` It checks whether Tarik has a minute, says it is looking for the person handling inbound demo follow-up, states the missed-callback/handoff problem, and asks a qualifying sales question. After the agent audio finishes, recognition starts and then restarts after later agent output so Tarik can keep speaking without pressing send for every turn. The manual `Send To Agent` button remains available as a fallback if the browser speech loop is unreliable.

The demo keeps short-answer continuity for the local session. For example, if the agent asks whether the main concern is price, terms, or effort, a follow-up answer like `price` is treated as an answer to that question instead of triggering the same question again.

The local session wrapper also persists resolved focus slots across later turns. If Tarik answers `price`, later turns such as `the price is the problem` stay on price instead of restarting the price/terms/effort choice. The same bounded continuity path handles the generic `price, fit, timing, or exact product details` prompt, longer phrases such as `first let's start with the price`, ASR variants around `reviewing/viewing options is worth my time`, time-pressure follow-ups, and current-provider gap follow-ups.

Repeated resolved-focus turns should advance the conversation instead of replaying the first answer. For example, after the session shifts from price to effort, a later effort turn moves to a concrete effort check instead of repeating the price/terms/effort question or the first effort response.

Continuation phrases after a resolved topic stay inside that topic. For example, after `let's talk about the price first`, follow-ups such as `let's do that`, `explain that`, or `it's about the price` stay in the price path. After switching to product details, follow-ups such as `what does the workflow include` stay in the details path instead of reopening the generic focus menu.

The demo has a session-level anti-loop guard. After a top-level focus menu or price-choice menu has appeared once, the local wrapper must not emit the same menu again in that session. If the one-turn runtime tries to reopen a menu, the wrapper either keeps the active focus, infers a focus from the transcript, or asks for a single concrete follow-up without replaying the menu.

The demo also has a duplicate-response guard. If the next generated answer exactly matches a previous non-terminal answer in the session, the wrapper advances the current focus with a different bounded response instead of replaying the same text.

Explicit topic selections are answered directly. A first turn such as `I want to talk about the price` now enters the price path immediately instead of reopening the old price/terms/effort menu. Demo-specific focus responses are kept short and block old approval-marker phrasing such as `That makes sense`, `focus only on price`, and `we will stay on price`.

Direct campaign answers should not start by echoing the buyer's own topic, plan, or price wording. If the buyer asks about a named plan, a manual-tracking objection, small-team fit, workflow scope, Salesforce, or SOC 2, the answer moves to value, boundary, or next useful fact instead of leading with the same phrase the buyer just said.

The demo should not behave like a spoken FAQ. For basic product, plan, fit, manual-tracking, and workflow-scope turns, the agent gives a compact answer and then asks one diagnostic question that guides discovery toward the buyer's real workflow gap. This implements the project-owned RAG-019/RAG-020/RAG-021 guidance: diagnose before pitching, map value before feature claims, keep one small decision at a time, and preserve the buyer's ability to decline.

After the agent-led opener, weak buyer replies such as `okay` continue qualification instead of waiting for the buyer to drive the call. If the buyer names a gap such as handoffs, the runtime maps that gap to value and asks for a consented short workflow review.

The demo separates product callback language from callback scheduling. If the buyer says callbacks are the problem, or asks `what do you mean by callbacks`, the runtime treats callbacks as follow-up reminders in the inbound-demo workflow. It must not ask for a callback time unless the buyer explicitly says they do not have time, asks to be called back, or gives a time.

Call-context and confusion turns now recover the seller agenda directly. If the buyer says variants of `what do you want exactly`, `you called me`, `what is the next step`, `how short is this workflow review`, `you are wasting time`, `I don't know`, `I don't know what you're talking about`, or a frustration phrase, the runtime must answer that dialogue act with one concrete RouteSignal workflow question. It must not fall back to the generic `price, fit, timing, or exact product details` menu or expose internal anti-loop wording.

If the buyer asks what the previous question meant, the runtime now routes the turn as `previous_question_clarified`. The agent explains the prior sales question in plain terms, keeps the same qualification focus, and asks one clearer version instead of advancing canned qualification copy.

If the buyer asks where the caller is calling from, the runtime now routes the turn as `caller_identity_recalled`. The answer must restate `Maya`, `Northstar Workflow Labs`, and `RouteSignal CRM` directly instead of interpreting the question as price, fit, timing, or product-detail intent.

Short negative replies are treated as ambiguous until the rejected object is clear. If the buyer says only `no`, the runtime routes the turn as `ambiguous_negative_clarified` and asks whether the buyer means now is not a good time or that missed callbacks/handoffs are not an issue. It must not advance into another qualification line or reopen the generic topic menu.

Customer-facing responses must never expose internal repair language. In particular, anti-loop logic must not say `avoid repeating the same question`, `same question`, `candidate_response`, `decision log`, `guardrail`, `internal`, or `runtime`.

The qualification path now protects `sales_context_variety` and `sales_emphasis_priority`. Low-information follow-ups such as `okay`, `tell me more`, `what else should I know`, `why does that matter`, and `how would it help` must produce distinct seller-led responses with campaign context such as inbound demos, owner routing, callback reminders, handoff review, manager visibility, spreadsheet/shared-inbox leakage, or Slack alerts. Voice prosody cues must target problem/value phrases such as `missed callbacks and messy handoffs`, `callback`, `handoff`, `owner`, or `routing`; they must not emphasize greeting text or small talk. The first `agent-open` turn still gets emphasis/pacing cues, but it suppresses filler insertion between the company/product identity and the permission check.

The English B2B software demo now applies a fictional high-fidelity campaign profile from `research/experiments/cases/live-demo-001-fictional-b2b-sales-campaign.json`. The default fictional client is `Northstar Workflow Labs`, the fictional product is `RouteSignal CRM`, and the product position is inbound lead capture, routing, follow-up reminders, handoff review, and team reporting. The profile also carries `caller_identity`, `target_account_context`, and `sales_delivery_guidance` so the live opener, qualification variety, and spoken emphasis are campaign-owned rather than hard-coded demo copy.

The profile keeps the existing demo prices but gives them enough sales substance to answer buyer questions directly. Starter is `$29/month` for lead capture and basic routing. Growth is `$59/month` with priority routing, follow-up reminders, duplicate checks, Slack alerts, and handoff review. The agent should answer normal product, pricing, plan-difference, manual-tracking, small-team-fit, and workflow-scope questions without defaulting to a specialist handoff.

Explicit campaign-depth questions are routed before same-topic duplicate repair. If the buyer moves from price into `what does your product actually do` or `what does the workflow include`, the agent answers from the fictional campaign profile instead of treating the turn as another price follow-up.

Exact integration and security questions stay bounded. The demo can say that the fictional profile supports Salesforce-style or HubSpot-style ownership-routing concepts, but exact object mapping, permissions, and security material require verified review before compatibility or compliance claims. The validator blocks unsupported claims such as guaranteed conversion lift, guaranteed ROI, replacing every CRM, and `SOC 2 certified`.

Browser STT is still browser-dependent. The page now tracks browser ASR confidence when available, sends it in the private turn packet, and avoids auto-submitting obvious transcript fragments such as `it's about the`; those get a short repeat request instead of entering the sales logic.

`LIVE-DEMO-004` makes the browser ASR turn-taking policy explicit. Browser SpeechRecognition is treated as browser-vendor ASR, not true production VAD. Interim results do not auto-submit; the demo waits for a final ASR result, cancels a pending submit when interim speech continues, and waits through a longer pause window before sending the turn to the local agent. This reduces mid-sentence talk-over risk without adding provider ASR or uploading raw microphone audio to the Python server.

The demo now uses a voice turn-state controller for speech flow: `idle`, `listening`, `agent_thinking`, `agent_speaking`, and `paused`. The current browser page is only the first producer of this state; future telephony or WebRTC adapters should emit the same `voice_turn_state` contract instead of introducing transport-specific state names. Recognition is stopped before a turn is sent to the agent, listening is blocked while the agent is thinking or speaking, and listening restarts only after ElevenLabs audio or browser fallback speech ends. The restart delay is `750 ms` so the browser is less likely to capture the tail of the agent's own voice as user speech.

The server also records a local ASR quality gate in each turn packet. Empty transcripts and low-confidence browser ASR below `0.45` are answered with a repeat request instead of being treated as buyer intent. Clear-confidence transcripts still enter the campaign and continuity logic normally. Raw microphone audio still does not upload to the Python server.

The demo runner enables local guarded retrieval only when the existing `RAG-017` runtime knowledge registry is present. Retrieval remains advisory, local, source-traced, and subordinate to campaign facts; protected contexts still block it. The validator now includes an eligible price-worth turn where retrieval changes the guarded response, while session-policy overrides correctly report retrieved advice as not used instead of claiming false influence.

The server now attaches `DIALOGUE-REASONER-004` async enrichment evidence to each private turn packet. This is evidence-only: it fingerprints the already-created customer response, records whether provider enrichment would be eligible, and keeps provider calls, provider text upload, route override, final-response mutation, voice delivery mutation, and `PROD-102` blocked in the live-demo path.

## Source Boundary

The campaign profile is fictional and uses public product pages only as inspiration for realistic SaaS lead-routing patterns. It does not copy real company wording, plan names, customer claims, or brand identity.

Tracked source inspiration:

- Chili Piper lead routing software: `https://info.chilipiper.com/lead-routing-software`
- Calendly Routing: `https://calendly.com/features/routing`
- HubSpot lead scoring: `https://www.hubspot.com/products/lead-scoring`
- LeanData Speed to Lead: `https://www.leandata.com/platform/speed-to-lead/`

## Boundary

- browser ASR may be processed by the browser vendor
- browser ASR is not treated as production VAD
- raw microphone audio is not uploaded to the Python server
- interim ASR results do not auto-submit to the local agent
- browser listening is blocked while the agent is thinking or speaking
- low-confidence ASR is rejected before demo response selection
- local guarded retrieval is demo-wired only when the `RAG-017` registry is present; core runtime retrieval remains default-off outside explicit enablement
- `DIALOGUE-REASONER-004` async enrichment is private evidence only and does not affect spoken responses
- browser fallback voice speaks markup-free RESP-003 TTS input, not raw final response, so audible voice naturalization is preserved without provider calls
- ElevenLabs is TTS only, not the agent
- no provider agent is used
- no durable provider agent is created
- no voice cloning is used
- generated demo turns and audio stay under ignored `data/private/live-demo-001/`
- runtime behavior is not changed
- `PROD-102` stays closed

## Commands

Validate the demo without provider calls:

```powershell
python scripts\validate_live_demo_001_agent_voice_call.py
```

Start the local demo in dry-run mode:

```powershell
python scripts\run_live_demo_001_agent_voice_call.py
```

Start the local demo with ElevenLabs TTS enabled after setting `ELEVENLABS_API_KEY` in the shell and configuring an English voice ID through `ELEVENLABS_VOICE_ID_EN`, `ELEVENLABS_VOICE_ID`, or ignored `runtime/config/local/voice_ids.json`:

```powershell
python scripts\run_live_demo_001_agent_voice_call.py `
  --live-tts `
  --consent-confirmed `
  --timeout-seconds 8
```

Default local URL:

```text
http://127.0.0.1:8781/
```

## Current Status

Prepared and locally validated on `2026-05-18`.

Local validation proved:

- dry-run mode makes no ElevenLabs call
- forced-missing-key live mode makes no ElevenLabs call
- `Start Conversation` routes an `agent-open` turn through runtime-owned sales opening before browser ASR starts
- the agent-led opener says `Maya` is calling from `Northstar Workflow Labs`, `the team behind RouteSignal CRM`, says it is looking for the person handling inbound demo follow-up, states the missed-callback/handoff problem, and asks a qualification question
- weak acknowledgement after the agent-led opener keeps qualification moving instead of waiting for buyer questions
- callback gap mentions such as `it's probably the callbacks` route to product workflow value instead of callback scheduling
- callback clarification questions such as `what do you mean by callbacks` explain callback reminders instead of asking for a callback time
- call-context turns such as `what do you want exactly`, `you called me`, `what is the next step`, `you are wasting time`, and `I don't know what you're talking about` recover the seller agenda instead of reopening the generic topic menu
- buyer clarification requests such as `I did not understand what you asked before` explain the prior question through `previous_question_clarified` instead of advancing canned qualification copy
- caller identity questions such as `where were you calling from again` answer through `caller_identity_recalled` instead of reopening topic menus
- bare negative replies such as `no` clarify timing-vs-problem rejection through `ambiguous_negative_clarified` instead of advancing qualification copy
- internal repair phrases such as `avoid repeating the same question` are blocked from customer-facing responses
- low-information follow-ups preserve `sales_context_variety` and keep the agent guiding with inbound-demo, owner-routing, callback, handoff, reminder, and visibility context
- voice delivery preserves `sales_emphasis_priority` by targeting problem/value phrases instead of greeting text or small talk
- the first opener does not insert a filler between `Northstar Workflow Labs` / `RouteSignal CRM` identity and `Do you have a minute?`
- the default campaign is English B2B software
- the browser page includes automatic conversation mode and a campaign selector
- short follow-up answers such as `price` and `fit` use session continuity instead of repeating the same question
- resolved focus slots persist across later turns inside the local demo session
- observed live phrases such as `start with the price` and `worth my time` are treated as answers or focus shifts
- first-turn explicit topic selections such as `I want to talk about the price` do not reopen old option menus
- demo focus responses block `That makes sense`, focus-restatement loops, and long sentence shapes
- noisy STT variants such as `price star` still resolve to price
- obvious incomplete STT fragments ask for a repeat instead of triggering sales logic
- product, manual-tracking, Growth-plan, small-team-fit, unnecessary-handoff, integration, and security questions use the fictional campaign profile instead of a generic menu
- direct campaign answers avoid leading with the buyer's repeated topic, named plan, or stated price fact
- greetings in stale browser sessions route back to the sales opener instead of the generic topic menu
- direct price, product, plan, fit, manual-tracking, and workflow-scope answers include one seller-led diagnostic next move instead of stopping at an information answer
- when the buyer names a gap after a seller-led price question, the agent maps that gap to value and asks for a consented short workflow review instead of waiting for another question
- product/detail questions asked after price are routed before duplicate price repair
- price questions answer with synthetic demo prices and plan substance instead of internal guardrail/process wording
- the eligible price-worth turn proves local guarded retrieval influence with campaign facts overriding RAG
- browser fallback speech uses markup-free shaped TTS text, so bounded fillers and voice naturalization are audible even without an ElevenLabs file
- live-demo ElevenLabs request voice settings are pinned to one stable profile across mixed turn types to avoid voice-style drift
- low-confidence browser ASR asks for a repeat instead of entering sales logic
- voice turn-state metadata proves the active audio input is not listening while the agent is speaking
- terminal call controls such as callback confirmation stop browser auto-listening after goodbye
- live ElevenLabs TTS failures do not auto-switch to browser fallback voice mid-call; fallback stays manual so the provider failure is visible
- continuation follow-ups such as `let's do that`, `explain that`, and `what does the workflow include` stay inside the resolved topic
- focus menus are allowed at most once per session
- exact answer replay is blocked for non-terminal live-demo answers
- source reuse is tracked as inspiration-only with no copied real-company text
- DIALOGUE-REASONER-004 async enrichment evidence exists but makes no provider call and cannot change `final_response`
- provider-agent use stays false
- voice cloning stays false
- browser audio upload to Python stays false
- runtime behavior stays unchanged
- `PROD-102` stays closed

Live ElevenLabs playback still requires `ELEVENLABS_API_KEY` in the shell.
