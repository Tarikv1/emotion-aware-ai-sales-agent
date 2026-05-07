# RAG-005 Chunk Normalization

This report converts NotebookLM report appendices into metadata-only chunk candidates for human review.

Runtime retrieval remains disabled. RAG-005 does not import chunks into product memory, call providers, or make the sales agent use any extracted tactic.

## Summary

- Reports scanned: `11`
- Chunk candidates: `121`
- Mapped chunks: `58`
- Unmapped chunks: `63`
- Chunks requiring review: `121`
- Chunks with source excerpts flagged: `80`
- Chunks requiring topic mapping review: `8`
- Source excerpt text stored: `False`
- Runtime retrieval enabled: `False`
- Chunk import enabled: `False`

## Chunk Candidates

| Candidate ID | Topic | Source IDs | Principle | Review Flags |
| --- | --- | --- | --- | --- |
| `rag005-chunk-001` | cold_calling | needs_source_mapping | JD-Based Tailored Permission | source_mapping_required, quote_review_required |
| `rag005-chunk-002` | cold_calling | needs_source_mapping | Arman Farokh EQ Rule (Immediate Exit) | source_mapping_required, quote_review_required |
| `rag005-chunk-003` | cold_calling | needs_source_mapping | Mirroring Pain | source_mapping_required, quote_review_required |
| `rag005-chunk-004` | cold_calling | needs_source_mapping | Honesty Anchor | source_mapping_required, quote_review_required |
| `rag005-chunk-005` | cold_calling | needs_source_mapping | Rep Talk-Time Dominance | source_mapping_required, quote_review_required |
| `rag005-chunk-006` | cold_calling | needs_source_mapping | Triple Confirmation | source_mapping_required, quote_review_required |
| `rag005-chunk-007` | cold_calling | needs_source_mapping | Shine a Light Presupposition | source_mapping_required, quote_review_required |
| `rag005-chunk-008` | cold_calling | needs_source_mapping | Categorical Classification | source_mapping_required, quote_review_required |
| `rag005-chunk-009` | closing_techniques | needs_source_mapping | The Strategic Bridge | source_mapping_required |
| `rag005-chunk-010` | closing_techniques | needs_source_mapping | The Yes or No Ultimatum | source_mapping_required |
| `rag005-chunk-011` | closing_techniques | needs_source_mapping | The Demonstration Close | source_mapping_required |
| `rag005-chunk-012` | closing_techniques | needs_source_mapping | The "Ding Ding" Signal Response | source_mapping_required |
| `rag005-chunk-013` | closing_techniques | needs_source_mapping | The Power of Silence | source_mapping_required |
| `rag005-chunk-014` | closing_techniques | needs_source_mapping | Postural Skillsets & Weight | source_mapping_required |
| `rag005-chunk-015` | closing_techniques | needs_source_mapping | The Approach Close | source_mapping_required |
| `rag005-chunk-016` | closing_techniques | needs_source_mapping | The Takeaway Close | source_mapping_required |
| `rag005-chunk-017` | objection_handling | rag004-source-086 | Yes, And" over "Yes, But | quote_review_required |
| `rag005-chunk-018` | consultative_selling_discovery | rag004-source-012 | Reflecting Emotions (Listening with the Heart) | quote_review_required |
| `rag005-chunk-019` | speech_tone_prosody_human_like_voice_behavior | rag004-source-002 | Purposeful Pausing for Highlight | quote_review_required |
| `rag005-chunk-020` | ethical_persuasion_persuasive_dialogue | rag004-source-016 | Declarative Statements vs. Rambling | quote_review_required |
| `rag005-chunk-021` | speech_tone_prosody_human_like_voice_behavior | rag004-source-076 | Soft Palate Lift for Warm Volume | quote_review_required |
| `rag005-chunk-022` | active_listening_human_like_sales_communication | rag004-source-002 | The Empathy Echo | quote_review_required |
| `rag005-chunk-023` | speech_tone_prosody_human_like_voice_behavior | rag004-source-002 | The Power Drop (Downward Inflection) | quote_review_required |
| `rag005-chunk-024` | ethical_persuasion_persuasive_dialogue | rag004-source-013 | The PREP Framework | quote_review_required |
| `rag005-chunk-025` | objection_handling | rag004-source-032 | The 3-2-1 Framework (Distilling Thoughts) | quote_review_required |
| `rag005-chunk-026` | emotional_intelligence | rag004-source-041 | Match, Mirror, and Lead | quote_review_required |
| `rag005-chunk-027` | speech_tone_prosody_human_like_voice_behavior | rag004-source-003 | Modulating Rate of Speech | quote_review_required |
| `rag005-chunk-028` | consultative_selling_discovery | needs_source_mapping | The 11-14 Question Rule | source_mapping_required |
| `rag005-chunk-029` | consultative_selling_discovery | rag004-source-007 | Level 3 Executive Problem (PR Risk) | human_review_required |
| `rag005-chunk-030` | consultative_selling_discovery | rag004-source-072 | The 'So What' Gap | human_review_required |
| `rag005-chunk-031` | consultative_selling_discovery | rag004-source-074 | Deadline Qualification | human_review_required |
| `rag005-chunk-032` | consultative_selling_discovery | needs_source_mapping | The Astute Observation / 90-Second Rule | source_mapping_required |
| `rag005-chunk-033` | consultative_selling_discovery | needs_source_mapping | The Humbling Disclaimer | source_mapping_required |
| `rag005-chunk-034` | consultative_selling_discovery | needs_source_mapping | Quantifying the Pain (Cost of Inaction) | source_mapping_required |
| `rag005-chunk-035` | consultative_selling_discovery | needs_source_mapping | PPO Agenda Setting (Purpose, Plan, Outcome) | source_mapping_required |
| `rag005-chunk-036` | consultative_selling_discovery | rag004-source-073 | Cadence Detection | human_review_required |
| `rag005-chunk-037` | consultative_selling_discovery | needs_source_mapping | Need-Payoff Formulation (SPIN Selling) | source_mapping_required |
| `rag005-chunk-038` | consultative_selling_discovery | needs_source_mapping | Active Listening: The Pause | source_mapping_required |
| `rag005-chunk-039` | consultative_selling_discovery | needs_source_mapping | The Challenger Sale (Xerox Case) | source_mapping_required |
| `rag005-chunk-040` | consultative_selling_discovery | needs_source_mapping | The 41% Camera Rule | source_mapping_required |
| `rag005-chunk-041` | consultative_selling_discovery | needs_source_mapping | Push-Pull Questioning | source_mapping_required |
| `rag005-chunk-042` | consultative_selling_discovery | needs_source_mapping | Active Listening Playbacks | source_mapping_required |
| `rag005-chunk-043` | active_listening_human_like_sales_communication | needs_source_mapping | The 7-38-55 Rule | source_mapping_required |
| `rag005-chunk-044` | active_listening_human_like_sales_communication | needs_source_mapping | Late-Night FM DJ Voice | source_mapping_required |
| `rag005-chunk-045` | active_listening_human_like_sales_communication | needs_source_mapping | Earned Case Studies | source_mapping_required, topic_mapping_required |
| `rag005-chunk-046` | active_listening_human_like_sales_communication | needs_source_mapping | The Dog Listening Metaphor | source_mapping_required |
| `rag005-chunk-047` | active_listening_human_like_sales_communication | needs_source_mapping | Affect Labeling (Tactical Empathy) | source_mapping_required |
| `rag005-chunk-048` | active_listening_human_like_sales_communication | needs_source_mapping | No-Oriented Logic | source_mapping_required, topic_mapping_required |
| `rag005-chunk-049` | active_listening_human_like_sales_communication | needs_source_mapping | The 'That's Right' Objective | source_mapping_required, topic_mapping_required |
| `rag005-chunk-050` | active_listening_human_like_sales_communication | needs_source_mapping | Exception Discovery | source_mapping_required, topic_mapping_required |
| `rag005-chunk-051` | active_listening_human_like_sales_communication | needs_source_mapping | The Four-Question Discovery Loop | source_mapping_required |
| `rag005-chunk-052` | active_listening_human_like_sales_communication | needs_source_mapping | Acoustic Triggers | source_mapping_required, topic_mapping_required |
| `rag005-chunk-053` | active_listening_human_like_sales_communication | needs_source_mapping | Mirroring for Elaboration | source_mapping_required |
| `rag005-chunk-054` | active_listening_human_like_sales_communication | needs_source_mapping | Do Not Interrupt | source_mapping_required |
| `rag005-chunk-055` | active_listening_human_like_sales_communication | needs_source_mapping | Dynamic Silence | source_mapping_required |
| `rag005-chunk-056` | active_listening_human_like_sales_communication | needs_source_mapping | Mutual Gains | source_mapping_required, topic_mapping_required |
| `rag005-chunk-057` | active_listening_human_like_sales_communication | needs_source_mapping | Amygdala Defusing | source_mapping_required, topic_mapping_required |
| `rag005-chunk-058` | active_listening_human_like_sales_communication | needs_source_mapping | Positive and Playful Voice | source_mapping_required |
| `rag005-chunk-059` | active_listening_human_like_sales_communication | needs_source_mapping | Eliciting "That's Right" via Summarization | source_mapping_required |
| `rag005-chunk-060` | active_listening_human_like_sales_communication | needs_source_mapping | Cultural Benchmark Variance | source_mapping_required, topic_mapping_required |
| `rag005-chunk-061` | negotiation_german_english_sales_calls_telefonakquise | needs_source_mapping | The 4-Step Fact-Benefit Hook. 1\. Undeniable fact, 2\. Peer problem, 3\. Solution idea, 4\. Micro-co | source_mapping_required, quote_review_required |
| `rag005-chunk-062` | negotiation_german_english_sales_calls_telefonakquise | needs_source_mapping | Decision Maker vs. Responsible. Ask for the person who makes decisions ('Entscheider'), not who is r | source_mapping_required, quote_review_required |
| `rag005-chunk-063` | negotiation_german_english_sales_calls_telefonakquise | rag004-source-089 | The Visual 'Loom' Follow-up Strategy. Using a folksy proverb to pivot from a verbal rejection to sen | quote_review_required |
| `rag005-chunk-064` | negotiation_german_english_sales_calls_telefonakquise | needs_source_mapping | Gatekeeper Bypass - Asking for Help. Treat the gatekeeper as an ally by admitting you need their hel | source_mapping_required, quote_review_required |
| `rag005-chunk-065` | negotiation_german_english_sales_calls_telefonakquise | needs_source_mapping | Future vs. Past Proverb. Responding to 'We already have a partner' with a philosophical challenge ab | source_mapping_required, quote_review_required |
| `rag005-chunk-066` | negotiation_german_english_sales_calls_telefonakquise | needs_source_mapping | Colleague & Appreciation (Loben bringt nach oben). Reference an internal colleague or system to warm | source_mapping_required, quote_review_required |
| `rag005-chunk-067` | negotiation_german_english_sales_calls_telefonakquise | needs_source_mapping | Calendar Week (KW) Trick. Referencing a specific Calendar Week (Kalenderwoche) forces the prospect t | source_mapping_required, quote_review_required |
| `rag005-chunk-068` | negotiation_german_english_sales_calls_telefonakquise | needs_source_mapping | Meta-Communication. Stepping out of the sales role to address the communication dynamic itself when  | source_mapping_required, quote_review_required |
| `rag005-chunk-069` | negotiation_german_english_sales_calls_telefonakquise | needs_source_mapping | Optimized Voicemail Structure. Keep it concise, state the exact reason, ask for a callback, and repe | source_mapping_required, quote_review_required |
| `rag005-chunk-070` | negotiation_german_english_sales_calls_telefonakquise | needs_source_mapping | Pull Strategy via Root Cause. Discover the underlying inability (e.g., cannot swim) rather than pitc | source_mapping_required, quote_review_required |
| `rag005-chunk-071` | ethical_persuasion_persuasive_dialogue | rag004-source-022 | Sunk Cost Fallacy & Mental Accounting | quote_review_required |
| `rag005-chunk-072` | ethical_persuasion_persuasive_dialogue | rag004-source-066 | Personalized Persuasion (Demographic & Psychological Adaptation) | quote_review_required |
| `rag005-chunk-073` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Consistency | quote_review_required |
| `rag005-chunk-074` | ethical_persuasion_persuasive_dialogue | rag004-source-083 | Guardrail: Non-Coercive Pressure & Trickery | quote_review_required |
| `rag005-chunk-075` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Scarcity & Loss Aversion | quote_review_required |
| `rag005-chunk-076` | ethical_persuasion_persuasive_dialogue | rag004-source-022 | Decoy Effect / Choice Architecture | quote_review_required |
| `rag005-chunk-077` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Reciprocity | quote_review_required |
| `rag005-chunk-078` | ethical_persuasion_persuasive_dialogue | rag004-source-022 | Choice Overload Prevention | quote_review_required |
| `rag005-chunk-079` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Consensus (Social Proof) | quote_review_required |
| `rag005-chunk-080` | ethical_persuasion_persuasive_dialogue | rag004-source-030 | Cognitive Dissonance | quote_review_required |
| `rag005-chunk-081` | ethical_persuasion_persuasive_dialogue | needs_source_mapping | Status Quo Bias & Inertia | source_mapping_required, quote_review_required |
| `rag005-chunk-082` | ethical_persuasion_persuasive_dialogue | rag004-source-065 | Autonomy Reminder | quote_review_required |
| `rag005-chunk-083` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Liking (Similarity & Mutual Goals) | quote_review_required |
| `rag005-chunk-084` | ethical_persuasion_persuasive_dialogue | needs_source_mapping | Endowment Effect & IKEA Effect | source_mapping_required, quote_review_required |
| `rag005-chunk-085` | ethical_persuasion_persuasive_dialogue | rag004-source-065 | Optimal Number of Claims (Rule of Three) | quote_review_required |
| `rag005-chunk-086` | ethical_persuasion_persuasive_dialogue | rag004-source-022 | Anchoring | quote_review_required |
| `rag005-chunk-087` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Authority (Third-Party Introduction) | quote_review_required |
| `rag005-chunk-088` | ethical_persuasion_persuasive_dialogue | rag004-source-065 | Emotional Self-Reflection | quote_review_required |
| `rag005-chunk-089` | ethical_persuasion_persuasive_dialogue | rag004-source-083 | Ethical Guardrails | quote_review_required |
| `rag005-chunk-090` | speech_tone_prosody_human_like_voice_behavior | rag004-source-042 | Start with an empowerment promise and use verbal punctuation to keep the audience engaged. | quote_review_required |
| `rag005-chunk-091` | speech_tone_prosody_human_like_voice_behavior | rag004-source-087 | Adopt a 'Yes, and...' mindset to treat objections as opportunities rather than threats. | quote_review_required |
| `rag005-chunk-092` | speech_tone_prosody_human_like_voice_behavior | rag004-source-036 | Take extreme ownership of communication failures or errors without making excuses. | quote_review_required |
| `rag005-chunk-093` | speech_tone_prosody_human_like_voice_behavior | rag004-source-042 | Build a 'fence' around a concept to prevent confusion with competitors. | quote_review_required |
| `rag005-chunk-094` | speech_tone_prosody_human_like_voice_behavior | rag004-source-085 | Avoid high-risk humor; it can easily alienate users and obscure the core message. | quote_review_required |
| `rag005-chunk-095` | speech_tone_prosody_human_like_voice_behavior | rag004-source-087 | Use inclusive, conversational language to reduce psychological distance. | quote_review_required |
| `rag005-chunk-096` | speech_tone_prosody_human_like_voice_behavior | rag004-source-042 | Tolerate extended silence (up to 7 seconds) after asking a high-value question. | quote_review_required |
| `rag005-chunk-097` | speech_tone_prosody_human_like_voice_behavior | rag004-source-004 | Frame corrections and directives positively to preserve the prospect's pride. | quote_review_required |
| `rag005-chunk-098` | speech_tone_prosody_human_like_voice_behavior | rag004-source-063, rag004-source-094 | Trust non-verbal paralinguistics (tone/pitch) over verbal content if there is a mismatch. | quote_review_required |
| `rag005-chunk-099` | speech_tone_prosody_human_like_voice_behavior | rag004-source-085 | Prioritize trustworthiness over friendliness; use a casual, conversational, and moderately enthusias | quote_review_required |
| `rag005-chunk-100` | speech_tone_prosody_human_like_voice_behavior | rag004-source-087 | Use structured frameworks like 'Problem-Solution-Benefit' or 'What-So What-Now What' for spontaneous | quote_review_required |
| `rag005-chunk-101` | speech_tone_prosody_human_like_voice_behavior | rag004-source-042, rag004-source-043, rag004-source-056 | Optimize the vocal toolbox (Register, Timbre, Prosody, Pace, Pitch, Volume) to convey authority and  | quote_review_required |
| `rag005-chunk-102` | speech_tone_prosody_human_like_voice_behavior | rag004-source-059, rag004-source-082 | Simplicity is key; avoid over-speaking and explicitly define terms to prevent misunderstandings. | quote_review_required |
| `rag005-chunk-103` | speech_tone_prosody_human_like_voice_behavior | rag004-source-042 | End interactions with a strong summary of contributions, not a weak 'thank you'. | quote_review_required |
| `rag005-chunk-104` | speech_tone_prosody_human_like_voice_behavior | rag004-source-042 | Cycle on the subject to ensure message retention. | quote_review_required |
| `rag005-chunk-105` | speech_tone_prosody_human_like_voice_behavior | rag004-source-087 | Bypass rehearsed objections or guardedness by shifting the dynamic and asking the prospect for advic | quote_review_required |
| `rag005-chunk-106` | emotion_recognition_speech_emotion_persuasion_datasets | rag004-source-078 | Cross-Modal Emotion Distillation | quote_review_required |
| `rag005-chunk-107` | emotion_recognition_speech_emotion_persuasion_datasets | rag004-source-017 | Multimodal Disambiguation | quote_review_required |
| `rag005-chunk-108` | emotion_recognition_speech_emotion_persuasion_datasets | rag004-source-034 | Antisocial Derailment Warning | quote_review_required |
| `rag005-chunk-109` | emotion_recognition_speech_emotion_persuasion_datasets | rag004-source-034 | Multi-Issue Bargaining Trade-offs | quote_review_required |
| `rag005-chunk-110` | emotion_recognition_speech_emotion_persuasion_datasets | needs_source_mapping | Dual Intent and Emotion Co-Tracking | source_mapping_required, quote_review_required |
| `rag005-chunk-111` | emotion_recognition_speech_emotion_persuasion_datasets | rag004-source-034 | Perceived Truthfulness Optimization | quote_review_required |
| `rag005-chunk-112` | emotion_recognition_speech_emotion_persuasion_datasets | rag004-source-017 | Incomplete Modality Graceful Degradation | quote_review_required |
| `rag005-chunk-113` | emotion_recognition_speech_emotion_persuasion_datasets | rag004-source-034 | Argumentation Delta Tracking | quote_review_required |
| `rag005-chunk-114` | emotion_recognition_speech_emotion_persuasion_datasets | needs_source_mapping | Dialogue Act Look-Ahead (Opponent Modeling) | source_mapping_required, quote_review_required |
| `rag005-chunk-115` | emotion_recognition_speech_emotion_persuasion_datasets | rag004-source-066 | Personalized Persuasion Strategy Selection | quote_review_required |
| `rag005-chunk-116` | emotion_recognition_speech_emotion_persuasion_datasets | needs_source_mapping | Task and Social Content Layering | source_mapping_required, quote_review_required |
| `rag005-chunk-117` | emotion_recognition_speech_emotion_persuasion_datasets | needs_source_mapping | Politeness Mitigation and Face Acts | source_mapping_required, quote_review_required |
| `rag005-chunk-118` | emotion_recognition_speech_emotion_persuasion_datasets | needs_source_mapping | Transparent and Ethical Social Influence | source_mapping_required, quote_review_required |
| `rag005-chunk-119` | emotion_recognition_speech_emotion_persuasion_datasets | rag004-source-017 | Low-Level Acoustic Feature Extraction | quote_review_required |
| `rag005-chunk-120` | emotion_recognition_speech_emotion_persuasion_datasets | needs_source_mapping | Sequential Emotion Shift Tracking | source_mapping_required, quote_review_required |
| `rag005-chunk-121` | emotion_recognition_speech_emotion_persuasion_datasets | needs_source_mapping | Fine-Grained Emotion Categorization | source_mapping_required, quote_review_required |

## Human Review Needed

- Verify source mappings against the RAG-004 manifest.
- Remove unsafe, manipulative, non-compliant, or product-inappropriate tactics.
- Review any chunk with `quote_review_required`; source excerpt text is intentionally not copied forward.
- Convert useful chunks into the final RAG schema only in a later checkpoint.

## Boundaries

- No runtime retrieval is enabled.
- No chunk import into product memory is enabled.
- No provider/API calls are made.
- No source excerpt text is stored in RAG-005 outputs.
