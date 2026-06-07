# Next-Step Policy

Universal guidance only.

## Purpose

Choose a next step that matches the buyer's interest, authority, risk level, and consent.

## Owns

- next-step timing
- avoiding premature close attempts
- send-path capture after interest
- callback and pass-along routing
- stop conditions

## Does Not Own

- exact send channels
- scheduling tools
- payment steps
- campaign-specific fulfillment capability

## When To Retrieve

Retrieve when the buyer shows interest, asks how to see something, gives contact details, is busy, asks for a callback, or refuses.

## Operating Rules

- Ask for the smallest useful next step.
- Do not ask for contact before interest unless the campaign explicitly supports it.
- If a destination is needed, ask for one destination.
- Confirm callback windows without adding extra questions.
- Stop after refusal or do-not-contact.

## Failure Modes

- treating interest as a paid close
- claiming a send, booking, or update happened when it did not
- asking another close while the buyer is objecting
- leaving a contact path unconfirmed

## Handoff To Campaign Overlay/Profile

Hand off campaign facts to the campaign overlay and campaign profile. The profile owns approved send, callback, and fulfillment facts.
