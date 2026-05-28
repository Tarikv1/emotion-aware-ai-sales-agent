# Speech Realism References

## Purpose

Collect research-backed references for making the AI sales agent sound more human in English and German without turning the voice into a national, regional, or cultural stereotype.

This file is reference-only. Product and engineering rules belong in `docs/product/VOICE_023_SPEECH_REALISM_LAYER.md`.

## Reference Boundary

Use this file for:

- related work
- citation candidates
- source summaries
- thesis limitations
- evaluation ideas

Do not use this file as the runtime rulebook. Runtime behavior should be implemented from the product design doc and validated separately.

Post-May-22 evaluation boundary:

- dry-run text validators can prove response content, guardrails, and side-effect flags, but they cannot prove spoken realism
- live voice realism still requires ASR, TTS, latency, turn-taking, audio playback, and listener-review evidence
- live TTS provider use remains explicit and gated; generic campaign live TTS requires consent plus the dedicated allow flag
- self-serve close language should be voice-ready, which means the agent should not read raw URLs aloud even when the URL is available in metadata or a packet
- public-data simulations should not sound like official vendor representation unless explicitly authorized and sourced

## Design Principle Supported By These Sources

The project should model speech mechanics, not stereotypes.

Allowed research framing:

- language-specific filler inventories
- speech-planning signals
- pause and breath variability
- discourse markers and backchannels
- audible warmth and smile-like prosody
- evaluation of naturalness, trust, and professionalism

Disallowed research framing:

- treating German speakers or English speakers as a personality stereotype
- adding random fillers without linguistic or conversational purpose
- claiming native-like naturalness without listener evaluation
- moving private customer details into speech-style rules

## General Prosody And Social Voice Perception

Cutler, A., Dahan, D., and van Donselaar, W. (1997). "Prosody in the Comprehension of Spoken Language: A Literature Review." Language and Speech, 40(2), 141-201.

- DOI: https://doi.org/10.1177/002383099704000203
- PubMed: https://pubmed.ncbi.nlm.nih.gov/9509577/
- Thesis relevance: supports treating prosody as a comprehension signal for words, syntax, and discourse structure, not just as decoration.
- Limitation: this is a broad comprehension review, not an AI sales-agent evaluation.

Wagner, M., and Watson, D. G. (2010). "Experimental and theoretical advances in prosody: A review." Language and Cognitive Processes, 25(7-9), 905-945.

- DOI: https://doi.org/10.1080/01690961003589492
- PubMed: https://pubmed.ncbi.nlm.nih.gov/22096264/
- Thesis relevance: supports modeling prosodic phrasing and prominence as context-sensitive cues influenced by syntax, semantics, rhythm, pragmatics, complexity, and predictability.
- Limitation: the product should not try to fully solve prosody generation; use it to define bounded runtime cues and evaluation dimensions.

Banse, R., and Scherer, K. R. (1996). "Acoustic profiles in vocal emotion expression." Journal of Personality and Social Psychology, 70(3), 614-636.

- DOI: https://doi.org/10.1037/0022-3514.70.3.614
- PubMed: https://pubmed.ncbi.nlm.nih.gov/8851745/
- Thesis relevance: supports the idea that emotion is communicated through acoustic parameter patterns, not just emotion words.
- Limitation: the study used acted portrayals of emotions; sales-agent emotion should be subtle and professional.

Juslin, P. N., and Laukka, P. (2003). "Communication of Emotions in Vocal Expression and Music Performance: Different Channels, Same Code?" Psychological Bulletin, 129(5), 770-814.

- DOI: https://doi.org/10.1037/0033-2909.129.5.770
- Thesis relevance: supports the broader claim that vocal emotion expression is systematic enough to be evaluated, but still multi-cue and context-sensitive.
- Limitation: use as background for acoustic emotion cues, not as a direct sales-call rulebook.

McAleer, P., Todorov, A., and Belin, P. (2014). "How Do You Say 'Hello'? Personality Impressions from Brief Novel Voices." PLOS ONE, 9(3), e90779.

- DOI: https://doi.org/10.1371/journal.pone.0090779
- PLOS page: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0090779
- Thesis relevance: supports evaluating first-impression voice dimensions such as trust, likeability, warmth, dominance, competence, and confidence.
- Limitation: first impressions from short `hello` clips should not be overgeneralized to long outbound sales calls.

## English Disfluency And Planning Signals

Clark, H. H., and Fox Tree, J. E. (2002). "Using uh and um in spontaneous speaking." Cognition, 84(1), 73-111.

- DOI: https://doi.org/10.1016/S0010-0277(02)00017-3
- Author PDF: https://web.stanford.edu/~clark/2000s/Clark.FoxTree.02.pdf
- Thesis relevance: English `uh` and `um` can be discussed as speech-planning delay signals rather than meaningless noise.
- Limitation: this supports controlled filler use, not blanket insertion of fillers into every response.

Kirjavainen, M., Crible, L., and Beeching, K. (2022). "Can filled pauses be represented as linguistic items? Investigating the effect of exposure on the perception and production of um." Language and Speech, 65(2), 263-289.

