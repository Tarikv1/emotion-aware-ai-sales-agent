# LOCAL-QWEN-BALANCED-DATASET-CONSISTENCY-AUDIT-001

- Status: pass
- Total rows: 445
- Split counts: `{"ood_test": 10, "test": 66, "train": 304, "validation": 65}`
- Exact buyer-text overlap: False
- Near-duplicate overlap found: False
- OOD isolated: True
- Previous 4H17 issues resolved: True

## Held-Out Coverage

- validation: covered_by_train=True, unseen_core=0, unseen_action_sub=0
- test: covered_by_train=True, unseen_core=0, unseen_action_sub=0

## Before / After

- Validation unseen core: 6 -> 0
- Test unseen core: 2 -> 0
- Validation unseen action/sub: 5 -> 0
- Test unseen action/sub: 2 -> 0
