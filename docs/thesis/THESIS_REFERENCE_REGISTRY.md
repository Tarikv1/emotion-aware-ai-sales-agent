# Thesis Reference Registry

## Purpose

Track the external resources that have influenced the thesis and product work so they are not lost in chat history.

This registry is not a final bibliography. It is a working source map for later thesis writing.

## Source Categories

Use the source categories carefully:

- Academic source: suitable for related work or methodology discussion after proper citation formatting.
- Dataset source: suitable for data chapter or experiment setup after access and license checks.
- Provider documentation: suitable for implementation and system-design discussion, not as academic proof of quality.
- Product inspiration: useful for product design attribution, not necessarily thesis evidence.
- Open-source inspiration: useful for attribution and process notes, not a runtime dependency unless separately reviewed.
- Unverified source: mentioned in project history but exact URL, license, or access conditions need follow-up.

## RAG And NotebookLM Workflow Sources

### NotebookLM supported source types

- Type: provider documentation and research workflow source
- Source: https://support.google.com/notebooklm/answer/16215270?hl=en
- Project use: informs RAG-001/RAG-002 source-intake assumptions for websites, YouTube videos, PDFs, text, Markdown, Google Docs/Slides, and audio sources.
- Current project status: used for workflow design only. RAG-001/RAG-002 do not call NotebookLM and do not store raw source text.
- Thesis caution: provider documentation describes tool capability, not scientific evidence for sales-agent performance.

### NotebookLM reports, data tables, and exports

- Type: provider documentation and research workflow source
- Source: https://support.google.com/notebooklm/answer/16206563?hl=en
- Project use: informs the RAG-002 decision to use generated reports/data-table style outputs and exported/copied JSON as the handoff from NotebookLM to the local validator.
- Current project status: used for workflow design only. RAG-002 still requires manual NotebookLM UI use and local validation before any extracted notes are promoted.
- Thesis caution: exported NotebookLM artifacts should be treated as intermediate extraction notes; the thesis should cite original sources, not NotebookLM.

### NotebookLM Enterprise API

- Type: provider documentation and possible future automation source
- Source: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources
- Project use: records that programmatic NotebookLM notebook/source workflows exist in NotebookLM Enterprise, while RAG-001 remains local and manual by default.
- Current project status: no NotebookLM API call is implemented or required.
- Thesis caution: future automation would need separate provider, privacy, retention, and cost review.

## Primary Public Dataset Sources

### IEMOCAP

- Type: dataset source
- Main source: https://sail.usc.edu/iemocap/iemocap_info.htm
- USC SAIL database page: https://sail.usc.edu/software/databases/
- Project use: speech emotion reference and possible audio-emotion baseline.
- Current project status: local file appears to be a repackaged CSV-style export, not the full official corpus structure.
- Thesis caution: do not make official-IEMOCAP claims from the local export until provenance and access conditions are verified.

### MELD

- Type: dataset source
- Project page: https://affective-meld.github.io/
- GitHub: https://github.com/declare-lab/MELD
- Paper: https://huggingface.co/papers/1810.02508
- Project use: conversation-level emotion labels, sentiment labels, and multimodal emotion-in-conversation grounding.
- Current project status: downloaded and extracted locally.
- Thesis caution: MELD is based on TV dialogue, so it is useful for emotion/context grounding but not a real sales-call corpus.

### Persuasion for Good

- Type: dataset and academic source
- ACL Anthology paper: https://aclanthology.org/P19-1566/
- ConvoKit corpus page: https://convokit.cornell.edu/documentation/persuasionforgood.html
- GitHub dataset/code reference: https://github.com/ohyj1002/persuasionforgood
- Project use: persuasion strategy taxonomy, persuasive-dialogue analysis, and success/failure reasoning.
- Current project status: downloaded and extracted locally.
- Thesis caution: the task is charity persuasion, not commercial outbound sales. Use it for strategy grounding, not direct product-performance claims.

## Speech Realism Sources

Detailed notes live in `docs/thesis/SPEECH_REALISM_REFERENCES.md`.

### Vinh Giang / AskVinh communication corpus

