# RAG-004 Source Manifest Normalization

This report converts source-title references from NotebookLM report artifacts into stable local source-ID candidates.

Runtime retrieval remains disabled. RAG-004 does not import chunks, call NotebookLM, call providers, or promote any sales knowledge automatically.

## Summary

- Imports folder: `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports`
- Reports scanned: `11`
- Source candidates: `95`
- Source-ID mapping review required: `True`
- Sources missing review metadata: `95`
- Sources without topics: `0`
- Secret-like source titles: `0`
- Runtime retrieval enabled: `False`
- Chunk import enabled: `False`

## Source Candidates

| Source ID | Title | Topics | Type Guess | Language | Review Status |
| --- | --- | --- | --- | --- | --- |
| `rag004-source-001` | 10 Communication Skills That Will Make You Rich!" [Youtube] - Used (Themes: Clarity | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-002` | 10 Speaking Techniques That Made Me A Top 1% Speaker" [Youtube] - Used (Themes: Rule of Three | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-003` | 13 Years of Communication Skills Knowledge in 53 minutes" [Youtube] - Used (Themes: Vocal foundations | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-004` | 2015 World Champion: 'The Power of Words' Mohammed Qahtani, Toastmasters International | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-005` | 3 Powerful Ways To Tell Stories Without Boring People" [Youtube] - Used (Themes: Shortening stories | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-006` | 30 Day Plan to Master Your Communication [Complete Beginner's Guide] + FREE Workbook PDF" [Youtube] - Used (Themes: Non-functional behaviors | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-007` | 30 Minutes to President’s Club | consultative_selling_discovery | needs_review | mixed | needs_human_review |
| `rag004-source-008` | 30MPC (Armon & Nick) | cold_calling | needs_review | mixed | needs_human_review |
| `rag004-source-009` | 33 Minutes Of Communication Skills Advice I Wish I Knew In My 20s" [Youtube] - Used (Themes: Managing conversational anxiety | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-010` | 43 minutes straight of SOLID communication skills advice" [Youtube] - Used (Themes: Melody | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-011` | 5 communication hacks that will dramatically improve your confidence!" [Youtube] - Used (Themes: Deepening questions | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-012` | 5 Communication Secrets That Give You An Unfair Advantage Over Anyone Else" [Youtube] - Used (Themes: Open-ended questions | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-013` | 7 Communication Cheat Codes To Speak Like A Pro!" [Youtube] - Used (Themes: PREP framework | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-014` | 7 emotions + 3 sentiments mapping interactions in video | emotion_recognition_speech_emotion_persuasion_datasets | video_or_transcript | mixed | needs_human_review |
| `rag004-source-015` | 7 POWERFUL Storytelling Secrets to Level Up Your Communication Skills" [Youtube] - Used (Themes: Dialogue play | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-016` | 9 Habits for Clearer Speaking (I Wish I Knew Sooner)" [Youtube] - Used (Themes: Pausing to highlight | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-017` | A Comprehensive Survey on Multi-modal Conversational Emotion Recognition | emotion_recognition_speech_emotion_persuasion_datasets | needs_review | mixed | needs_human_review |
| `rag004-source-018` | Advanced JS | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-019` | Alessia Cara - Here | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-020` | Alex Cattoni | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-021` | Alexander Lyon (Comm Coach) | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-022` | An Introduction to Behavioral Economics | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-023` | Andy Luttrell Transcript | ethical_persuasion_persuasive_dialogue | video_or_transcript | mixed | needs_human_review |
| `rag004-source-024` | BE Hub Concepts | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-025` | Behavioral Science Concepts (BE Hub) | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-026` | BigSpeak | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-027` | Center for Creative Leadership | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-028` | Cognism Hub/Scripts | cold_calling | website_or_blog | mixed | needs_human_review |
| `rag004-source-029` | Cognism Live | cold_calling | website_or_blog | mixed | needs_human_review |
| `rag004-source-030` | Cognitive Dissonance Theory | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-031` | Colleen Stanley (Badger Maps) | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-032` | Communication Is Hard Until You Structure Your Thinking First!" [Youtube] - Used (Themes: 3-2-1 Framework | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-033` | Connor Murray Video | cold_calling | video_or_transcript | mixed | needs_human_review |
| `rag004-source-034` | Datasets - ConvoKit 4.1.1 | emotion_recognition_speech_emotion_persuasion_datasets | needs_review | mixed | needs_human_review |
| `rag004-source-035` | EASY 3-Step Exercise To INSTANTLY Improve Your Articulation!" [Youtube] - Used (Themes: Crisp articulation | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-036` | Extreme Ownership | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-037` | Felix Thönnessen YouTube Transcript | negotiation_german_english_sales_calls_telefonakquise | video_or_transcript | mixed | needs_human_review |
| `rag004-source-038` | Give me 14 minutes | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-039` | Harvard Business (DeSmet) | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-040` | Harvard Gazette (Siegel) | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-041` | How to Build INSTANT Rapport With Strangers!" [Youtube] - Used (Themes: Match | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-042` | How to Speak | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-043` | How to Speak So That People Want to Listen | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-044` | How to Turn That Difficult Conversation You Need to Have on EASY Mode" [Youtube] - Used (Themes: Sandwich technique | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-045` | HubSpot | closing_techniques | website_or_blog | mixed | needs_human_review |
| `rag004-source-046` | HubSpot (Context) | negotiation_german_english_sales_calls_telefonakquise | website_or_blog | mixed | needs_human_review |
| `rag004-source-047` | I'll help you think & speak faster" [Youtube] - Used (Themes: Breath control | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-048` | IAW Website | ethical_persuasion_persuasive_dialogue | website_or_blog | mixed | needs_human_review |
| `rag004-source-049` | Intro to BE | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-050` | Intro to BE (Samson) | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-051` | Jason Bay (Sell Better) | cold_calling | needs_review | mixed | needs_human_review |
| `rag004-source-052` | Jeff Shore (5 Min Sales) | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-053` | Jens Löser (#derLÖSER) Transcripts | negotiation_german_english_sales_calls_telefonakquise | video_or_transcript | de | needs_human_review |
| `rag004-source-054` | Josh Braun 30MPC | cold_calling | needs_review | mixed | needs_human_review |
| `rag004-source-055` | Journal of the International Phonetic Association | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-056` | Julian Treasure | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-057` | Lars Krüger YouTube Transcripts | negotiation_german_english_sales_calls_telefonakquise | video_or_transcript | de | needs_human_review |
| `rag004-source-058` | Loss Aversion | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-059` | Marcus Alexander Velazquez | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-060` | Matthew Pollard | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-061` | Mindtools | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-062` | Multi-party Conversational Emotion | emotion_recognition_speech_emotion_persuasion_datasets | needs_review | mixed | needs_human_review |
| `rag004-source-063` | Non-Verbal Communication | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-064` | Pausing/dead air | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-065` | Persuasion (Psychology Today) | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-066` | Persuasion for Good | emotion_recognition_speech_emotion_persuasion_datasets | needs_review | mixed | needs_human_review |
| `rag004-source-067` | Persuasion for Good (arXiv) | ethical_persuasion_persuasive_dialogue | paper_or_reference | mixed | needs_human_review |
| `rag004-source-068` | Persuasion for Good (Paper) | ethical_persuasion_persuasive_dialogue | paper_or_reference | mixed | needs_human_review |
| `rag004-source-069` | Pipedrive Blog | negotiation_german_english_sales_calls_telefonakquise | website_or_blog | mixed | needs_human_review |
| `rag004-source-070` | Psychology Today | emotional_intelligence, ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-071` | Sales Gravy (Jeb Blount Jr.) | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-072` | Sales Introverts (Kyle Asay) | consultative_selling_discovery | needs_review | mixed | needs_human_review |
| `rag004-source-073` | Salesforce | closing_techniques, negotiation_german_english_sales_calls_telefonakquise | needs_review | mixed | needs_human_review |
| `rag004-source-074` | Salesman.com: 5 Questions | consultative_selling_discovery | needs_review | mixed | needs_human_review |
| `rag004-source-075` | Science Of Persuasion (Cialdini) | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-076` | Speak 10X Clearer: Do These 3 Vocal Exercises Every Day" [Youtube] - Used (Themes: Soft palate lifting | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-077` | Speak Better Than 99% of People (Everything You Need To Know)" [Youtube] - Used (Themes: Full vocal range | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-078` | Speech Emotion Recognition via Multi-Level Cross-Modal Distillation | emotion_recognition_speech_emotion_persuasion_datasets | needs_review | mixed | needs_human_review |
| `rag004-source-079` | Stanford Encyclopedia (Noggle) | ethical_persuasion_persuasive_dialogue | paper_or_reference | mixed | needs_human_review |
| `rag004-source-080` | Sunstein (IAW) | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-081` | Team Cialdini | ethical_persuasion_persuasive_dialogue | needs_review | mixed | needs_human_review |
| `rag004-source-082` | The Art of Effective Communication | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-083` | The Ethics of Manipulation (Stanford) | ethical_persuasion_persuasive_dialogue | paper_or_reference | mixed | needs_human_review |
| `rag004-source-084` | The Four Dimensions of Tone of Voice - NN/G | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-085` | The Impact of Tone of Voice on Users' Brand Perception (Nielsen Norman Group UX research) - NN/G | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-086` | The Only Video You Need To Fix Your Communication Skills" [Youtube] - Used (Themes: Influence diamond | active_listening_human_like_sales_communication, consultative_selling_discovery, emotional_intelligence, ethical_persuasion_persuasive_dialogue, objection_handling, speech_tone_prosody_human_like_voice_behavior | video_or_transcript | mixed | needs_human_review |
| `rag004-source-087` | Think Fast, Talk Smart: Communication Techniques | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-088` | Thomas Pelzl YouTube Transcript | negotiation_german_english_sales_calls_telefonakquise | video_or_transcript | mixed | needs_human_review |
| `rag004-source-089` | Timo Sven Bauer | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-090` | Timo Sven Bauer YouTube Transcripts | negotiation_german_english_sales_calls_telefonakquise | video_or_transcript | mixed | needs_human_review |
| `rag004-source-091` | Toastmasters International -Public Speaking Tips | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-092` | Tony Robbins | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-093` | Trillium BCG (Science of Selling) | emotional_intelligence | needs_review | mixed | needs_human_review |
| `rag004-source-094` | Verbal Communication Skills | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |
| `rag004-source-095` | Your Body Language May Shape Who You Are | speech_tone_prosody_human_like_voice_behavior | needs_review | mixed | needs_human_review |

## Human Review Needed

- Fill URL, author/channel, source type, language, rights status, and citation metadata where available.
- Merge any duplicate titles that the heuristic did not recognize.
- Delete any rows that are not real sources.
- Keep source excerpts out of the manifest; this file is metadata-only.
- Use reviewed source IDs in the later chunk-normalization checkpoint.

## Boundaries

- No private/customer data is allowed in this manifest.
- No raw source text is stored.
- No NotebookLM API or provider call is made.
- No runtime retrieval or chunk import is enabled.
