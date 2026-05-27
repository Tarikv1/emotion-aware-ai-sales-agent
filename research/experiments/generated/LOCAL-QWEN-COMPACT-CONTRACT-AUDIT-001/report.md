# LOCAL-QWEN-COMPACT-CONTRACT-AUDIT-001

- Status: pass
- Contract: `LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002`
- Provider calls made: false
- OpenAI API calls made: false
- Live TTS calls made: false
- Runtime behavior changed: false
- Response text changed: false

## Before / Current

| Metric | Previous audit | Current audit |
| --- | ---: | ---: |
| deprecated_label_count | 189 | 0 |
| case_id_label_leak_count | 54 | 0 |
| generic_label_count | 126 | 0 |
| generalized_sales_move_count | 34 | 0 |
| verifier_pass_gold_section_fail_count | 15 | 0 |

## Dataset

- Rows: 80
- Flagged targets: 0
- Split counts: `{"test": 10, "train": 60, "validation": 10}`

## Eval

- Status: completed
- Adapter path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-002`
- Flagged outputs: 8
- Verifier-pass but gold-section-fail: 0

## Top Flagged Dataset Labels


## Top Flagged Eval Labels

- `act=coding_voice_use_case`: 1
- `sub=sounds_right`: 1
- `act=side_effect_boundary_request`: 1
- `sub=use_case_gap`: 1
- `act=coding_or_voice_use_case`: 1
- `sub=compare_competitor_context`: 1
- `sub=data_sharing_boundary`: 1
- `sub=current_tool_context`: 1