- Type: practitioner/video source pack and RAG extraction source
- YouTube channel: https://www.youtube.com/@askvinh/videos
- Official site: https://www.vinhgiang.com/
- Project use: imported through NotebookLM as a communication, vocal delivery, pacing, pausing, resonance, concise-response, rapport, and storytelling source pack for RAG voice/response review.
- Current project status: the NotebookLM report is stored under `research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports/` and is included in refreshed RAG-003 through RAG-006 outputs.
- Thesis caution: use as practitioner training material, not academic evidence. Exact per-video URLs and publication metadata still need review before final citation.

Core references:

- Cutler, Dahan, and van Donselaar (1997), prosody in spoken-language comprehension: https://doi.org/10.1177/002383099704000203
- Cutler, Dahan, and van Donselaar (1997), PubMed record: https://pubmed.ncbi.nlm.nih.gov/9509577/
- Wagner and Watson (2010), prosodic phrasing and prominence review: https://doi.org/10.1080/01690961003589492
- Wagner and Watson (2010), PubMed record: https://pubmed.ncbi.nlm.nih.gov/22096264/
- Banse and Scherer (1996), acoustic profiles of vocal emotion: https://doi.org/10.1037/0022-3514.70.3.614
- Banse and Scherer (1996), PubMed record: https://pubmed.ncbi.nlm.nih.gov/8851745/
- Juslin and Laukka (2003), vocal emotion communication review: https://doi.org/10.1037/0033-2909.129.5.770
- McAleer, Todorov, and Belin (2014), vocal first impressions: https://doi.org/10.1371/journal.pone.0090779
- McAleer, Todorov, and Belin (2014), PLOS page: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0090779
- Clark and Fox Tree (2002), English `uh` and `um`: https://doi.org/10.1016/S0010-0277(02)00017-3
- Kirjavainen, Crible, and Beeching (2022), filled pauses as linguistic items: https://doi.org/10.1177/00238309211011201
- Bortfeld et al. (2001), conversation disfluency rates by role/topic/relationship: https://doi.org/10.1177/00238309010440020101
- Levelt (1983), monitoring and self-repair in speech: https://doi.org/10.1016/0010-0277(83)90026-4
- Laserna, Seih, and Pennebaker (2014), filler-word categories and variation: https://doi.org/10.1177/0261927X14526993
- Bolden (2009), English discourse marker `so`: https://doi.org/10.1016/j.pragma.2008.10.004
- Heritage (1998), English `oh`-prefaced responses: https://doi.org/10.1017/S0047404598003017
- Swerts (1998), filled pauses and discourse boundaries: https://doi.org/10.1016/S0378-2166(98)00014-9
- Gosy (2023), filled pause positions and neighboring pauses/words: https://doi.org/10.3390/languages8010079
- Brennan and Williams (1995), prosody/fillers as perceived knowledge cues: https://doi.org/10.1006/jmla.1995.1017
- Kirkland et al. (2022), filler location, speech rate, f0, and confidence: https://doi.org/10.21437/Interspeech.2022-10973
- Dall et al. (2014), filled-pause insertion for speech synthesis: https://www.research.ed.ac.uk/en/publications/investigating-automatic-amp-human-filled-pause-insertion-for-spee/
- Elmers, O'Mahony, and Szekely (2023), pause-internal phonetic particles in speech synthesis: https://doi.org/10.21437/Interspeech.2023-2178
- Heritage (2015), English turn-initial `well`: https://doi.org/10.1016/j.pragma.2015.08.008
- Sacks, Schegloff, and Jefferson (1974), turn-taking organization: https://doi.org/10.2307/412243
- Sacks, Schegloff, and Jefferson (1974), MPI record: https://www.mpi.nl/publications/item2376846/simplest-systematics-organization-turn-taking-conversation
- Stivers et al. (2009), turn-taking timing across languages: https://doi.org/10.1073/pnas.0903616106
- Levinson and Torreira (2015), timing in turn-taking and processing: https://doi.org/10.3389/fpsyg.2015.00731
- Ward and Tsukahara (2000), prosodic cues for backchannels: https://doi.org/10.1016/S0378-2166(99)00109-5
- Heldner and Edlund (2010), pauses/gaps/overlaps in conversation: https://doi.org/10.1016/j.wocn.2010.08.002
- Heldner and Edlund (2010), article page: https://www.sciencedirect.com/science/article/pii/S0095447010000628
- Skantze (2021), turn-taking in conversational systems review: https://doi.org/10.1016/j.csl.2020.101178
- Skantze (2021), article page: https://www.sciencedirect.com/science/article/pii/S088523082030111X
- Witt (2015), user response timings in spoken dialog systems: https://doi.org/10.1007/s10772-014-9265-1
- Pardo (2006), phonetic convergence in conversation: https://doi.org/10.1121/1.2178720
- Pardo (2006), university record: https://digitalcommons.montclair.edu/psychology-facpubs/347/
- Weise et al. (2019), acoustic-prosodic entrainment: https://doi.org/10.1016/j.specom.2019.10.007
- Weise et al. (2019), university record: https://cris.biu.ac.il/en/publications/individual-differences-in-acoustic-prosodic-entrainment-in-spoken/
- Spoken BNC2014: https://corpora.lancs.ac.uk/bnc2014/
- Switchboard-1 Release 2, LDC page: https://catalog.ldc.upenn.edu/LDC97S62
- Switchboard-1 Release 2, DOI: https://doi.org/10.35111/sw3h-rw02
- Santa Barbara Corpus of Spoken American English, LDC Part I: https://catalog.ldc.upenn.edu/LDC2000S85
- Buckeye Corpus: https://buckeyecorpus.osu.edu/
- Buckeye Corpus paper: https://doi.org/10.1016/j.specom.2004.09.001
- DGD / FOLK spoken German portal: https://dgd.ids-mannheim.de/DGD2Web/jsp/Welcome.jsp
- German turn-beginning design, Deppermann (2013): https://doi.org/10.1016/j.pragma.2012.07.010
- German `also` and `dann` in talk-in-interaction, Deppermann and Helmer (2013): https://ids-pub.bsz-bw.de/frontdoor/index/index/docId/1304
- German sentence-position effects for `also`, Alm (2004): https://doi.org/10.21248/zaspil.35.2004.219
- German `okay` as a neutral acceptance token, Oloff (2018): https://doi.org/10.54563/lexique.924
- German response token `ja` and prosody, Golato and Fagyal (2008): https://doi.org/10.1080/08351810802237834
- German backchannels and fluencemes, Bottcher and Rossi (2025): https://doi.org/10.3389/fcomm.2025.1655049
- German/Austrian-German backchannel timing, Paierl, Kelterer, and Schuppler (2025): https://doi.org/10.3390/languages10080194
- Paierl, Kelterer, and Schuppler (2025), article page: https://www.mdpi.com/2226-471X/10/8/194
- Austrian German read/conversational corpus, Schuppler et al. (2017): https://doi.org/10.1016/j.specom.2017.09.003
- Schuppler et al. (2017), article page: https://www.sciencedirect.com/science/article/pii/S0167639317300535
- Kiel Corpus of Spoken German: https://www.isfas.uni-kiel.de/de/linguistik-und-phonetik/smile-if-you-can-see-this/forschung/kiel-corpus/the-kiel-corpus-of-spoken-german-read-and-spontaneous-speech
- German filler particles, Muhlack et al. (2023): https://www.mdpi.com/2226-471X/8/2/100
- Filler-particle terminology, Belz (2023): https://www.mdpi.com/2226-471X/8/1/57
- German `äh`/`ähm` phonetics, Belz (2021): https://doi.org/10.1007/978-3-662-62812-6
- German `äh`/`ähm` phonetics publisher page, Belz (2021): https://link.springer.com/book/10.1007/978-3-662-62812-6
- Reduced pronunciation variants, Ernestus and Warner (2011): https://doi.org/10.1016/S0095-4470(11)00055-6
- Reduced pronunciation variants, MPI record: https://www.mpi.nl/publications/item_1084571
- Text normalization for speech applications, Zhang et al. (2019): https://doi.org/10.1162/COLI_a_00349
- German schwa realization in spontaneous speech, Lange et al. (2024): https://doi.org/10.1515/zfs-2024-2011
- German schwa realization repository page: https://edoc.hu-berlin.de/items/2ca4d454-e829-4f9b-8938-bda2302dc6c2
- GAT 2 transcription system: https://ids-pub.bsz-bw.de/files/222/Selting_Auer_Barth-Weingarten_Gespraechsanalytisches_Transkriptionssystem_2009.pdf
- Inbreath noises, Trouvain et al. (2020): https://www.isca-archive.org/speechprosody_2020/trouvain20_speechprosody.html
- Pause variability, Werner et al. (2022): https://www.isca-archive.org/speechprosody_2022/werner22_speechprosody.html
- Breath-noise acoustics and modeling, Werner et al. (2024): https://doi.org/10.1044/2023_JSLHR-23-00112
- Smiled speech, Barthel and Quene (2015): https://dspace.library.uu.nl/handle/1874/356042
- Smiling and acoustic/perceptual effects on speech, Tartter (1980): https://doi.org/10.3758/BF03199901
- Call-center vocal cues and service success, Zhou et al. (2025): https://doi.org/10.1016/j.jbusres.2025.115282
- Speech rate, intonation, pitch, confidence, and persuasion, Guyer, Fabrigar, and Vaughan-Johnston (2019): https://doi.org/10.1177/0146167218787805
- Acoustic-prosodic charisma in business/keynote speech, Niebuhr, Vosse, and Brem (2016): https://doi.org/10.1016/j.chb.2016.06.059
- Niebuhr, Vosse, and Brem (2016), article page: https://www.sciencedirect.com/science/article/pii/S0747563216304873
- Acoustic charisma profiles for entrepreneurship, Niebuhr, Brem, and Tegtmeier (2017): https://doi.org/10.20396/joss.v6i1.14983
- Niebuhr, Brem, and Tegtmeier (2017), article page: https://econtents.sbu.unicamp.br/inpec/index.php/joss/article/view/14983
- ITU-T P.800 subjective speech-quality testing: https://www.itu.int/rec/T-REC-P.800
- Limits of MOS for speech synthesis evaluation, Le Maguer, King, and Harte (2024): https://doi.org/10.1016/j.csl.2023.101577
- Le Maguer, King, and Harte (2024), university record: https://www.research.ed.ac.uk/en/publications/the-limits-of-the-mean-opinion-score-for-speech-synthesis-evaluat/
- Blizzard Challenge 2023 speech-synthesis evaluation, Perrotin et al. (2024): https://doi.org/10.1016/j.csl.2024.101747
- Perrotin et al. (2024), university record: https://www.research.ed.ac.uk/en/publications/refining-the-evaluation-of-speech-synthesis-a-summary-of-the-bliz
- Synthetic vs human speech persuasiveness, Stern et al. (1999): https://doi.org/10.1518/001872099779656680
- Stern et al. (1999), PubMed record: https://pubmed.ncbi.nlm.nih.gov/10774129/
- ElevenLabs pacing and emotion prompting: https://elevenlabs.io/docs/product/prompting/pacing-and-emotion
- ElevenLabs Voice Design: https://elevenlabs.io/docs/creative-platform/voices/voice-design

