# EXP-002 Dataset-Derived Case Pack

This file defines six dataset-derived, domain-adapted cases for the phase-1 baseline experiment.

These are not raw benchmark cases copied directly from a single dataset.
They are grounded in:

- emotional interaction patterns observed in `MELD`
- persuasion strategy patterns observed in `Persuasion for Good`

The wording is adapted into a sales-dialogue setting so the cases fit the thesis domain.

## Case 01

- Case ID: `EXP-002-C01`
- Emotion label: `positive`
- Adaptive strategy label: `direct-ask-or-commitment`

Source grounding:

- `MELD`: `Dialogue_ID=0`, `Utterance_ID=12`, positive surprise after receiving good news
- `Persuasion for Good`: `proposition-of-donation` examples such as a direct ask after readiness appears

Dialogue context:

```text
Agent: The setup is usually much lighter than teams expect, especially when the current process is already documented.
User: Okay.
Agent: In many cases, teams can get a pilot running without changing everything at once.
User: That would make a big difference for us.
```

Current user utterance:

```text
Really? If that is true, then maybe we should actually try it.
```

Expected adaptive behavior:

- respond to readiness
- move toward commitment
- avoid drifting back into a generic explanation

## Case 02

- Case ID: `EXP-002-C02`
- Emotion label: `positive`
- Adaptive strategy label: `direct-ask-or-commitment`

Source grounding:

- `MELD`: `Dialogue_ID=2`, `Utterance_ID=2`, positive engaged agreement
- `Persuasion for Good`: `acknowledgement` plus `proposition-of-donation`

Dialogue context:

```text
Agent: We usually start by targeting the repetitive follow-up tasks that consume the most time.
User: That is definitely one of our problems.
Agent: If we focus just on that part first, the rollout tends to feel much safer.
User: Right.
```

Current user utterance:

```text
Yeah, I would be open to seeing what that first step actually looks like.
```

Expected adaptive behavior:

- acknowledge interest
- suggest a concrete next step
- keep momentum

## Case 03

- Case ID: `EXP-002-C03`
- Emotion label: `neutral`
- Adaptive strategy label: `evidence-or-benefit`

Source grounding:

- `MELD`: `Dialogue_ID=0`, `Utterance_ID=3`, neutral role-focused information request
- `Persuasion for Good`: `donation-information` and `logical-appeal`

Dialogue context:

```text
Agent: Our system is mainly used to manage follow-ups, reminders, and lead visibility in one place.
User: Okay.
Agent: It is typically most useful for teams that are losing time in manual coordination.
User: I see.
```

Current user utterance:

```text
So what would this actually do for us on a normal workday?
```

Expected adaptive behavior:

- explain practical benefit
- stay neutral and informative
- avoid premature closing language

## Case 04

- Case ID: `EXP-002-C04`
- Emotion label: `neutral`
- Adaptive strategy label: `evidence-or-benefit`

Source grounding:

- `MELD`: `Dialogue_ID=0`, `Utterance_ID=1`, calm informational exchange
- `Persuasion for Good`: `credibility-appeal`

Dialogue context:

```text
Agent: We work with service teams that need more consistency in early follow-up.
User: All right.
Agent: The main improvement usually comes from reducing missed handoffs and unclear next steps.
User: Okay.
```

Current user utterance:

```text
What makes you confident this works better than the tools we already have?
```

Expected adaptive behavior:

- answer with credibility and concrete value
- remain measured
- make the comparison legible

## Case 05

- Case ID: `EXP-002-C05`
- Emotion label: `skeptical-or-negative`
- Adaptive strategy label: `inquiry`

Source grounding:

- `MELD`: `Dialogue_ID=1`, `Utterance_ID=1`, frustrated rejection pattern
- `Persuasion for Good`: `task-related-inquiry` used to surface the concern before pushing

Dialogue context:

```text
Agent: We help teams improve response consistency and reduce dropped leads.
User: That is what every vendor says.
Agent: Fair point.
User: Exactly.
```

Current user utterance:

```text
You know what, forget it. Most of these tools just make the process more annoying.
```

Expected adaptive behavior:

- reduce pressure
- investigate the specific friction
- do not argue immediately

## Case 06

- Case ID: `EXP-002-C06`
- Emotion label: `skeptical-or-negative`
- Adaptive strategy label: `inquiry`

Source grounding:

- `MELD`: `Dialogue_ID=0`, `Utterance_ID=10`, overloaded negative reaction to more detail
- `Persuasion for Good`: `task-related-inquiry` and `acknowledgement`

Dialogue context:

```text
Agent: I can walk you through every feature if that helps.
User: I am not sure that is the issue.
Agent: Okay.
User: We have been through too many long software explanations already.
```

Current user utterance:

```text
No, please do not give me another feature tour unless this actually solves something specific for us.
```

Expected adaptive behavior:

- stop feature dumping
- ask what specific problem matters most
- show that the conversation can narrow to a real need
