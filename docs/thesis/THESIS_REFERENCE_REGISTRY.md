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

Core references:

- Clark and Fox Tree (2002), English `uh` and `um`: https://doi.org/10.1016/S0010-0277(02)00017-3
- Spoken BNC2014: https://corpora.lancs.ac.uk/bnc2014/
- DGD / FOLK spoken German portal: https://dgd.ids-mannheim.de/DGD2Web/jsp/Welcome.jsp
- German filler particles, Muhlack et al. (2023): https://www.mdpi.com/2226-471X/8/2/100
- Filler-particle terminology, Belz (2023): https://www.mdpi.com/2226-471X/8/1/57
- GAT 2 transcription system: https://ids-pub.bsz-bw.de/files/222/Selting_Auer_Barth-Weingarten_Gespraechsanalytisches_Transkriptionssystem_2009.pdf
- Inbreath noises, Trouvain et al. (2020): https://www.isca-archive.org/speechprosody_2020/trouvain20_speechprosody.html
- Pause variability, Werner et al. (2022): https://www.isca-archive.org/speechprosody_2022/werner22_speechprosody.html
- Smiled speech, Barthel and Quene (2015): https://dspace.library.uu.nl/handle/1874/356042

Project use:

- `VOICE-023` speech-realism design
- thesis discussion of controlled speech naturalness
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