Project use:

- `VOICE-023` speech-realism design
- thesis discussion of controlled speech naturalness
- `VOICE-025` filler-placement design
- `VOICE-026` planned interaction-prosody/backchannel design
- limitations around listener evaluation and language-specific behavior

## Privacy And Data Governance Sources

### European Commission GDPR Principles

- Type: legal/privacy reference
- Source: https://commission.europa.eu/law/law-topic/data-protection/rules-business-and-organisations/principles-gdpr/overview-principles/what-data-can-we-process-and-under-which-conditions_en
- Project use: data minimization, purpose limitation, storage limitation, integrity/confidentiality framing.
- Thesis use: private call-center data boundary and retention rationale.

### European Data Protection Board GDPR Basics

- Type: legal/privacy reference
- Processing principles: https://www.edpb.europa.eu/sme-data-protection-guide/faq-frequently-asked-questions/answer/what-are-basic-processing_en
- Legal bases: https://www.edpb.europa.eu/sme-data-protection-guide/faq-frequently-asked-questions/answer/what-are-legal-basics-processing_en
- Project use: private-data learning checkpoints, redaction, retention/deletion, and no-provider-upload default.
- Thesis caution: use these for high-level GDPR framing, not as legal advice.

## TTS And Voice Provider Sources

### VOICE-009 provider research