- DOI: https://doi.org/10.1177/00238309211011201
- Open-access copy: https://pmc.ncbi.nlm.nih.gov/articles/PMC9014665/
- Thesis relevance: supports treating filled pauses as learned spoken-language items with distributional patterns, not random decorations.
- Limitation: results are about English filled pauses and linguistic representation; they do not directly optimize sales-call TTS placement.

Bortfeld, H., Leon, S. D., Bloom, J. E., Schober, M. F., and Brennan, S. E. (2001). "Disfluency Rates in Conversation: Effects of Age, Relationship, Topic, Role, and Gender." Language and Speech, 44(2), 123-147.

- DOI: https://doi.org/10.1177/00238309010440020101
- Thesis relevance: supports the claim that disfluency rates vary with role, task difficulty, relationship, and planning load. For the product, this means fillers should be context-gated rather than globally randomized.
- Limitation: the study is not sales-specific and does not prescribe exact TTS strings.

Levelt, W. J. M. (1983). "Monitoring and self-repair in speech." Cognition, 14(1), 41-104.

- DOI: https://doi.org/10.1016/0010-0277(83)90026-4
- Thesis relevance: supports treating repair, hesitation, and editing terms as part of speech monitoring rather than simple style decoration.
- Limitation: self-repair evidence should inform repair/reformulation behavior, not justify errors in campaign facts or regulated statements.

Laserna, C. M., Seih, Y.-T., and Pennebaker, J. W. (2014). "Um... Who Like Says You Know: Filler Word Use as a Function of Age, Gender, and Personality." Journal of Language and Social Psychology, 33(3), 328-338.

- DOI: https://doi.org/10.1177/0261927X14526993
- Thesis relevance: separates filled pauses such as `uh` and `um` from discourse markers such as `I mean`, `you know`, and `like`, supporting separate runtime categories.
- Limitation: demographic/personality associations must not become product stereotypes.

## English Discourse Markers And Response Tokens

Bolden, G. B. (2009). "Implementing incipient actions: The discourse marker 'so' in English conversation." Journal of Pragmatics, 41(5), 974-998.

- DOI: https://doi.org/10.1016/j.pragma.2008.10.004
- Thesis relevance: supports `so` as a sequence-launching or agenda-advancing marker, not just a casual filler.
- Limitation: sales usage should be sparse and goal-relevant, especially before qualification or scheduling transitions.

Heritage, J. (1998). "Oh-prefaced responses to inquiry." Language in Society, 27(3), 291-334.

- DOI: https://doi.org/10.1017/S0047404598003017
- Thesis relevance: supports `oh` as a response-preface that can signal a problem with relevance, presupposition, or context. This matters for customer objections and clarification turns.
- Limitation: `oh` should not be used as generic warmth or fake surprise.

Heritage, J. (2015). "Well-prefaced turns in English conversation: A conversation analytic perspective." Journal of Pragmatics, 88, 88-104.

- DOI: https://doi.org/10.1016/j.pragma.2015.08.008
- Thesis relevance: supports turn-initial discourse markers such as `well` as relationship-to-prior-turn signals, especially before responses, topic shifts, or speaker-perspective turns.
- Limitation: `well` is not the same category as `uh`/`um`, and professional sales calls should use it sparingly.

## Filler Placement, Boundaries, And Listener Perception

Swerts, M. G. J. (1998). "Filled pauses as markers of discourse structure." Journal of Pragmatics, 30(4), 485-496.

- DOI: https://doi.org/10.1016/S0378-2166(98)00014-9
- Repository page: https://research.tue.nl/en/publications/filled-pauses-as-markers-of-discourse-structure
- Thesis relevance: supports placing fillers near discourse boundaries and phrase beginnings rather than mechanically inserting them inside already-fluent clauses.
- Limitation: study material is Dutch spontaneous monologue, so it should guide boundary logic without being treated as direct English/German sales-call evidence.

Gosy, M. (2023). "Occurrences and Durations of Filled Pauses in Relation to Words and Silent Pauses in Spontaneous Speech." Languages, 8(1), 79.

- DOI: https://doi.org/10.3390/languages8010079
- URL: https://www.mdpi.com/2226-471X/8/1/79
- Thesis relevance: supports distinguishing filler positions by neighboring words and silent pauses instead of using one generic mid-utterance insertion rule.
- Limitation: the data is Hungarian spontaneous narrative speech, not sales dialogue.

Brennan, S. E., and Williams, M. (1995). "The feeling of another's knowing: Prosody and filled pauses as cues to listeners about the metacognitive states of speakers." Journal of Memory and Language, 34(3), 383-398.

- DOI: https://doi.org/10.1006/jmla.1995.1017
- Thesis relevance: supports the risk that fillers and prosody change perceived knowledge/confidence, which matters for a professional sales agent.
- Limitation: this is a question-answering perception study, not a direct TTS naturalness benchmark.

Kirkland, A., Lameris, H., Szekely, E., and Gustafson, J. (2022). "Where's the uh, hesitation? The interplay between filled pause location, speech rate and fundamental frequency in perception of confidence." Interspeech 2022.

- DOI: https://doi.org/10.21437/Interspeech.2022-10973
- ISCA page: https://www.isca-archive.org/interspeech_2022/kirkland22_interspeech.html
- Thesis relevance: supports evaluating filler placement together with speech rate and pitch because these cues jointly affect perceived confidence.
- Limitation: confidence perception is not the same as sales trust, so listener evaluation remains required.

