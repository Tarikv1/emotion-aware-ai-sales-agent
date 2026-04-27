# EXP-001 Case Pack

This file defines the first six curated prompt-comparison cases for the phase-1 baseline experiment.

## Case 01

- Case ID: `EXP-001-C01`
- Emotion label: `positive`
- Adaptive strategy label: `direct-ask-or-commitment`

Dialogue context:

```text
Agent: Thanks for taking a minute to chat today. We help small teams cut repetitive admin work by automating follow-up and reporting.
User: That actually sounds useful. We have been trying to reduce the time our team spends on manual updates.
Agent: That makes sense. What usually takes the most time right now?
User: Mostly status reporting and chasing people for updates.
```

Current user utterance:

```text
If it's easy to set up, I could see us trying something like that.
```

Expected adaptive behavior:

- move toward next-step commitment
- avoid over-explaining
- suggest a concrete trial or follow-up action

## Case 02

- Case ID: `EXP-001-C02`
- Emotion label: `positive`
- Adaptive strategy label: `direct-ask-or-commitment`

Dialogue context:

```text
Agent: Our platform helps local shops recover missed leads from web forms and social messages.
User: We do lose track of those sometimes.
Agent: A lot of owners tell us the same thing before they centralize everything.
User: Right, and then someone forgets to reply for a day or two.
```

Current user utterance:

```text
Honestly, if it really helps us respond faster, I'd be interested in seeing a demo.
```

Expected adaptive behavior:

- capitalize on willingness
- propose a clear next step
- keep tone confident and efficient

## Case 03

- Case ID: `EXP-001-C03`
- Emotion label: `neutral`
- Adaptive strategy label: `evidence-or-benefit`

Dialogue context:

```text
Agent: We support sales teams by organizing leads, reminders, and follow-up sequences in one place.
User: Okay.
Agent: Teams usually come to us when they want better visibility into who needs follow-up and when.
User: I see.
```

Current user utterance:

```text
How is this different from just using a shared spreadsheet?
```

Expected adaptive behavior:

- explain concrete benefit clearly
- stay informative rather than pushy
- make the answer easy to compare

## Case 04

- Case ID: `EXP-001-C04`
- Emotion label: `neutral`
- Adaptive strategy label: `evidence-or-benefit`

Dialogue context:

```text
Agent: We help service businesses keep track of inbound inquiries and automate the first stages of follow-up.
User: Okay, but we've already got a couple of tools in place.
Agent: Totally fair. A lot of teams start there and then look for something more unified later on.
User: Sure.
```

Current user utterance:

```text
What kind of time savings are companies actually seeing?
```

Expected adaptive behavior:

- answer with practical value
- use credible, concrete framing
- avoid pressure or emotional language

## Case 05

- Case ID: `EXP-001-C05`
- Emotion label: `skeptical-or-negative`
- Adaptive strategy label: `inquiry`

Dialogue context:

```text
Agent: We help teams improve follow-up consistency and reduce dropped leads.
User: We have heard that kind of pitch before.
Agent: I get that. A lot of tools sound similar at first.
User: Exactly.
```

Current user utterance:

```text
Most of these systems just create more work for us instead of solving anything.
```

Expected adaptive behavior:

- explore the objection before pitching harder
- ask a clarifying question
- lower pressure and show understanding indirectly

## Case 06

- Case ID: `EXP-001-C06`
- Emotion label: `skeptical-or-negative`
- Adaptive strategy label: `inquiry`

Dialogue context:

```text
Agent: We help businesses automate early lead qualification and customer follow-up.
User: We are very careful about adding anything new to the process.
Agent: That makes sense.
User: We have had bad experiences with software rollouts before.
```

Current user utterance:

```text
What worries me is paying for another tool and then finding out my team won't actually use it.
```

Expected adaptive behavior:

- focus on the underlying concern
- ask a useful follow-up question or narrow the risk
- avoid jumping straight to a hard close
