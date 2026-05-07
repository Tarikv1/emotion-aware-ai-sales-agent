# RAG-006 Chunk Review Packet

This report turns RAG-005 candidates into human review queues before any runtime knowledge promotion.

Runtime retrieval remains disabled. No chunks are promoted, imported, or used by the sales agent in this checkpoint.

## Summary

- Chunk candidates reviewed: `121`
- Source-title review groups: `46`
- Chunks needing source mapping: `63`
- Chunks needing topic mapping: `8`
- Chunks needing quote review: `80`
- First-slice review candidates: `20`
- Auto-promoted chunks: `0`
- Runtime retrieval enabled: `False`
- Chunk import enabled: `False`

## Source Mapping Queue

| Source Title | Chunk Count | Chunk IDs | Suggestions |
| --- | ---: | --- | --- |
| Discovery Masterclass: Everything You Need to Run a Perfect Discovery Call | 5 | `rag005-chunk-032`, `rag005-chunk-033`, `rag005-chunk-035`, `rag005-chunk-041`, `rag005-chunk-042` | create_or_review_source |
| Never Split The Difference / Chris Voss Summary Cheat-Sheet | 4 | `rag005-chunk-043`, `rag005-chunk-044`, `rag005-chunk-055`, `rag005-chunk-059` | create_or_review_source |
| Social Influence Dialogue Systems | 3 | `rag005-chunk-114`, `rag005-chunk-116`, `rag005-chunk-118` | create_or_review_source |
| 24 Techniques for Closing the Sale | 2 | `rag005-chunk-011`, `rag005-chunk-015` | create_or_review_source |
| Behavioral Science Concepts - BehavioralEconomics.com | The BE Hub | 2 | `rag005-chunk-081`, `rag005-chunk-084` | rag004-source-025 (0.666) |
| Einwandbehandlung im Verkauf (zu teuer, keine Zeit & Co.) (\#derLÖSER) | 2 | `rag005-chunk-065`, `rag005-chunk-068` | create_or_review_source |
| Master B2B Sales Negotiation in 46 Minutes | 2 | `rag005-chunk-046`, `rag005-chunk-051` | create_or_review_source |
| Never Split the Difference | 2 | `rag005-chunk-049`, `rag005-chunk-052` | create_or_review_source |
| Sell Better - Jason Bay | 2 | `rag005-chunk-005`, `rag005-chunk-006` | rag004-source-051 (0.689) |
| Telefonakquise - Der Leitfaden | Kaltakquise (\#derLÖSER) | 2 | `rag005-chunk-062`, `rag005-chunk-067` | create_or_review_source |
| Telefonakquise-Leitfaden: 11 Vorlagen, Beispiele (Pipedrive) | 2 | `rag005-chunk-064`, `rag005-chunk-069` | create_or_review_source |
| 10 Sales Training Methodologies Compared (2026) | Salesmotion | 1 | `rag005-chunk-037` | create_or_review_source |
| 16 Best Closing Techniques | 1 | `rag005-chunk-016` | create_or_review_source |
| 18 Steps to a Successful Discovery Call \+ Free Discovery Call Checklist | 1 | `rag005-chunk-034` | create_or_review_source |
| 30MPC - Mr. Miyagi Method | 1 | `rag005-chunk-002` | create_or_review_source |
| 30MPC Perfect Script Masterclass | 1 | `rag005-chunk-001` | create_or_review_source |
| Am TELEFON richtig VERKAUFEN | So geht AKQUISE (Felix Thönnessen) | 1 | `rag005-chunk-070` | create_or_review_source |
| Chris Voss - The Decision Lab | 1 | `rag005-chunk-047` | create_or_review_source |
| Chris Voss: FBI Hostage Negotiator Teaches Us How to Sell | EP 106 | 1 | `rag005-chunk-058` | create_or_review_source |
| Close: 18 Steps to Discovery | 1 | `rag005-chunk-040` | create_or_review_source |
| Cognism Cold Calling Hub - Frida Ottosson | 1 | `rag005-chunk-004` | rag004-source-028 (0.47) |
| Cognism Cold Calling Scripts | 1 | `rag005-chunk-003` | rag004-source-028 (0.587) |
| DailyDialog: A Manually Labelled Multi-turn Dialogue Dataset... | 1 | `rag005-chunk-110` | create_or_review_source |
| Elite Sales Performance | 1 | `rag005-chunk-013` | rag004-source-073 (0.452) |
| Four Levers Negotiating | 1 | `rag005-chunk-045` | create_or_review_source |
| Getting More | 1 | `rag005-chunk-050` | create_or_review_source |
| Getting More by Stuart Diamond: Summary & Notes | 1 | `rag005-chunk-054` | create_or_review_source |
| Getting More Summary | 1 | `rag005-chunk-060` | create_or_review_source |
| Getting to Yes | 1 | `rag005-chunk-056` | create_or_review_source |
| GoEmotions: A Dataset of Fine-Grained Emotions | 1 | `rag005-chunk-121` | create_or_review_source |
| Gong: 8 Things for Discovery | 1 | `rag005-chunk-028` | create_or_review_source |
| Grant Cardone - Phone Closing | 1 | `rag005-chunk-010` | create_or_review_source |
| High Ticket Sales in 1 Call | 1 | `rag005-chunk-009` | create_or_review_source |
| How To Close Every Sale (2024) | 1 | `rag005-chunk-012` | create_or_review_source |
| Josh Braun - Knowledge Gap | 1 | `rag005-chunk-007` | rag004-source-054 (0.52) |
| Kaltakquise am Telefon - so öffnest du deinen Gesprächspartner [in 4 Schritten] (Thomas Pelzl) | 1 | `rag005-chunk-061` | create_or_review_source |
| Kaltakquise Telefon - Der Einstieg - Wie öffne ich den Entscheider? (Lars Krüger) | 1 | `rag005-chunk-066` | create_or_review_source |
| MELD: A Multimodal Multi-Party Dataset for Emotion Recognition... | 1 | `rag005-chunk-120` | rag004-source-017 (0.47) |
| Never Split the Difference: 3 SALES Tips (+ examples) | 1 | `rag005-chunk-053` | create_or_review_source |
| Pipedrive: Consultative Selling | 1 | `rag005-chunk-038` | rag004-source-069 (0.451) |
| Precision Cold Calling - Josh Braun | 1 | `rag005-chunk-008` | create_or_review_source |
| Salesmotion: 10 Sales Methodologies | 1 | `rag005-chunk-039` | create_or_review_source |
| Social Influence Dialogue Systems: A Survey... | 1 | `rag005-chunk-117` | create_or_review_source |
| The Upward Spiral | 1 | `rag005-chunk-057` | create_or_review_source |
| Ultimate Sales Training | 1 | `rag005-chunk-014` | create_or_review_source |
| Voss Transcript | 1 | `rag005-chunk-048` | rag004-source-023 (0.464), rag004-source-088 (0.46) |

## Topic Mapping Queue

| Chunk ID | Original Topic | Current Topic IDs | Principle |
| --- | --- | --- | --- |
| `rag005-chunk-045` | ethics_guardrails | active_listening_human_like_sales_communication | Earned Case Studies |
| `rag005-chunk-048` | no_oriented_questions | active_listening_human_like_sales_communication | No-Oriented Logic |
| `rag005-chunk-049` | behavioral_markers | active_listening_human_like_sales_communication | The 'That's Right' Objective |
| `rag005-chunk-050` | tactic_countermeasure | active_listening_human_like_sales_communication | Exception Discovery |
| `rag005-chunk-052` | delivery | active_listening_human_like_sales_communication | Acoustic Triggers |
| `rag005-chunk-056` | principled_negotiation | active_listening_human_like_sales_communication | Mutual Gains |
| `rag005-chunk-057` | neuroscience | active_listening_human_like_sales_communication | Amygdala Defusing |
| `rag005-chunk-060` | cross_cultural_logic | active_listening_human_like_sales_communication | Cultural Benchmark Variance |

## First-Slice Review Candidates

| Chunk ID | Topic IDs | Source IDs | Principle |
| --- | --- | --- | --- |
| `rag005-chunk-017` | objection_handling | rag004-source-086 | Yes, And" over "Yes, But |
| `rag005-chunk-025` | objection_handling | rag004-source-032 | The 3-2-1 Framework (Distilling Thoughts) |
| `rag005-chunk-020` | ethical_persuasion_persuasive_dialogue | rag004-source-016 | Declarative Statements vs. Rambling |
| `rag005-chunk-024` | ethical_persuasion_persuasive_dialogue | rag004-source-013 | The PREP Framework |
| `rag005-chunk-071` | ethical_persuasion_persuasive_dialogue | rag004-source-022 | Sunk Cost Fallacy & Mental Accounting |
| `rag005-chunk-072` | ethical_persuasion_persuasive_dialogue | rag004-source-066 | Personalized Persuasion (Demographic & Psychological Adaptation) |
| `rag005-chunk-073` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Consistency |
| `rag005-chunk-074` | ethical_persuasion_persuasive_dialogue | rag004-source-083 | Guardrail: Non-Coercive Pressure & Trickery |
| `rag005-chunk-075` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Scarcity & Loss Aversion |
| `rag005-chunk-076` | ethical_persuasion_persuasive_dialogue | rag004-source-022 | Decoy Effect / Choice Architecture |
| `rag005-chunk-077` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Reciprocity |
| `rag005-chunk-078` | ethical_persuasion_persuasive_dialogue | rag004-source-022 | Choice Overload Prevention |
| `rag005-chunk-079` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Consensus (Social Proof) |
| `rag005-chunk-080` | ethical_persuasion_persuasive_dialogue | rag004-source-030 | Cognitive Dissonance |
| `rag005-chunk-082` | ethical_persuasion_persuasive_dialogue | rag004-source-065 | Autonomy Reminder |
| `rag005-chunk-083` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Liking (Similarity & Mutual Goals) |
| `rag005-chunk-085` | ethical_persuasion_persuasive_dialogue | rag004-source-065 | Optimal Number of Claims (Rule of Three) |
| `rag005-chunk-086` | ethical_persuasion_persuasive_dialogue | rag004-source-022 | Anchoring |
| `rag005-chunk-087` | ethical_persuasion_persuasive_dialogue | rag004-source-075 | Authority (Third-Party Introduction) |
| `rag005-chunk-088` | ethical_persuasion_persuasive_dialogue | rag004-source-065 | Emotional Self-Reflection |

## Review Rules

- Treat source suggestions as review hints only, never automatic mappings.
- Resolve source mappings before promotion.
- Resolve topic mapping flags before promotion.
- Review quote flags and replace source-excerpt dependence with paraphrased, cited knowledge.
- Keep campaign guardrails above all RAG suggestions.

## Boundaries

- Runtime retrieval remains disabled.
- No chunks are promoted.
- No source excerpt text is stored.
- No provider or NotebookLM API calls are made.