Dall, R., Tomalin, M., Wester, M., Byrne, W., and King, S. (2014). "Investigating Automatic & Human Filled Pause Insertion for Speech Synthesis." Interspeech 2014.

- University record: https://www.research.ed.ac.uk/en/publications/investigating-automatic-amp-human-filled-pause-insertion-for-spee/
- ISCA archive: https://www.isca-speech.org/archive/interspeech_2014/i14_0051.html
- Thesis relevance: supports the user-observed problem that there are right and wrong filled-pause locations, and that automatic insertion should be evaluated against human placement preferences.
- Limitation: the work is speech-synthesis focused and English-oriented; German placement still needs German-specific validation.

Elmers, M., O'Mahony, J., and Szekely, E. (2023). "Synthesis after a couple PINTs: Investigating the role of pause-internal phonetic particles in speech synthesis and perception." Interspeech 2023.

- DOI: https://doi.org/10.21437/Interspeech.2023-2178
- University record: https://www.research.ed.ac.uk/en/publications/synthesis-after-a-couple-pints-investigating-the-role-of-pause-in/
- Thesis relevance: supports treating breath noises, tongue clicks, and hesitations as pause-internal phonetic particles that can affect perceived certainty.
- Limitation: PINTs can reduce perceived certainty, so the sales agent should use them very lightly and only in freeform thinking moments.

## Turn-Taking Timing And Backchannels

Sacks, H., Schegloff, E. A., and Jefferson, G. (1974). "A simplest systematics for the organization of turn-taking for conversation." Language, 50(4), 696-735.

- DOI: https://doi.org/10.2307/412243
- MPI record: https://www.mpi.nl/publications/item2376846/simplest-systematics-organization-turn-taking-conversation
- Thesis relevance: foundational support for treating turn-taking as locally managed and recipient-sensitive.
- Limitation: this is conversation-analysis theory, not a specific implementation recipe for latency thresholds.

Stivers, T., Enfield, N. J., Brown, P., Englert, C., Hayashi, M., Heinemann, T., Hoymann, G., Rossano, F., de Ruiter, J. P., Yoon, K.-E., and Levinson, S. C. (2009). "Universals and cultural variation in turn-taking in conversation." Proceedings of the National Academy of Sciences, 106(26), 10587-10592.

- DOI: https://doi.org/10.1073/pnas.0903616106
- MPI record: https://www.mpi.nl/publications/item66202/universals-and-cultural-variation-turn-taking-conversation
- Thesis relevance: supports the product latency rule that long silence is unnatural, while language/culture timing differences should be treated as quantitative tuning rather than stereotypes.
- Limitation: the study is ordinary conversation, not outbound sales or synthetic voice.

Levinson, S. C., and Torreira, F. (2015). "Timing in turn-taking and its implications for processing models of language." Frontiers in Psychology, 6, 731.

- DOI: https://doi.org/10.3389/fpsyg.2015.00731
- URL: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.00731/full
- Thesis relevance: supports the architecture choice to produce immediate acknowledgments or short latency fillers while slower reasoning, retrieval, or provider work completes.
- Limitation: does not define the exact threshold for this product; project latency targets still need empirical measurement.

Ward, N., and Tsukahara, W. (2000). "Prosodic features which cue back-channel responses in English and Japanese." Journal of Pragmatics, 32(8), 1177-1207.

- DOI: https://doi.org/10.1016/S0378-2166(99)00109-5
- Thesis relevance: supports treating backchannels as timing/prosody-sensitive listener feedback, not random short phrases.
- Limitation: English/Japanese findings should not be copied directly into German, but the principle of timing/prosody sensitivity is useful.

Heldner, M., and Edlund, J. (2010). "Pauses, gaps and overlaps in conversations." Journal of Phonetics, 38(4), 555-568.

- DOI: https://doi.org/10.1016/j.wocn.2010.08.002
- URL: https://www.sciencedirect.com/science/article/pii/S0095447010000628
- Thesis relevance: supports modeling pauses, gaps, and overlaps as distributions rather than fixed constants.
- Limitation: implementation should still set simple product thresholds before using probabilistic timing models.

Skantze, G. (2021). "Turn-taking in Conversational Systems and Human-Robot Interaction: A Review." Computer Speech & Language, 67, 101178.

- DOI: https://doi.org/10.1016/j.csl.2020.101178
- URL: https://www.sciencedirect.com/science/article/pii/S088523082030111X
- Thesis relevance: directly supports VOICE-026 as a turn-taking/backchannel/prosody layer for conversational systems rather than a text-only filler layer.
- Limitation: covers conversational systems broadly, including multimodal robots; our MVP is voice-only and sales-focused.

Witt, S. M. (2015). "Modeling user response timings in spoken dialog systems." International Journal of Speech Technology, 18, 231-247.

- DOI: https://doi.org/10.1007/s10772-014-9265-1
- Thesis relevance: supports timeout and interruption policies that avoid both long silence and premature interruption.
- Limitation: the project should validate timing with its own browser/provider pipeline and sales-call tasks.

## Speech Entrainment And Adaptation

