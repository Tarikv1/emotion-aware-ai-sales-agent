# NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001

- Status: pass
- Cases: 21
- Campaign coverage: b2b_saas, generic_insurance, generic_telecom, home_services, public_openai_plan, routesignal_preservation
- Selector/runtime disagreements: 17
- Candidate response hashes recorded: 21
- Raw candidate responses in shadow records: 0
- Safety blockers: 0
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false
- Live selector control: false
- Response replacement: false

## Disagreement By Campaign

- b2b_saas: selector_possible_improvement=1, selector_possible_regression=2
- generic_insurance: selector_possible_regression=3
- generic_telecom: selector_possible_improvement=1, selector_possible_regression=2
- home_services: selector_possible_regression=2, unknown=1
- public_openai_plan: same_action=4, selector_possible_regression=1
- routesignal_preservation: selector_possible_regression=4
