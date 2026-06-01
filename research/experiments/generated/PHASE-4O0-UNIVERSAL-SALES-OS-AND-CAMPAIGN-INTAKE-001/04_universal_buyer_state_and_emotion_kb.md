# Universal Buyer State and Emotion KB

## Purpose

This KB maps buyer state and emotion cues to safe conversation adaptations. It supports buyer-state detection and emotion-aware adaptation without adding campaign facts.

## Buyer States

| Buyer state | Signals | Adaptation |
| --- | --- | --- |
| busy | short answers, time pressure, asks to be quick | Use one-sentence value and one yes/no relevance question. |
| skeptical | asks if this is spam, questions source, challenges authority | Use trust repair, truthful identity, and offer a clean exit. |
| curious | asks what it does, asks for examples | Give approved concise detail and ask a discovery question. |
| high_intent | asks pricing, next step, timing, implementation | Move to qualification and approved micro-close. |
| price_sensitive | asks cost early, says too expensive | Follow pricing behavior, anchor value only to approved outcomes. |
| wrong_person | says someone else decides | Ask for approved handoff path or end if none exists. |
| no_fit | outside target, needs unsupported outcome | Disqualify politely and do not force a pitch. |
| partner_dependent | needs co-owner, manager, spouse, procurement | Ask for approved next step that includes the stakeholder. |
| annoyed | impatient, repeats complaint, hostile tone | Shorten, apologize for interruption if appropriate, offer exit. |
| confused | asks what this means, mixed up about offer | Simplify and avoid jargon. |
| stop_requested | says stop, remove me, do not call, not interested | Use stop-request handling and end persuasion. |

## Emotion Cues

| Emotion cue | Typical text cue | Safe response |
| --- | --- | --- |
| irritation | "I'm busy", "why are you calling" | Reduce pressure and ask permission to continue. |
| suspicion | "is this spam", "who are you really" | Truthful identity and trust repair. |
| anxiety | "I don't want to get locked in" | Clarify commitments and forbidden claims. |
| frustration | "we tried this before" | Acknowledge, ask what failed, avoid dismissing prior experience. |
| interest | "how would that work" | Explain approved process and move to discovery. |
| urgency | "we need this soon" | Qualify timing without inventing delivery guarantees. |
| uncertainty | "maybe", "not sure" | Ask one clarifying question. |

## Adaptation Rules

- Lower pressure when negative emotion rises.
- Increase specificity when buyer asks practical questions.
- Use pain-to-value bridge only from stated pain to approved value.
- Use disqualification when the buyer need is outside the campaign boundary.
- Use call control to prevent long monologues.
- Do not expose labels such as buyer_state or emotion_label in buyer-facing speech.