Pardo, J. S. (2006). "On phonetic convergence during conversational interaction." The Journal of the Acoustical Society of America, 119(4), 2382-2393.

- DOI: https://doi.org/10.1121/1.2178720
- University record: https://digitalcommons.montclair.edu/psychology-facpubs/347/
- Thesis relevance: supports later adaptive speech behavior where the agent may lightly accommodate rate or energy to the customer.
- Limitation: do not mimic accents, identities, or sensitive traits; adaptation should be bounded to comfort, clarity, and timing.

Weise, A., Levitan, S. I., Hirschberg, J., and Levitan, R. (2019). "Individual differences in acoustic-prosodic entrainment in spoken dialogue." Speech Communication, 115, 78-87.

- DOI: https://doi.org/10.1016/j.specom.2019.10.007
- University record: https://cris.biu.ac.il/en/publications/individual-differences-in-acoustic-prosodic-entrainment-in-spoken/
- Thesis relevance: supports treating entrainment as variable and context-sensitive, not a universal rule to copy every customer.
- Limitation: entrainment should be future work after the basic voice pipeline and guardrails are stable.

## Spoken English Corpus Reference

British National Corpus 2014, Spoken BNC2014.

- Corpus page: https://corpora.lancs.ac.uk/bnc2014/
- Related paper: Love, R., Dembry, C., Hardie, A., Brezina, V., and McEnery, T. (2017). "The Spoken BNC2014: designing and building a spoken corpus of everyday conversations." International Journal of Corpus Linguistics, 22(3), 319-344.
- DOI: https://doi.org/10.1075/ijcl.22.3.02lov
- Thesis relevance: useful reference for contemporary spoken English, informal discourse markers, turn-taking, and conversation style.
- Limitation: everyday conversation is not the same as professional sales-call speech.

Switchboard-1 Release 2, Linguistic Data Consortium.

- Corpus page: https://catalog.ldc.upenn.edu/LDC97S62
- DOI: https://doi.org/10.35111/sw3h-rw02
- Thesis relevance: useful future reference for American English telephone conversation, disfluencies, backchannels, interruptions, and speech acts.
- Limitation: LDC license applies; do not copy corpus material into this repo without reviewing terms.

Santa Barbara Corpus of Spoken American English, Linguistic Data Consortium.

- Part I page: https://catalog.ldc.upenn.edu/LDC2000S85
- Thesis relevance: useful future reference for natural American spoken interaction with discourse/prosody relevance.
- Limitation: access/licensing differs by distribution route; examples should not be copied into tracked docs without review.

Buckeye Corpus of Conversational Speech.

- Corpus page: https://buckeyecorpus.osu.edu/
- Related paper: https://doi.org/10.1016/j.specom.2004.09.001
- Thesis relevance: useful future reference for spontaneous American English pronunciation, reductions, and phonetic alignment.
- Limitation: noncommercial and corpus-specific access terms apply.

## Spoken German Corpus Reference

DGD / FOLK: Database for Spoken German and Forschungs- und Lehrkorpus Gesprochenes Deutsch.

- Corpus portal: https://dgd.ids-mannheim.de/DGD2Web/jsp/Welcome.jsp
- Thesis relevance: candidate reference for spontaneous German interaction, German filler particles, backchannels, turn-taking, and pause behavior.
- Access note: DGD requires registration and has usage terms. Do not copy corpus content into this repo unless those terms are reviewed.
- Limitation: corpus access and allowed reuse must be checked before using examples in thesis text.

Deppermann, A. (2013). "Turn-design at turn-beginnings: Multimodal resources to deal with tasks of turn-construction in German." Journal of Pragmatics, 46(1), 91-121.

- DOI: https://doi.org/10.1016/j.pragma.2012.07.010
- Open-access record: https://ids-pub.bsz-bw.de/frontdoor/index/index/docId/8798
- Thesis relevance: supports language-aware turn-beginning design for German interaction instead of copying English turn-start patterns directly.
- Limitation: multimodal conversation analysis informs response design but does not specify exact TTS filler strings.

Deppermann, A., and Helmer, H. (2013). "Zur Grammatik des Verstehens im Gespräch: Inferenzen anzeigen und Handlungskonsequenzen ziehen mit 'also' und 'dann'."

- Bibliographic record: https://ids-pub.bsz-bw.de/frontdoor/index/index/docId/1304
- Thesis relevance: supports using German `also` as a turn-beginning/display-of-understanding resource, not as a direct copy of English `also`.
- Limitation: this informs German boundary placement; it does not mean every German response should start with `also`.

Alm, M. (2004). "The contribution of sentence position: the word 'also' in spoken German." ZAS Papers in Linguistics, 35, 1-14.

- DOI: https://doi.org/10.21248/zaspil.35.2004.219
- URL: https://zaspil.leibniz-zas.de/article/view/219
- Thesis relevance: supports distinguishing German sentence-initial discourse `also` from in-clause adverbial `also`, which matters for avoiding unnatural placement.
- Limitation: informs grammar/discourse placement, not sales persona.

Oloff, F. (2018). "Okay as a neutral acceptance token in German conversation." Lexique, 25, 197-225.

