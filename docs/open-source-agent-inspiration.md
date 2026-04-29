# Open-Source Agent Inspiration

Sources reviewed:

- `safishamsi/graphify`
- `Shubhamsaboo/awesome-llm-apps`
- `NousResearch/hermes-agent`
- `jamiepine/voicebox`
- `facebookresearch/tribev2`

## Useful Patterns

### Knowledge Graph Memory

Use graph-style project memory to make agent behavior explainable:

- extracted facts vs inferred relationships
- confidence on inferred links
- portable source paths
- graph reports that surface key concepts and surprising connections

This is useful for sales-agent product work because a sales assistant should explain why it believes a lead, objection, or emotional signal matters.

### Agent Platform Shape

The durable pieces to consider:

- skills for repeatable procedures
- plugins for integrations
- context files for project/session behavior
- scheduled tasks for follow-ups
- memory with user-visible privacy boundaries
- command/tool approval rules

### Voice Interface Caution

Voice workflows are useful for call simulation, coaching, and roleplay, but require:

- consent for cloned voices
- clear synthetic output labeling
- secure storage of voice samples
- human review before external use

### Multimodal Signal Research

TRIBE v2 is not implementation code for us, but it reinforces a useful product idea: emotional or sales signals are multimodal and time-aligned across language, voice, and visual context.

## Do Not Adopt Blindly

- Do not build hidden memory that users cannot inspect.
- Do not infer emotional state without uncertainty and user-visible framing.
- Do not clone or synthesize real customer voices without explicit permission.
- Do not import large templates when a smaller, owned implementation would be clearer.

