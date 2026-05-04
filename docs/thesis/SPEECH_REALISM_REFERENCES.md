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

## English Disfluency And Planning Signals

Clark, H. H., and Fox Tree, J. E. (2002). "Using uh and um in spontaneous speaking." Cognition, 84(1), 73-111.

- DOI: https://doi.org/10.1016/S0010-0277(02)00017-3
- Author PDF: https://web.stanford.edu/~clark/2000s/Clark.FoxTree.02.pdf
- Thesis relevance: English `uh` and `um` can be discussed as speech-planning delay signals rather than meaningless noise.
- Limitation: this supports controlled filler use, not blanket insertion of fillers into every response.

## Spoken English Corpus Reference

British National Corpus 2014, Spoken BNC2014.

- Corpus page: https://corpora.lancs.ac.uk/bnc2014/
- Related paper: Love, R., Dembry, C., Hardie, A., Brezina, V., and McEnery, T. (2017). "The Spoken BNC2014: designing and building a spoken corpus of everyday conversations." International Journal of Corpus Linguistics, 22(3), 319-344.
- DOI: https://doi.org/10.1075/ijcl.22.3.02lov
- Thesis relevance: useful reference for contemporary spoken English, informal discourse markers, turn-taking, and conversation style.
- Limitation: everyday conversation is not the same as professional sales-call speech.

## Spoken German Corpus Reference

DGD / FOLK: Database for Spoken German and Forschungs- und Lehrkorpus Gesprochenes Deutsch.

- Corpus portal: https://dgd.ids-mannheim.de/DGD2Web/jsp/Welcome.jsp
- Thesis relevance: candidate reference for spontaneous German interaction, German filler particles, backchannels, turn-taking, and pause behavior.
- Access note: DGD requires registration and has usage terms. Do not copy corpus content into this repo unless those terms are reviewed.
- Limitation: corpus access and allowed reuse must be checked before using examples in thesis text.

## German Filler Particles

Muhlack, B., Trouvain, J., and Jessen, M. (2023). "Distributional and Acoustic Characteristics of Filler Particles in German with Consideration of Forensic-Phonetic Aspects." Languages, 8(2), 100.

- URL: https://www.mdpi.com/2226-471X/8/2/100
- Thesis relevance: supports the idea that German fillers should not simply copy English `uh` and `um`.
- Limitation: filler particles show strong speaker variation; this supports cautious language-specific profiles, not one fixed German speaking style.

Belz, M. (2023). "Defining Filler Particles: A Phonetic Account of the Terminology, Form, and Grammatical Classification of 'Filled Pauses'." Languages, 8(1), 57.

- URL: https://www.mdpi.com/2226-471X/8/1/57
- Thesis relevance: helps define terms such as filler particle, filled pause, hesitation marker, and disfluency.
- Limitation: terminology should be used carefully because not every pause, repair, or hesitation is the same phenomenon.

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

## Smiled Speech And Audible Warmth

Barthel, H., and Quene, H. (2015). "Acoustic-phonetic properties of smiling revised: measurements on a natural video corpus." Proceedings of ICPhS 2015.

- URL: https://dspace.library.uu.nl/handle/1874/356042
- Thesis relevance: supports discussing smile-like acoustic cues and perceived warmth in speech.
- Limitation: audible warmth should be evaluated for trust and professionalism; it should not become overacting.

## Thesis Usage Notes

Possible thesis framing:

- Speech naturalness was treated as a controlled design layer rather than random disfluency.
- English and German were handled through language-aware speech-realism profiles under one reusable agent architecture.
- Fillers and pauses were treated as speech-planning and interaction-management signals.
- The system intentionally separated language mechanics from campaign persona and avoided stereotype-driven voice behavior.

Possible thesis limitation:

- The profiles are literature-informed but still require listening evaluation with proficient or native English and German speakers before strong claims can be made.

Possible future work:

- Compare plain TTS, prosody-shaped TTS, and language-profile-shaped TTS.
- Add listener ratings for naturalness, trust, professionalism, warmth, and overacting risk.
- Review DGD/FOLK and Spoken BNC2014 access terms before using any corpus examples directly.