- DOI: https://doi.org/10.54563/lexique.924
- URL: https://www.peren-revues.fr/lexique/924
- Thesis relevance: supports using German `okay` as a neutral acceptance or information-receipt token rather than a direct agreement marker.
- Limitation: because `okay` can signal acceptance without verification, it must be blocked when the customer makes unsafe medical, legal, coverage, or pricing claims.

Golato, A., and Fagyal, Z. (2008). "Comparing Single and Double Sayings of the German Response Token ja and the Role of Prosody: A Conversation Analytic Perspective." Research on Language and Social Interaction, 41(3), 241-270.

- DOI: https://doi.org/10.1080/08351810802237834
- Thesis relevance: supports treating German `ja` and doubled `ja ja` as prosody/function-sensitive tokens rather than generic agreement.
- Limitation: `ja` must not create false agreement with customer misunderstandings or unsafe claims.

Bottcher, M., and Rossi, M. (2025). "The speaker's 'okay' vs. the listener's 'okay': exploring lexical, phonetic, and multimodal variation of backchannels and fluencemes in conversation." Frontiers in Communication, 10.

- DOI: https://doi.org/10.3389/fcomm.2025.1655049
- URL: https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2025.1655049/full
- Thesis relevance: supports separating speaker-side fluencemes from listener-side backchannels in German, even when they share forms such as `ja`, `okay`, and `genau`.
- Limitation: face-to-face German findings need adaptation for voice-only call-center use where visual nods are unavailable.

Paierl, M., Kelterer, A., and Schuppler, B. (2025). "Distribution and Timing of Verbal Backchannels in Conversational Speech: A Quantitative Study." Languages, 10(8), 194.

- DOI: https://doi.org/10.3390/languages10080194
- URL: https://www.mdpi.com/2226-471X/10/8/194
- Thesis relevance: supports German/Austrian-German backchannel timing as dependent on syntax, prosody, and turn-taking function.
- Limitation: Austrian German and dyadic spontaneous conversation are not the same as German outbound sales calls.

Schuppler, B., Hagmueller, M., and Zahrer, A. (2017). "A corpus of read and conversational Austrian German." Speech Communication, 94, 62-74.

- DOI: https://doi.org/10.1016/j.specom.2017.09.003
- URL: https://www.sciencedirect.com/science/article/pii/S0167639317300535
- Thesis relevance: useful future source for comparing read vs conversational German-family speech and prosodic annotation.
- Limitation: Austrian German should not be treated as equivalent to the first German client context.

Kohler, K. J., Peters, B., and Scheffers, M. (2017). "The Kiel Corpus of Spoken German: Read and Spontaneous Speech."

- Corpus page: https://www.isfas.uni-kiel.de/de/linguistik-und-phonetik/smile-if-you-can-see-this/forschung/kiel-corpus/the-kiel-corpus-of-spoken-german-read-and-spontaneous-speech
- Thesis relevance: candidate reference for German read/spontaneous speech, phonetic annotation, and prosody.
- Limitation: access and usage terms must be checked before examples are reused.

## German Filler Particles

Muhlack, B., Trouvain, J., and Jessen, M. (2023). "Distributional and Acoustic Characteristics of Filler Particles in German with Consideration of Forensic-Phonetic Aspects." Languages, 8(2), 100.

- URL: https://www.mdpi.com/2226-471X/8/2/100
- Thesis relevance: supports the idea that German fillers should not simply copy English `uh` and `um`.
- Limitation: filler particles show strong speaker variation; this supports cautious language-specific profiles, not one fixed German speaking style.

Belz, M. (2023). "Defining Filler Particles: A Phonetic Account of the Terminology, Form, and Grammatical Classification of 'Filled Pauses'." Languages, 8(1), 57.

- URL: https://www.mdpi.com/2226-471X/8/1/57
- Thesis relevance: helps define terms such as filler particle, filled pause, hesitation marker, and disfluency.
- Limitation: terminology should be used carefully because not every pause, repair, or hesitation is the same phenomenon.

Belz, M. (2021). "Die Phonetik von äh und ähm: Akustische Variation von Füllpartikeln im Deutschen." Springer.

- DOI: https://doi.org/10.1007/978-3-662-62812-6
- Publisher page: https://link.springer.com/book/10.1007/978-3-662-62812-6
- Thesis relevance: supports German-specific `äh` and `ähm` treatment and the importance of phonetic/prosodic context.
- Limitation: acoustic analysis does not automatically define when a sales agent should use a visible filler in TTS text.

## Connected Speech, Reductions, And Text Normalization

Ernestus, M., and Warner, N. (2011). "An introduction to reduced pronunciation variants." Journal of Phonetics, 39(3), 253-260.

- DOI: https://doi.org/10.1016/S0095-4470(11)00055-6
- MPI record: https://www.mpi.nl/publications/item_1084571
- Thesis relevance: supports the user observation that natural speech includes reductions and connected-speech variants, not just written-word pronunciation.
- Limitation: reductions should be conservative in professional sales speech and blocked in protected campaign text.

Zhang, H., Sproat, R., Ng, A. H., Stahlberg, F., Peng, X., Gorman, K., and Roark, B. (2019). "Neural Models of Text Normalization for Speech Applications." Computational Linguistics, 45(2), 293-337.

