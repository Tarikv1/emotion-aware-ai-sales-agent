# Data Readiness

## Goal

Create a simple inventory of the data sources that may feed the thesis project and identify what is usable now, what needs cleanup, and what must remain restricted.

## Recommended Phase 1 Dataset Plan

Use a narrow public-data baseline first instead of trying to merge many corpora at once.

### Primary public datasets

#### 1. IEMOCAP

Role in project:

- speech emotion baseline
- emotion labels from voiced conversation
- first pass on the emotion-classification component

Why it is included:

- widely used for speech emotion work
- useful for audio-based emotion experiments
- good fit for the first version of the emotion layer

Known limitation:

- acted rather than real sales calls

#### 2. MELD

Role in project:

- conversational emotion context
- multi-turn dialogue emotion signals
- support for text-aware or multimodal emotion experiments

Why it is included:

- useful for conversation-level emotional context
- helps bridge from isolated speech emotion to dialogue-aware behavior

Known limitation:

- sourced from TV dialogue rather than real call-center conversations

#### 3. Persuasion for Good

Role in project:

- persuasion strategy reference
- success and failure patterns in persuasive dialogue
- source for an initial lightweight strategy taxonomy

Why it is included:

- closest match to the persuasion part of the thesis
- gives the project a grounded strategy layer without inventing one from scratch

Known limitation:

- text dialogue, not phone-call audio

## Deferred Datasets

Do not treat these as phase-1 requirements:

- Fisher
- Switchboard
- CALLHOME
- negotiation datasets such as Deal or No Deal or CraigslistBargain

These may be useful later for realism, turn-taking, or strategy experiments, but they add complexity too early and are not required for the first believable thesis baseline.

## Source Inventory

### Public datasets

Status: downloaded locally for phase 1

Current planned set:

- IEMOCAP
- MELD
- Persuasion for Good

Current local state:

- `MELD` is downloaded and extracted
- `Persuasion for Good` is downloaded and extracted
- `IEMOCAP` currently appears to be a single CSV-style export rather than the official corpus structure, so it needs verification before we rely on it for audio experiments

Unknowns to confirm:

- license and usage terms
- exact download source
- local storage layout
- label mapping into the thesis emotion taxonomy
- whether each dataset will be used for training, validation, analysis, or only strategy design

### Private call-center recordings

Status: not currently available in hand

Unknowns to confirm:

- audio only or audio plus transcripts
- number of calls
- language mix
- product domain
- outcome labels available
- metadata available
- whether annotations already exist
- anonymization needs
- practical permission boundaries for thesis usage

## Language and Domain Note

The eventual target is not specifically German sales calls.
However, if private call-center data is later introduced, it may be German-language and therefore create a language and domain shift relative to the initial public datasets.

Treat that as a later adaptation problem, not as a blocker for phase 1.
For now, build the first baseline so that:

- the emotion layer can be evaluated independently
- the strategy layer can be kept small and explicit
- later German private-data adaptation can be added as a documented extension

## Phase 1 Working Assumptions

Assume the first public-data baseline will:

- use public data only
- focus on a small emotion taxonomy
- use a lightweight persuasion-strategy mapping
- prioritize a believable thesis pipeline over acoustic realism
- treat private call-center data as a later optional enhancement

## Required Inventory Fields

For each dataset, record:

- dataset name
- public or private
- raw format
- transcript availability
- label availability
- outcome labels
- sample count
- duration
- language
- known noise/issues
- allowed use
- storage location
- experiment label: `public-only`, `private-restricted`, or `mixed-source`

## Readiness Questions

Before training or tuning anything, answer:

1. Do we have audio, transcripts, or both?
2. Do we have reliable sales outcomes?
3. Do we have usable emotion labels, or must they be created?
4. Can the private data legally and practically be used for local thesis work?
5. Which experiments must stay reproducible with public data only?
6. What is the minimum clean subset we can work with first?

## Recommended First Technical Slice

Do not begin with end-to-end agent training.
Start by preparing one narrow dataset slice:

- one public-data baseline
- one small emotion taxonomy
- one persuasion-strategy mapping
- one outcome signal

The goal is to prove that the data can support a believable first pipeline.