Detailed source index:

- `research/experiments/generated/VOICE-009-tts-provider-research-report.md`

Provider sources used:

- Cartesia docs: https://docs.cartesia.ai/
- Cartesia Sonic 3: https://docs.cartesia.ai/build-with-cartesia/tts-models/sonic-3
- Cartesia realtime quickstart: https://docs.cartesia.ai/get-started/realtime-text-to-speech-quickstart
- Cartesia WebSocket API: https://docs.cartesia.ai/api-reference/tts/websocket
- Cartesia pricing: https://cartesia.ai/pricing
- ElevenLabs TTS: https://elevenlabs.io/docs/overview/capabilities/text-to-speech
- ElevenLabs models: https://elevenlabs.io/docs/models
- ElevenLabs TTS API: https://elevenlabs.io/text-to-speech-api
- OpenAI TTS guide: https://platform.openai.com/docs/guides/text-to-speech
- OpenAI audio quickstart: https://platform.openai.com/docs/guides/audio/quickstart
- OpenAI GPT-4o mini TTS model: https://platform.openai.com/docs/models/gpt-4o-mini-tts
- Azure AI Speech TTS: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech
- Azure language support: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support
- Azure TTS REST API: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech
- Google Cloud Chirp 3 HD: https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd
- Google Cloud streaming TTS: https://cloud.google.com/text-to-speech/docs/create-audio-text-streaming
- Google Cloud voices: https://cloud.google.com/text-to-speech/docs/voices
- Amazon Polly SynthesizeSpeech: https://docs.aws.amazon.com/polly/latest/dg/API_SynthesizeSpeech.html
- Amazon Polly streaming: https://docs.aws.amazon.com/polly/latest/dg/API_StartSpeechSynthesisStream.html
- Amazon Polly neural voices: https://docs.aws.amazon.com/polly/latest/dg/neural-voices.html
- Deepgram Aura voices: https://developers.deepgram.com/docs/tts-models
- Piper local TTS: https://github.com/rhasspy/piper
- Open Home Foundation Piper: https://github.com/OHF-Voice/piper1-gpl
- Open Home Foundation Piper releases: https://github.com/OHF-Voice/piper1-gpl/releases
- OpenAI pricing: https://platform.openai.com/docs/pricing
- Azure AI Speech pricing: https://azure.microsoft.com/en-gb/pricing/details/speech/
- Amazon Polly pricing: https://aws.amazon.com/polly/pricing/
- Deepgram pricing: https://deepgram.com/pricing
- Cartesia TTS bytes endpoint docs: https://docs.cartesia.ai/api-reference/tts/bytes
- Cartesia TTS endpoint comparison: https://docs.cartesia.ai/api-reference/tts/compare-tts-endpoints
- Cartesia alternate endpoint comparison: https://docs.cartesia.ai/use-the-api/compare-tts-endpoints
- Cartesia Sonic SSML tags: https://docs.cartesia.ai/build-with-cartesia/sonic-3/ssml-tags
- Cartesia Sonic volume, speed, and emotion controls: https://docs.cartesia.ai/build-with-cartesia/sonic-3/volume-speed-emotion
- ElevenLabs streaming TTS API: https://elevenlabs.io/docs/api-reference/text-to-speech/stream
- ElevenLabs WebSocket API: https://elevenlabs.io/docs/api-reference/websocket
- ElevenLabs latency concepts: https://elevenlabs.io/docs/eleven-api/concepts/latency
- ElevenLabs pacing and emotion prompting: https://elevenlabs.io/docs/product/prompting/pacing-and-emotion
- ElevenLabs API pause/SSML help article: https://help.elevenlabs.io/hc/en-us/articles/24352686926609-Do-pauses-and-SSML-phoneme-tags-work-with-the-API