- DOI: https://doi.org/10.1162/COLI_a_00349
- Thesis relevance: supports treating spoken-text normalization as its own layer before TTS, especially for dates, numbers, abbreviations, contractions, and provider input.
- Limitation: local rules remain safer than black-box normalization for regulated product claims and appointment details.

Lange, R., Sell, B., Terada, M., Belz, M., Mooshammer, C., and Luedeling, A. (2024). "Schwa realisation in verbal inflection in two dialogue registers of German spontaneous speech." Zeitschrift fuer Sprachwissenschaft, 43(2), 237-266.

- DOI: https://doi.org/10.1515/zfs-2024-2011
- Repository page: https://edoc.hu-berlin.de/items/2ca4d454-e829-4f9b-8938-bda2302dc6c2
- Thesis relevance: supports German-specific spoken reduction work as a future layer, especially for avoiding over-formal synthetic German.
- Limitation: do not force colloquial German reductions into exact campaign questions or legal/compliance text.

## German Conversation Transcription

Selting, M., Auer, P., Barth-Weingarten, D., et al. (2009). "Gespraechsanalytisches Transkriptionssystem 2 (GAT 2)."

- PDF: https://ids-pub.bsz-bw.de/files/222/Selting_Auer_Barth-Weingarten_Gespraechsanalytisches_Transkriptionssystem_2009.pdf
- Bibliographic record: https://orbilu.uni.lu/handle/10993/4358
- Thesis relevance: useful reference for how conversation analysis represents pauses, overlap, breath, lengthening, laughter, and hesitation.
- Limitation: this should inspire annotation thinking; copied notation should be avoided unless citation and usage are reviewed.

## Breath And Pause Realism

Trouvain, J., Werner, R., and Mobius, B. (2020). "An Acoustic Analysis of Inbreath Noises in Read and Spontaneous Speech." Speech Prosody 2020.

- URL: https://www.isca-archive.org/speechprosody_2020/trouvain20_speechprosody.html
- Thesis relevance: supports the point that breath cues can be part of natural spoken communication.
- Limitation: breath cues in an AI sales call must be subtle and should not create discomfort or sound theatrical.

Werner, R., Trouvain, J., and Mobius, B. (2022). "Optionality and variability of speech pauses in read speech across languages and rates." Speech Prosody 2022.

- URL: https://www.isca-archive.org/speechprosody_2022/werner22_speechprosody.html
- Thesis relevance: supports variable, phrase-aware pause behavior rather than fixed pause templates.
- Limitation: read-speech pause behavior is not identical to spontaneous sales dialogue.

Werner, R., Fuchs, S., Trouvain, J., Kurbis, S., Mobius, B., and Birkholz, P. (2024). "Acoustics of Breath Noises in Human Speech: Descriptive and Three-Dimensional Modeling Approaches." Journal of Speech, Language, and Hearing Research, 67(10S), 3947-3961.

- DOI: https://doi.org/10.1044/2023_JSLHR-23-00112
- PubMed: https://pubmed.ncbi.nlm.nih.gov/37971432/
- Thesis relevance: supports the idea that breathing is part of speech structure and acoustic realism.
- Limitation: breath modeling is not a near-term requirement for the MVP unless provider output sounds unnaturally breathless in longer calls.

## Smiled Speech And Audible Warmth

Barthel, H., and Quene, H. (2015). "Acoustic-phonetic properties of smiling revised: measurements on a natural video corpus." Proceedings of ICPhS 2015.

- URL: https://dspace.library.uu.nl/handle/1874/356042
- Thesis relevance: supports discussing smile-like acoustic cues and perceived warmth in speech.
- Limitation: audible warmth should be evaluated for trust and professionalism; it should not become overacting.

Tartter, V. C. (1980). "Happy talk: perceptual and acoustic effects of smiling on speech." Perception & Psychophysics, 27, 24-27.

- DOI: https://doi.org/10.3758/BF03199901
- PubMed: https://pubmed.ncbi.nlm.nih.gov/7367197/
- Thesis relevance: early evidence that smiling can be heard in speech, supporting the idea of audible warmth.
- Limitation: old, small experimental work; use as background only, not as a product-performance claim.

## Sales And Call-Center Voice Evidence

Zhou, Y., Fei, Z., Yang, J., and Kong, D. (2025). "Serve with voice: The role of agents' vocal cues in the call center service." Journal of Business Research, 192, 115282.

- DOI: https://doi.org/10.1016/j.jbusres.2025.115282
- URL: https://www.sciencedirect.com/science/article/pii/S0148296325001055
- Thesis relevance: supports the product claim that how an agent speaks matters in call centers, not only what the agent says. The study identifies affirmative tone and relatively quick speech rate as useful service-success cues.
- Limitation: service success is not identical to outbound sales conversion, and "fast" must be balanced against clarity, compliance, and customer trust.

Guyer, J. J., Fabrigar, L. R., and Vaughan-Johnston, T. I. (2019). "Speech Rate, Intonation, and Pitch: Investigating the Bias and Cue Effects of Vocal Confidence on Persuasion." Personality and Social Psychology Bulletin, 45(3), 389-405.

