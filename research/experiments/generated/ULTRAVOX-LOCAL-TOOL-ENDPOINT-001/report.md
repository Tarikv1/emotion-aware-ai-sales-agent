# ULTRAVOX-LOCAL-TOOL-ENDPOINT-001 Report

No Ultravox provider call was made.
No public tunnel was opened.
No real customer data, private audio, private transcripts, or side effects were used.

Endpoint: `http://127.0.0.1:8765/ultravox/project-sales-brain-next-move`
Cases passed: `8` / `8`
Missing token rejected: `true`
Invalid token rejected: `true`
Fake side-effect count: `0`
Unsupported claim count: `0`
Internal label leak count: `0`

## Cases

### case_001_what_is_this

- Buyer: What is this?
- HTTP status: `200`
- Passed: `true`
- Next action: `orient_buyer`

### case_002_existing_tools

- Buyer: I use ChatGPT and other tools.
- HTTP status: `200`
- Passed: `true`
- Next action: `differentiate_controlled_sales_guidance`

### case_003_price

- Buyer: How much is it?
- HTTP status: `200`
- Passed: `true`
- Next action: `clarify_pricing_context`

### case_004_not_team

- Buyer: I'm by myself, not a team.
- HTTP status: `200`
- Passed: `true`
- Next action: `reframe_for_individual_user`

### case_005_already_told_you

- Buyer: I already told you, coding and voice.
- HTTP status: `200`
- Passed: `true`
- Next action: `repair_memory_acknowledgement`

### case_006_signup_path

- Buyer: How do I sign up?
- HTTP status: `200`
- Passed: `true`
- Next action: `safe_signup_boundary`

### case_007_no_crm

- Buyer: Don't put me in CRM.
- HTTP status: `200`
- Passed: `true`
- Next action: `respect_contact_boundary`

### case_008_terminal_thanks

- Buyer: Ok, thanks.
- HTTP status: `200`
- Passed: `true`
- Next action: `end_call`