Project use:

- provider-readiness matrix
- latency, German/English, privacy, and fallback criteria
- guarded TTS integration sequence

Thesis caution:

- provider docs justify engineering choices, not objective quality claims. Audio quality claims require measured runs and listening review.

### ElevenLabs voice design and remixing

Detailed source entry:

- `docs/third-party-inspirations.md`
- `docs/product/VOICE_020_ELEVENLABS_VOICE_DESIGN.md`

Sources:

- Voices overview: https://elevenlabs.io/docs/overview/capabilities/voices
- Voice Design: https://elevenlabs.io/docs/eleven-creative/voices/voice-design
- TTS best practices: https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices
- Voice settings API: https://elevenlabs.io/docs/api-reference/voices/settings/get
- Agent privacy docs: https://elevenlabs.io/docs/eleven-agents/customization/privacy
- Commercial-use help article: https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform
- Voice Remixing: https://elevenlabs.io/docs/overview/capabilities/voice-remixing

Project use:

- voice prompt design
- voice remixing prompts
- live custom voice comparison
- provider privacy and logging boundaries

## Sales Objection And Product Sources

### Sales difficulty taxonomy

Project file:

- `docs/product/SALES_DIFFICULTY_TAXONOMY.md`

Sources found or recovered:

- Apollo common sales objections: https://www.apollo.io/insights/common-sales-objections
- Apollo handling objections in sales: https://www.apollo.io/insights/handling-objections-in-sales
- Salesgenie objection handling: https://www.salesgenie.com/blog/sales-objection-handling/
- Proposify sales objection handling: https://www.proposify.com/blog/sales-objection-handling
- Proposify four types of objections: https://www.proposify.com/blog/overcome-sales-objections
- B2B Vic objection handling framework: https://b2bvic.com/articles/objection-handling-b2b-sales.html