- DOI: https://doi.org/10.1177/0146167218787805
- Thesis relevance: supports evaluating speech rate, intonation, and pitch as persuasion/confidence cues rather than treating voice naturalness as only filler placement.
- Limitation: persuasive confidence can become manipulative if misused; regulated campaigns still require guardrails and disclosures.

Niebuhr, O., Vosse, J., and Brem, A. (2016). "What makes a charismatic speaker? A computer-based acoustic-prosodic analysis of Steve Jobs' tone of voice." Computers in Human Behavior, 64, 366-382.

- DOI: https://doi.org/10.1016/j.chb.2016.06.059
- URL: https://www.sciencedirect.com/science/article/pii/S0747563216304873
- Thesis relevance: supports evaluating charisma-related prosody through melody, loudness, tempo, fluency, and audience/context differences.
- Limitation: product speech should aim for professional warmth and trust, not theatrical keynote-style charisma.

Niebuhr, O., Brem, A., and Tegtmeier, S. (2017). "Advancing research and practice in entrepreneurship through speech analysis - From descriptive rhetorical terms to phonetically informed acoustic charisma profiles." Journal of Speech Sciences, 6(1), 3-26.

- DOI: https://doi.org/10.20396/joss.v6i1.14983
- URL: https://econtents.sbu.unicamp.br/inpec/index.php/joss/article/view/14983
- Thesis relevance: supports replacing vague voice terms such as "charismatic" with measurable acoustic/prosodic features.
- Limitation: entrepreneurship pitches differ from two-party sales calls and should not dominate the MVP voice style.

## Speech Synthesis Evaluation And Human-Likeness

ITU-T Recommendation P.800. "Methods for subjective determination of transmission quality."

- URL: https://www.itu.int/rec/T-REC-P.800
- Thesis relevance: useful baseline reference for subjective speech-quality testing and MOS-style evaluation.
- Limitation: MOS alone may be too coarse for modern near-human TTS and does not capture sales usefulness, trust, or guardrail safety.

Le Maguer, S., King, S., and Harte, N. (2024). "The limits of the Mean Opinion Score for speech synthesis evaluation." Computer Speech & Language, 84, 101577.

- DOI: https://doi.org/10.1016/j.csl.2023.101577
- University record: https://www.research.ed.ac.uk/en/publications/the-limits-of-the-mean-opinion-score-for-speech-synthesis-evaluat/
- Thesis relevance: supports using richer listening rubrics instead of relying only on one naturalness score.
- Limitation: the project can still use simple ratings during development, but should interpret them cautiously.

Perrotin, O., Stephenson, B., Gerber, S., Bailly, G., and King, S. (2024). "Refining the evaluation of speech synthesis: A summary of the Blizzard Challenge 2023." Computer Speech & Language, 90, 101747.

- DOI: https://doi.org/10.1016/j.csl.2024.101747
- University record: https://www.research.ed.ac.uk/en/publications/refining-the-evaluation-of-speech-synthesis-a-summary-of-the-bliz
- Thesis relevance: supports multi-dimensional TTS evaluation as synthetic speech approaches human naturalness.
- Limitation: the Blizzard Challenge is a benchmark context, not a sales-agent deployment context.

Stern, S. E., Mullennix, J. W., Dyson, C., and Wilson, S. J. (1999). "The Persuasiveness of Synthetic Speech versus Human Speech." Human Factors, 41(4), 588-595.

- DOI: https://doi.org/10.1518/001872099779656680
- PubMed: https://pubmed.ncbi.nlm.nih.gov/10774129/
- Thesis relevance: historical evidence that synthetic speech can affect persuasion and speaker perception differently than human speech.
- Limitation: older TTS systems differ sharply from modern neural TTS; use as background, not current provider comparison evidence.

## Provider Control References

ElevenLabs. "Text to Speech Best Practices."

- URL: https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices
- Thesis relevance: supports using provider-supported pause, pacing, and emotion controls carefully instead of relying only on local text mutation.
- Limitation: provider guidance changes over time and does not replace project-specific listening tests.

ElevenLabs. "Controls / Pacing and Emotion."

- URL: https://elevenlabs.io/docs/product/prompting/pacing-and-emotion
- Thesis relevance: documents provider-supported break tags, speed settings, narrative styling, and emotion/pacing guidance that should be tested before adding too many local text fillers.
- Limitation: excessive break tags can create instability, and provider behavior is voice/model-specific.

ElevenLabs. "Voice Design."

- URL: https://elevenlabs.io/docs/creative-platform/voices/voice-design
- Thesis relevance: supports voice-design prompt work around language, timbre, pacing, emotion, audio quality, loudness, and guidance scale.
- Limitation: Voice Design is described as exploratory and variable; it does not replace runtime prosody control or listening evaluation.

ElevenLabs. "Get voice settings."

- URL: https://elevenlabs.io/docs/api-reference/voices/settings/get
- Thesis relevance: documents provider voice settings such as stability, style, and speed, which can affect emotional range, latency, and pace.
- Limitation: settings are provider-specific and should not be generalized to other TTS systems.

Fish Audio S2 / fish-speech.

- URLs:
  - https://fish.audio/s2/
  - https://github.com/fishaudio/fish-speech
  - https://huggingface.co/fishaudio/s2-pro
  - https://speech.fish.audio/
