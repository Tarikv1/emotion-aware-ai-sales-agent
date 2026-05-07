# RAG-015 Source-Mapping Batches

RAG-015 organizes the remaining source-mapping review work. Runtime retrieval remains disabled.

## Summary

- Source-mapping groups: `43`
- Source-mapping chunks: `58`
- High-impact groups: `3`
- Medium groups: `6`
- Singleton groups: `34`
- Candidate source suggestion groups: `6`
- Candidate source suggestions: `7`
- Latent quote follow-ups after source mapping: `21`
- Cleanup decisions applied now: `0`
- Source-mapping blockers resolved now: `0`
- Source-mapping blockers remaining: `58`
- Auto-promoted chunks: `0`
- Runtime retrieval enabled: `False`
- Chunk import enabled: `False`

## Priority Batches

| Batch | Groups | Chunks | Latent quote follow-ups | Objective |
| --- | ---: | ---: | ---: | --- |
| `batch_1_high_impact_groups` | `3` | `12` | `3` | Review larger source-title groups first because one source decision can unblock multiple chunks. |
| `batch_2_medium_groups` | `6` | `12` | `6` | Review two-chunk groups after larger groups to reduce blocker count efficiently. |
| `batch_3_suggested_singletons` | `6` | `6` | `3` | Review singleton chunks with candidate source suggestions before unsuggested singletons. |
| `batch_4_unsuggested_singletons` | `28` | `28` | `9` | Manually map or create source metadata for singleton chunks without source suggestions. |

## Source-Mapping Review Groups

| Batch | Source title | Chunks | Suggestions | Latent quote follow-ups |
| --- | --- | ---: | ---: | ---: |
| `batch_1_high_impact_groups` | Discovery Masterclass: Everything You Need to Run a Perfect Discovery Call | `5` | `0` | `0` |
| `batch_1_high_impact_groups` | Never Split The Difference / Chris Voss Summary Cheat-Sheet | `4` | `0` | `0` |
| `batch_1_high_impact_groups` | Social Influence Dialogue Systems | `3` | `0` | `3` |
| `batch_2_medium_groups` | 24 Techniques for Closing the Sale | `2` | `0` | `0` |
| `batch_2_medium_groups` | Einwandbehandlung im Verkauf (zu teuer, keine Zeit & Co.) (\#derLÖSER) | `2` | `0` | `2` |
| `batch_2_medium_groups` | Master B2B Sales Negotiation in 46 Minutes | `2` | `0` | `0` |
| `batch_2_medium_groups` | Never Split the Difference | `2` | `0` | `0` |
| `batch_2_medium_groups` | Telefonakquise - Der Leitfaden / Kaltakquise (\#derLÖSER) | `2` | `0` | `2` |
| `batch_2_medium_groups` | Telefonakquise-Leitfaden: 11 Vorlagen, Beispiele (Pipedrive) | `2` | `0` | `2` |
| `batch_3_suggested_singletons` | Cognism Cold Calling Hub - Frida Ottosson | `1` | `1` | `1` |
| `batch_3_suggested_singletons` | Elite Sales Performance | `1` | `1` | `0` |
| `batch_3_suggested_singletons` | Josh Braun - Knowledge Gap | `1` | `1` | `1` |
| `batch_3_suggested_singletons` | MELD: A Multimodal Multi-Party Dataset for Emotion Recognition... | `1` | `1` | `1` |
| `batch_3_suggested_singletons` | Pipedrive: Consultative Selling | `1` | `1` | `0` |
| `batch_3_suggested_singletons` | Voss Transcript | `1` | `2` | `0` |
| `batch_4_unsuggested_singletons` | 10 Sales Training Methodologies Compared (2026) / Salesmotion | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | 16 Best Closing Techniques | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | 18 Steps to a Successful Discovery Call \+ Free Discovery Call Checklist | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | 30MPC - Mr. Miyagi Method | `1` | `0` | `1` |
| `batch_4_unsuggested_singletons` | 30MPC Perfect Script Masterclass | `1` | `0` | `1` |
| `batch_4_unsuggested_singletons` | Am TELEFON richtig VERKAUFEN / So geht AKQUISE (Felix Thönnessen) | `1` | `0` | `1` |
| `batch_4_unsuggested_singletons` | Chris Voss - The Decision Lab | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Chris Voss: FBI Hostage Negotiator Teaches Us How to Sell / EP 106 | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Close: 18 Steps to Discovery | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | DailyDialog: A Manually Labelled Multi-turn Dialogue Dataset... | `1` | `0` | `1` |
| `batch_4_unsuggested_singletons` | Four Levers Negotiating | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Getting More | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Getting More by Stuart Diamond: Summary & Notes | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Getting More Summary | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Getting to Yes | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | GoEmotions: A Dataset of Fine-Grained Emotions | `1` | `0` | `1` |
| `batch_4_unsuggested_singletons` | Gong: 8 Things for Discovery | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Grant Cardone - Phone Closing | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | High Ticket Sales in 1 Call | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | How To Close Every Sale (2024) | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Kaltakquise am Telefon - so öffnest du deinen Gesprächspartner [in 4 Schritten] (Thomas Pelzl) | `1` | `0` | `1` |
| `batch_4_unsuggested_singletons` | Kaltakquise Telefon - Der Einstieg - Wie öffne ich den Entscheider? (Lars Krüger) | `1` | `0` | `1` |
| `batch_4_unsuggested_singletons` | Never Split the Difference: 3 SALES Tips (+ examples) | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Precision Cold Calling - Josh Braun | `1` | `0` | `1` |
| `batch_4_unsuggested_singletons` | Salesmotion: 10 Sales Methodologies | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Social Influence Dialogue Systems: A Survey... | `1` | `0` | `1` |
| `batch_4_unsuggested_singletons` | The Upward Spiral | `1` | `0` | `0` |
| `batch_4_unsuggested_singletons` | Ultimate Sales Training | `1` | `0` | `0` |

## Review Rules

- RAG-015 is a batch packet only.
- Human source review is still required before source mapping can be accepted.
- Candidate source suggestions are review hints only and are not auto-applied.
- Larger groups are reviewed first because one source decision can unblock multiple chunks.
- Source mapping may create additional quote-clearance follow-up work.

## Boundaries

- Runtime retrieval remains disabled.
- Chunk import remains disabled.
- No chunks are auto-promoted.
- No source-mapping decisions are applied.
- No provider or NotebookLM API calls are made.
- No private customer data is used.
- No source excerpt text is stored.
- A later runtime integration gate is required before any runtime use.