Project use:

- broad difficulty categories such as price, timing, authority, trust, status quo, competitor comparison, fit/risk, and brush-off.

Thesis caution:

- these are public sales-practice articles, not peer-reviewed evidence.
- use them as product grounding, not as academic proof.
- synthetic experiment cases should not copy example scripts from these pages.

## Open-Source And Workflow Inspirations

Detailed attribution lives in:

- `docs/third-party-inspirations.md`

Sources:

- OpenMythos: https://github.com/kyegomez/OpenMythos
- jcode: https://github.com/1jehuang/jcode
- autoresearch: https://github.com/karpathy/autoresearch
- gstack: https://github.com/garrytan/gstack
- GitNexus: https://github.com/abhigyanpatwari/GitNexus
- awesome-llm-apps: https://github.com/Shubhamsaboo/awesome-llm-apps
- graphify: https://github.com/safishamsi/graphify
- voicebox: https://github.com/jamiepine/voicebox
- VibeVoice: https://github.com/microsoft/VibeVoice
- hermes-agent: https://github.com/NousResearch/hermes-agent
- TRIBE v2: https://github.com/facebookresearch/tribev2

Project use:

- review workflow inspiration
- local relevant-file reading
- experiment discipline
- product review gates
- voice provenance caution
- future ASR and multimodal ideas

Thesis caution:

- cite only where these materially influenced methodology or implementation process.
- do not imply these repos are runtime dependencies.
- license restrictions are recorded in `docs/third-party-inspirations.md`.

## Browser And Local Prototype Sources

Project-relevant browser/local APIs:

- browser Web Speech API behavior was used in early browser speech demos
- Windows SAPI was tested as a local no-key TTS path

Current registry status:

- exact external documentation pages for Web Speech API and Windows SAPI are not yet captured in a thesis-ready source entry.

Follow-up:

- if browser speech recognition or Windows SAPI remains in the thesis prototype discussion, add MDN/Microsoft source links and limitations before final writing.

## Unverified Or Needs Follow-Up

These influenced project direction but should not be used as final thesis references yet:

- exact original download source and license for the local IEMOCAP CSV-style export
- exact original download source and license for the local MELD archive, beyond the official project/GitHub references
- exact original download source and license for the local Persuasion for Good archive, beyond the official paper/corpus references
- exact provider terms for production retention and logging beyond the implementation docs already cited
- final German outbound-calling, insurance-sales, and call-recording legal sources

## How To Use This Registry

For the thesis:

- use academic papers and dataset sources in related work, data, and methodology chapters
- use provider docs only when explaining engineering constraints and implementation decisions
- use sales-practice articles only as product-context grounding
- use open-source repos only for attribution and methodology/process inspiration
- disclose private-data influence separately and never include private artifacts

For product work:

- keep provider claims behind live tests and listening review
- keep private call-center audio local-only
- keep SalesCampaign profiles as the product boundary
- keep one reusable sales-agent core across verticals
- run `python scripts\check_thesis_reference_registry.py` before GitHub checkpoints so source-backed claims stay traceable