- Thesis relevance: supports the idea of fine-grained inline emotion/prosody control as architecture inspiration for an internal sales-safe prosody taxonomy.
- Project boundary: Fish is not installed, run, or used as a local runtime dependency. The project does not import Fish's full 15,000+ tag universe. Fish-style tags remain internal and must not appear in ElevenLabs buyer-facing speech.
- Limitation: hardware and commercial-license constraints make Fish a research/inspiration source only for the current project.

Liquid Audio / LFM2.5-Audio-1.5B.

- URLs:
  - https://github.com/Liquid4All/liquid-audio
  - https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B
  - https://docs.liquid.ai/lfm/help/model-license
- Thesis relevance: speech-to-speech architecture inspiration and negative TTS-quality result.
- Project boundary: Liquid setup, load, and synthetic TTS smoke succeeded mechanically, but manual listening review found the generated speech unintelligible/gibberish. Liquid is not a TTS backend, fallback voice, thesis-demo TTS, ASR quality proof, or live runtime component.
- Limitation: technical generation success does not imply intelligible or usable speech.

Kokoro-82M.

- URLs:
  - https://github.com/hexgrad/kokoro
  - https://huggingface.co/hexgrad/Kokoro-82M
- Thesis relevance: optional future local/offline TTS benchmark candidate if provider-independent TTS becomes thesis-relevant.
- Project boundary: Kokoro is not installed, run, or wired into runtime in the current evidence. It is not an immediate ElevenLabs replacement.
- Limitation: quality, latency, Windows setup, and sales-call suitability remain untested in this project.

## Thesis Usage Notes

Possible thesis framing:

- Speech naturalness was treated as a controlled design layer rather than random disfluency.
- English and German were handled through language-aware speech-realism profiles under one reusable agent architecture.
- Fillers and pauses were treated as speech-planning and interaction-management signals.
- Filler placement should be boundary-aware: pre-answer, sentence-boundary, discourse-transition, repair/reformulation, or pause-only when the filler would damage a fluent clause.
- Backchannels should be a separate interaction layer from speaker-side fillers, because the same short token can mean different things depending on whether the agent is speaking, listening, acknowledging, agreeing, or transitioning.
- Sales-call voice quality should be evaluated through rate, pitch/intonation, affirmative tone, warmth, clarity, and confidence, not just through filler count.
- General speech quality should be evaluated across prosodic phrasing, prominence, rhythm, reduction, response timing, perceived trust/warmth, and interaction quality.
- The system intentionally separated language mechanics from campaign persona and avoided stereotype-driven voice behavior.
- Prosody is now treated as an internal planning layer that maps buyer emotion, sales move, objection type, and conversation state into safe delivery guidance.
- ElevenLabs remains the current live voice path; Fish, Liquid, and Kokoro are not active live runtimes.
- Fish-inspired labels are internal/backend-neutral and must not be injected as raw bracket tags into buyer-facing speech.
- Liquid is useful only as architecture inspiration after failed manual listening review, not as a voice quality result.
- Buyer-facing uncertainty should be natural clarification, not exposed classifier language. For example, ask whether the buyer means plan details or fit, rather than saying the classifier is uncertain.

Near-term implementation implications:

- Add `VOICE-026` before the next major live audio comparison: separate speaker fillers, listener backchannels, discourse markers, pauses, and provider prosody tags.
- Add language-specific guardrails for English `well`/`so`/`oh` and German `also`/`okay`/`ja`/`genau` so they cannot imply unsafe agreement.
- Prefer provider prosody and short acknowledgments for thinking time before adding more visible `um`/`ähm` tokens.
- Evaluate faster sales-call pace, but only inside a bounded speed range and never for disclosures, regulated claims, appointment details, or campaign questions.
- Include a minimal evaluation rubric for VOICE-026 that separates naturalness, trust, confidence, warmth, pace, interruption safety, and sales usefulness.
- Clean the Fish-inspired prosody taxonomy before mapping it to ElevenLabs style prompts, punctuation, sentence length, or voice settings.
- Do not treat prosody taxonomy validation as audio-quality evidence; listening review is still required.

Possible thesis limitation:

- The profiles are literature-informed but still require listening evaluation with proficient or native English and German speakers before strong claims can be made.
- Most speech-pattern sources are ordinary conversation, read speech, or service calls. Direct outbound-sales evidence is thinner, so product claims should be stated as literature-informed hypotheses until evaluated on project audio and private call-center data.
- Many speech sources are language-, corpus-, channel-, and task-specific. The project should avoid claiming a universal "human speech formula"; it should claim a guardrailed, testable speech-behavior layer.

Possible future work:

- Compare plain TTS, prosody-shaped TTS, and language-profile-shaped TTS.
- Add listener ratings for naturalness, trust, professionalism, warmth, and overacting risk.
- Review DGD/FOLK and Spoken BNC2014 access terms before using any corpus examples directly.
- When private call-center data arrives, mine only anonymized aggregate timing, phrasing, objection, and outcome patterns; do not copy private customer identifiers or raw audio into tracked thesis docs.
- Add a later `VOICE-03x` adaptive-speech checkpoint for bounded entrainment to customer pace/energy after the core latency, interruption, and protected-text behavior is stable.
