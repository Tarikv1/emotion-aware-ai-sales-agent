# Atlas Detailed Pricing Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Atlas Web Studio's coarse website ranges with the approved hybrid package and feature matrix while preventing every unprompted paid-price disclosure.

**Architecture:** Keep the compact system prompt responsible only for price-intent gating and quote selection. Store the detailed package and add-on catalog in the existing active `atlas_price_scope_cost_drivers.md` document, mirror the five existing whole-project variables in repo and live defaults, and validate the behavior through a new frozen ELEVENLABS-040 suite plus deterministic trace checks. Patch existing live documents in place and compare protected provider state before and after every write.

**Tech Stack:** Markdown prompt and KB documents, JSON dynamic variables and ElevenLabs simulation definitions, Python 3.11 validators and guarded API utilities, ElevenLabs dashboard/browser for test management, ElevenLabs API for exact readback and sanitized trace capture.

## Global Constraints

- Checkpoint ID is exactly `ELEVENLABS-040-detailed-pricing-control`.
- Active agent is exactly `agent_7801kt0g32zxf4f8x5zkykj7syty` named `web design`.
- Retain `gpt-5.5`, temperature `0.1`, reasoning effort `none`, and provider-normalized thinking budget `null`.
- Paid prices may appear only after explicit buyer price, cost, fee, range, ballpark, budget, affordability, monthly-charge, or add-on-cost intent.
- Capability, scope, mockup, free, catch, contract, and ordinary-interest questions must not disclose paid prices.
- Light copy refinement is included; full copywriting is separate.
- Hosting and ongoing support use separate care plans and are disclosed only when asked.
- Quote one relevant package or add-on range and at most one material scope question.
- Never mechanically add three or more features or calculate a final quote during the initial call.
- Portals, dashboards, custom APIs, user accounts, databases, complex payments, inventory synchronization, marketplaces, and custom business logic require scoping.
- Existing Analysis criteria and existing simulation definitions must not be edited or weakened.
- New tests use `gemini-2.5-flash` for both simulated user and evaluation model.
- Active KB attachment count and order remain exactly 17 and unchanged.
- Update active KB documents in place; do not create provider duplicates or broaden the attachment set.
- Preserve unrelated tools, tool IDs, MCP IDs, voice, first message, phone settings, LLM settings, and all unrelated dynamic variables.
- Procedures remain inactive.
- Do not place outbound calls.
- Provider labels are supporting evidence only; independently validate sanitized traces.

## File Map

**Modify:**

- `runtime/providers/elevenlabs_agents/variables/mikes_kitchen_dynamic_variable_defaults.json`: new default whole-project ranges and disclosure rule.
- `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md`: compact price gate, classification, one-range, and no-stacking rules.
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_offer_facts.md`: approved package defaults and commercial exclusions.
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md`: complete package, feature, care-plan, and quoting matrix.
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md`: no-unprompted-price and no-menu leakage output rules.

**Create:**

- `runtime/providers/elevenlabs_agents/tests/web_design_detailed_pricing_control_tests.json`: ten focused frozen simulations.
- `runtime/providers/elevenlabs_agents/manifests/web_design_detailed_pricing_control.package.json`: repo package metadata; not an active KB upload manifest.
- `scripts/validate_elevenlabs_040_detailed_pricing_control.py`: static contract validator.
- `scripts/apply_elevenlabs_040_detailed_pricing_control.py`: guarded prompt, dynamic-variable, and in-place KB patcher.
- `scripts/capture_elevenlabs_040_test_invocation.py`: sanitized invocation capture.
- `scripts/validate_elevenlabs_040_live_test_traces.py`: independent deterministic trace validator.
- `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/`: sanitized plans, requests, snapshots, captures, results, and report.

**Must remain unchanged:**

- `runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_config.json`
- `runtime/providers/elevenlabs_agents/analysis/atlas_web_studio_analysis_setup.md`
- Every pre-040 file under `runtime/providers/elevenlabs_agents/tests/`
- `runtime/providers/elevenlabs_agents/manifests/web_design_sales_spine_compression.package.json`
- `runtime/providers/elevenlabs_agents/procedures/`

---

### Task 1: Add The Failing Static Contract Validator

**Files:**

- Create: `scripts/validate_elevenlabs_040_detailed_pricing_control.py`
- Test: `scripts/validate_elevenlabs_040_detailed_pricing_control.py`

**Interfaces:**

- Consumes: approved design at `docs/superpowers/specs/2026-07-11-atlas-detailed-pricing-design.md`.
- Produces: callable functions `validate_dynamic_defaults()`, `validate_prompt_policy()`, `validate_pricing_kb()`, `validate_output_rules()`, `validate_tests()`, `validate_live_patcher()`, and `main() -> int`.

- [ ] **Step 1: Create the validator constants and assertions**

```python
CHECKPOINT_ID = "ELEVENLABS-040-detailed-pricing-control"
EXPECTED_PRICE_DEFAULTS = {
    "website_starting_price": "$500",
    "website_basic_site_range": "$900-$1,500",
    "website_light_feature_range": "$1,800-$3,000",
    "website_workflow_content_range": "$2,800-$4,500",
    "website_integration_heavy_range": "$4,000-$6,500",
    "website_premium_price_anchor": "$6,500",
}
EXPECTED_TEST_IDS = [
    "sim_040_capability_question_no_unprompted_price",
    "sim_040_free_mockup_question_no_paid_price",
    "sim_040_basic_site_direct_price",
    "sim_040_existing_site_request_form_add_on",
    "sim_040_new_site_booking_whole_project",
    "sim_040_multi_feature_no_price_stacking",
    "sim_040_direct_crm_integration_existing_site",
    "sim_040_portal_requires_scope",
    "sim_040_budget_fit_direct_answer",
    "sim_040_care_plan_only_when_asked",
]
```

The validator must read exact repo paths, assert the six defaults above, enforce a prompt word count of at most 1,900, assert all approved package/add-on/care-plan markers, assert exactly ten 040 tests in the specified order, and fail if any existing test, Analysis file, active manifest, or Procedure is changed in the working diff.

- [ ] **Step 2: Add focused callable validation functions**

```python
def validate_dynamic_defaults() -> None:
    defaults = read_json(DEFAULTS)
    for key, expected in EXPECTED_PRICE_DEFAULTS.items():
        assert_condition(defaults.get(key) == expected, f"{key} mismatch")


def validate_prompt_policy() -> None:
    prompt = read(PROMPT)
    assert_markers("prompt", prompt, PROMPT_MARKERS)
    assert_condition(word_count(prompt) <= 1900, "compact prompt exceeds 1,900 words")


def validate_tests() -> None:
    payload = read_json(TESTS)
    tests = payload.get("tests")
    assert_condition(isinstance(tests, list), "040 tests must be a list")
    assert_condition([item.get("test_id") for item in tests] == EXPECTED_TEST_IDS, "040 test IDs/order mismatch")
    assert_condition(all(item.get("simulated_user_model") == "gemini-2.5-flash" for item in tests), "simulated-user model mismatch")
    assert_condition(all(item.get("evaluation_model") == "gemini-2.5-flash" for item in tests), "evaluation model mismatch")
```

- [ ] **Step 3: Run the validator and verify the red gate**

Run:

```powershell
python scripts\validate_elevenlabs_040_detailed_pricing_control.py
```

Expected: exit `1` with missing 040 pricing policy, test, or patcher markers. It must not fail because of a Python syntax or import error.

- [ ] **Step 4: Commit the red validator**

```powershell
git add scripts\validate_elevenlabs_040_detailed_pricing_control.py
git commit -m "Add Atlas detailed pricing red gate"
```

---

### Task 2: Implement The Canonical Pricing Catalog

**Files:**

- Modify: `runtime/providers/elevenlabs_agents/variables/mikes_kitchen_dynamic_variable_defaults.json:15-24`
- Modify: `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_offer_facts.md:145-168`
- Modify: `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md:5-205`
- Modify: `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md`
- Test: `scripts/validate_elevenlabs_040_detailed_pricing_control.py::validate_dynamic_defaults`
- Test: `scripts/validate_elevenlabs_040_detailed_pricing_control.py::validate_pricing_kb`
- Test: `scripts/validate_elevenlabs_040_detailed_pricing_control.py::validate_output_rules`

**Interfaces:**

- Consumes: `EXPECTED_PRICE_DEFAULTS` from Task 1.
- Produces: one canonical active KB catalog with the exact package, feature, exclusion, and care-plan policy approved in the design.

- [ ] **Step 1: Update the six campaign defaults**

Replace only the six pricing values and tighten the disclosure rule:

```json
"website_starting_price": "$500",
"website_basic_site_range": "$900-$1,500",
"website_light_feature_range": "$1,800-$3,000",
"website_workflow_content_range": "$2,800-$4,500",
"website_integration_heavy_range": "$4,000-$6,500",
"website_premium_price_anchor": "$6,500",
"website_price_disclosure_rule": "only discuss paid pricing after explicit buyer price, cost, fee, range, ballpark, budget, affordability, monthly-charge, or add-on-cost intent; capability, scope, mockup, free, catch, contract, and ordinary-interest questions do not unlock paid pricing"
```

Do not change business context, value points, or the optional-upsell boundary.

- [ ] **Step 2: Replace the coarse package defaults in Offer Facts**

Use the existing placeholders for campaign-overridable whole-project bands:

```markdown
- Quick Launch: `$500-$800` for one adapted-template page.
- Essential Local: `{{website_basic_site_range}}` for three to five tailored-template pages.
- Custom Business: `{{website_light_feature_range}}` for five to eight pages with an original homepage direction.
- Growth Website: `{{website_workflow_content_range}}` for deeper content, CMS, filtering, or request workflows.
- Integration Website: `{{website_integration_heavy_range}}` for a new website with a standard CRM, calendar, payment, or automation integration.
- Starter Ecommerce: `$2,500-$5,000`.
- Advanced Ecommerce: `$5,000-$10,000+`.
- Portals and web applications: scoped separately.
```

Add explicit exclusions for third-party subscriptions, domains, paid plugins, transaction fees, stock assets, photography, full branding, translation, advertising, ongoing SEO, and tax.

- [ ] **Step 3: Rewrite the pricing KB around the approved decision matrix**

Preserve useful capability-first and portal-scope language, but replace the coarse feature-to-whole-band examples with these sections:

```markdown
## Hard Price Disclosure Gate
## New Website Versus Existing-Site Add-On
## Base Package Ladder
## Pages, Content, And Design Add-Ons
## Forms And Lead Capture Add-Ons
## Booking, CRM, Payments, And Automation Add-Ons
## Local Search And Analytics Add-Ons
## Ecommerce Add-Ons
## Languages, Membership, And Portal Boundaries
## Care Plans
## No Mechanical Stacking
## Range Selection
## Excluded Costs
```

Copy every approved range and boundary exactly from the design specification. Whole-project package rows must use campaign placeholders where one of the five established bands exists. Feature add-ons and care plans may use literal approved values.

- [ ] **Step 4: Add output-quality prohibitions**

Add exact rules:

```markdown
- Never disclose a paid price before explicit buyer price intent.
- A capability, scope, mockup, free, catch, contract, or ordinary-interest question does not unlock paid pricing.
- Do not read the package or feature menu aloud.
- Do not add three or more features into a final quote.
- Do not charge twice for overlapping work.
- Use one relevant range and at most one material scope question.
- Do not quote a fixed price or ceiling for portals, dashboards, APIs, accounts, databases, or custom business logic.
```

- [ ] **Step 5: Run focused catalog checks**

Run:

```powershell
python -c "import scripts.validate_elevenlabs_040_detailed_pricing_control as v; v.validate_dynamic_defaults(); v.validate_pricing_kb(); v.validate_output_rules(); print('catalog checks: pass')"
```

Expected: `catalog checks: pass`.

- [ ] **Step 6: Commit the pricing catalog**

```powershell
git add runtime/providers/elevenlabs_agents/variables/mikes_kitchen_dynamic_variable_defaults.json runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_offer_facts.md runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md
git commit -m "Define detailed Atlas website pricing"
```

---

### Task 3: Implement The Compact Prompt Decision Policy

**Files:**

- Modify: `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md:11-39`
- Modify: `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md:112-121`
- Test: `scripts/validate_elevenlabs_040_detailed_pricing_control.py::validate_prompt_policy`

**Interfaces:**

- Consumes: detailed catalog in `atlas_price_scope_cost_drivers.md`.
- Produces: compact runtime algorithm that gates retrieval and quoting without embedding the full menu.

- [ ] **Step 1: Replace the coarse pricing rule with the hard gate**

The prompt must state, compactly and exactly in meaning:

```markdown
Paid-price gate: disclose paid pricing only after the buyer explicitly asks price, cost, fee, range, ballpark, budget, affordability, monthly charge, or add-on cost. Capability, scope, mockup, free, catch, contract, and ordinary-interest questions never unlock paid pricing. Before a price trigger, answer normally with no dollar amount, range, package, starting price, or paid-price hint.
```

- [ ] **Step 2: Add context and complexity classification**

```markdown
After price intent: new website -> one whole-project band; compatible existing site -> one relevant add-on range; unclear -> ask whether this is a new site or an addition. Classify as simple (native/embed/plugin), integrated (data moves or automation runs), or custom (API/accounts/database/permissions/business logic).
```

- [ ] **Step 3: Add response and stacking controls**

```markdown
Quote one relevant range, name one scope driver, and ask at most one necessary question. Never read the menu. One or two independent add-ons may be discussed; three or more move to a whole-project band. Never add ranges into a final quote or charge overlapping work twice. Portals, dashboards, APIs, accounts, databases, complex payments, inventory sync, marketplaces, and custom logic require scope without a fixed price or ceiling.
```

- [ ] **Step 4: Preserve compactness**

Remove superseded scheduling, CRM, and generic price wording rather than appending duplicate rules. Keep the prompt at or below 1,900 words.

- [ ] **Step 5: Run the focused prompt check**

```powershell
python -c "import scripts.validate_elevenlabs_040_detailed_pricing_control as v; v.validate_prompt_policy(); print('prompt policy: pass')"
```

Expected: `prompt policy: pass` and validator-reported prompt word count at or below 1,900.

- [ ] **Step 6: Commit the prompt policy**

```powershell
git add runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md
git commit -m "Gate Atlas paid pricing on buyer intent"
```

---

### Task 4: Add The Frozen ELEVENLABS-040 Regression Suite

**Files:**

- Create: `runtime/providers/elevenlabs_agents/tests/web_design_detailed_pricing_control_tests.json`
- Create: `runtime/providers/elevenlabs_agents/manifests/web_design_detailed_pricing_control.package.json`
- Test: `scripts/validate_elevenlabs_040_detailed_pricing_control.py::validate_tests`

**Interfaces:**

- Consumes: package ranges and disclosure gate from Tasks 2 and 3.
- Produces: ten ordered test definitions with no edits to any pre-040 test or Analysis criterion.

- [ ] **Step 1: Define shared dynamic variables**

Use:

```json
{
  "agent_name": "Emma",
  "company_name": "Atlas Web Studio",
  "offer": "free homepage mockup",
  "website_starting_price": "$500",
  "website_basic_site_range": "$900-$1,500",
  "website_light_feature_range": "$1,800-$3,000",
  "website_workflow_content_range": "$2,800-$4,500",
  "website_integration_heavy_range": "$4,000-$6,500",
  "website_premium_price_anchor": "$6,500",
  "source_package_id": "ELEVENLABS-040-detailed-pricing-control"
}
```

- [ ] **Step 2: Add the ten exact scenarios**

Each test uses 6-12 maximum turns and `gemini-2.5-flash` for both models:

```text
sim_040_capability_question_no_unprompted_price
Buyer asks whether Atlas can add booking, CRM, and payments but never asks cost.
Pass: confident capability answer, no dollar amount, range, package, starting price, or care-plan price.

sim_040_free_mockup_question_no_paid_price
Buyer asks whether the mockup is really free and whether there is a catch.
Pass: process-risk answer only; no paid website price.

sim_040_basic_site_direct_price
Buyer explicitly asks what a basic three-to-five-page local-business site costs.
Pass: one `$900-$1,500` whole-project range and one relevant driver at most.

sim_040_existing_site_request_form_add_on
Buyer states they have an existing compatible site and asks the cost of adding a simple appointment-request form.
Pass: one `$100-$250` add-on range; no whole-site package dump.

sim_040_new_site_booking_whole_project
Buyer asks what a new straightforward site with a simple request form costs, then asks about live calendar integration.
Pass: `$900-$1,500` for simple request; later one higher relevant band for live integration; no add-on/whole-site confusion.

sim_040_multi_feature_no_price_stacking
Buyer asks for a new site with booking, CRM, payments, service-area pages, and a blog, then asks total cost.
Pass: one likely whole-project band and scope driver; no arithmetic sum or feature-menu recital.

sim_040_direct_crm_integration_existing_site
Buyer has an existing compatible site and asks what a direct CRM integration costs.
Pass: `$1,000-$2,500+`, an API/data-flow caveat, and no claim that every behavior is included.

sim_040_portal_requires_scope
Buyer asks how much a parent portal with accounts and progress dashboards costs.
Pass: no numeric quote or ceiling; scope accounts, data, permissions, security, and integrations.

sim_040_budget_fit_direct_answer
Buyer says the budget is `$1,200` and asks whether a basic site fits.
Pass: direct fit answer against `$900-$1,500`; no unrelated package menu.

sim_040_care_plan_only_when_asked
Buyer first asks about ordinary site capability, then explicitly asks monthly hosting and maintenance cost.
Pass: no care price before the ongoing-cost question; after it, one relevant `$79`, `$149`, or `$249` plan with scope.
```

- [ ] **Step 3: Create package metadata**

The package manifest must list the new test file and the existing prompt plus the three modified active KB documents. It must state that it is not an active KB upload manifest and that Analysis, Procedures, and existing tests remain unchanged.

- [ ] **Step 4: Run the test-definition check**

```powershell
python -c "import scripts.validate_elevenlabs_040_detailed_pricing_control as v; v.validate_tests(); print('040 tests: pass')"
```

Expected: `040 tests: pass`, exactly ten IDs, correct order, and 6-12 turns each.

- [ ] **Step 5: Commit the frozen test contract**

```powershell
git add runtime/providers/elevenlabs_agents/tests/web_design_detailed_pricing_control_tests.json runtime/providers/elevenlabs_agents/manifests/web_design_detailed_pricing_control.package.json
git commit -m "Add Atlas detailed pricing regression suite"
```

---

### Task 5: Build The Guarded Live Patcher

**Files:**

- Create: `scripts/apply_elevenlabs_040_detailed_pricing_control.py`
- Test: `scripts/validate_elevenlabs_040_detailed_pricing_control.py::validate_live_patcher`

**Interfaces:**

- Consumes: prompt, three KB files, six pricing defaults, and existing guarded helpers from `apply_elevenlabs_039_independent_test_hardening.py` and `apply_elevenlabs_038_end_call_terminal_control.py`.
- Produces: dry-run by default and live write only with exact token `confirm-provider-write`.

- [ ] **Step 1: Define target surface**

```python
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
AGENT_NAME = "web design"
CONFIRM_TOKEN = "confirm-provider-write"
TARGET_LLM = {
    "llm": "gpt-5.5",
    "temperature": 0.1,
    "thinking_budget": None,
    "reasoning_effort": "none",
}
TARGET_PRICE_VARIABLES = {
    "website_starting_price": "$500",
    "website_basic_site_range": "$900-$1,500",
    "website_light_feature_range": "$1,800-$3,000",
    "website_workflow_content_range": "$2,800-$4,500",
    "website_integration_heavy_range": "$4,000-$6,500",
    "website_premium_price_anchor": "$6,500",
}
KB_DOCS = (
    "atlas_offer_facts.md",
    "atlas_price_scope_cost_drivers.md",
    "atlas_output_quality_rules.md",
)
```

- [ ] **Step 2: Merge only approved dynamic-variable keys**

```python
def merged_dynamic_variables(agent: dict[str, Any]) -> dict[str, Any]:
    conversation_config = agent.get("conversation_config")
    if not isinstance(conversation_config, dict):
        raise ValueError("agent conversation_config must be an object")
    agent_config = conversation_config.get("agent")
    if not isinstance(agent_config, dict):
        raise ValueError("agent conversation_config.agent must be an object")
    dynamic = copy.deepcopy(agent_config.get("dynamic_variables") or {})
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("agent dynamic_variable_placeholders must be an object")
    placeholders.update(TARGET_PRICE_VARIABLES)
    dynamic["dynamic_variable_placeholders"] = placeholders
    return dynamic
```

Fail safely if either dynamic-variable container is not an object. Never replace unrelated variables such as `business_name`, `business_type`, or `city`.

- [ ] **Step 3: Build the minimal agent patch**

```python
def patch_body(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": PROMPT_PATH.read_text(encoding="utf-8").strip()},
                "dynamic_variables": merged_dynamic_variables(agent),
            }
        }
    }
```

Do not include voice, LLM, first message, phone, tools, KB attachments, Analysis, or Procedures in the write body.

- [ ] **Step 4: Add protected-state fingerprints**

Create a comparison that removes only the approved prompt text and six approved dynamic-variable values before hashing. Preserve and compare:

```python
def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def collateral_state(agent: dict[str, Any]) -> dict[str, Any]:
    state = guards.protected_agent_state(copy.deepcopy(agent))
    agent_config = state["conversation_config"]["agent"]
    prompt = agent_config["prompt"]
    prompt.pop("prompt", None)
    dynamic = agent_config.get("dynamic_variables")
    if not isinstance(dynamic, dict):
        raise ValueError("protected dynamic_variables must be an object")
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("protected dynamic_variable_placeholders must be an object")
    for key in TARGET_PRICE_VARIABLES:
        placeholders.pop(key, None)
    return state
```

Preserve and compare:

```python
{
    "knowledge_base_ids_in_order": preflight["knowledge_base_ids_in_order"],
    "unrelated_tool_fingerprint": preflight["unrelated_tool_fingerprint"],
    "analysis_criterion_ids_in_order": preflight["analysis_criterion_ids_in_order"],
    "procedures_inactive": preflight["procedures_inactive"],
    "collateral_state_sha256": canonical_sha256(collateral_state(agent)),
}
```

The patch must stop on any mismatch and preserve the exact provider error without a blind retry.

- [ ] **Step 5: Add evidence outputs**

Write sanitized files under `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/`:

```text
live_agent_pre_patch_snapshot.json
live_agent_patch_plan.json
live_agent_patch_requests.json
live_agent_patch_result.json
live_agent_post_patch_snapshot.json
live_dynamic_variables_readback.json
unrelated_tool_fingerprint_before.json
unrelated_tool_fingerprint_after.json
```

- [ ] **Step 6: Run patcher validation and dry run**

```powershell
python -c "import scripts.validate_elevenlabs_040_detailed_pricing_control as v; v.validate_live_patcher(); print('live patcher: pass')"
python scripts\apply_elevenlabs_040_detailed_pricing_control.py
```

Expected: validator passes; patcher reports `plan_only_missing_confirmation` and `provider_writes_made: false`.

- [ ] **Step 7: Commit the guarded patcher**

```powershell
git add scripts\apply_elevenlabs_040_detailed_pricing_control.py research/experiments/generated/ELEVENLABS-040-detailed-pricing-control
git commit -m "Add guarded Atlas pricing patcher"
```

---

### Task 6: Add Independent Trace Capture And Validation

**Files:**

- Create: `scripts/capture_elevenlabs_040_test_invocation.py`
- Create: `scripts/validate_elevenlabs_040_live_test_traces.py`
- Test: `scripts/validate_elevenlabs_040_detailed_pricing_control.py`

**Interfaces:**

- Consumes: an ElevenLabs invocation ID for exactly the ten 040 tests.
- Produces: sanitized capture JSON and deterministic pass/fail JSON independent of provider labels.

- [ ] **Step 1: Reuse the sanitized 039 capture implementation**

```python
import capture_elevenlabs_039_test_invocation as capture

capture.CHECKPOINT_ID = "ELEVENLABS-040-detailed-pricing-control"
capture.EXPECTED_SYNTHETIC_EMAILS = set()

if __name__ == "__main__":
    raise SystemExit(capture.main())
```

Do not weaken phone, token, authorization, customer, or email redaction.

- [ ] **Step 2: Define deterministic price-intent matching**

```python
PRICE_TRIGGER_RE = re.compile(
    r"\b(?:how much|cost|price|charge|fee|range|ballpark|budget|afford|monthly|extra)\b",
    re.IGNORECASE,
)
PAID_PRICE_RE = re.compile(
    r"(?:\$\s?\d[\d,]*(?:\s?(?:-|to)\s?\$?\d[\d,]*)?|\b\d+\s?(?:dollars?|per month|monthly)\b)",
    re.IGNORECASE,
)
```

The validator must identify the first buyer price trigger and fail any agent paid-price disclosure before it.

- [ ] **Step 3: Add scenario-specific assertions**

Use an `EXPECTED_TESTS` mapping keyed by the ten test IDs. Assert:

- provider and repo test names match;
- ordered responses exist;
- no price appears before buyer intent;
- expected ranges appear only in the relevant scenarios;
- no response contains more than two approved ranges;
- multi-feature output contains no arithmetic total;
- existing-site and whole-project classifications are correct;
- portal output contains no numeric paid price;
- care-plan price appears only after the ongoing-cost question;
- no unsupported fixed quote, menu dump, or guaranteed ceiling appears.

- [ ] **Step 4: Test the validator against a synthetic failing fixture**

Create a temporary in-memory trace in the module self-test path where the buyer asks only capability and Emma says `$4,000-$6,500`. Assert that the failure includes `unprompted_paid_price`.

Run:

```powershell
python scripts\validate_elevenlabs_040_live_test_traces.py --self-test
```

Expected: `self-test: pass` because the validator detects the deliberately invalid trace.

- [ ] **Step 5: Commit independent verification tooling**

```powershell
git add scripts\capture_elevenlabs_040_test_invocation.py scripts\validate_elevenlabs_040_live_test_traces.py
git commit -m "Independently validate Atlas pricing traces"
```

---

### Task 7: Run The Full Repo Gate

**Files:**

- Modify only if validation reveals a product or utility defect.
- Do not modify existing test success criteria or Analysis criteria.

**Interfaces:**

- Consumes: Tasks 1-6.
- Produces: a green repo state before any live provider write.

- [ ] **Step 1: Run the new validator**

```powershell
python scripts\validate_elevenlabs_040_detailed_pricing_control.py
```

Expected: `status: pass`, ten tests, prompt at or below 1,900 words, existing tests unchanged, Analysis unchanged, active manifest unchanged, and Procedures unchanged.

- [ ] **Step 2: Run regression validators**

```powershell
python scripts\validate_elevenlabs_039_end_call_edge_case_hardening.py
python scripts\validate_elevenlabs_038_end_call_terminal_control.py
python scripts\validate_elevenlabs_037_confident_capability_control.py
python scripts\validate_elevenlabs_036_natural_sales_scenarios_tests.py
python scripts\validate_elevenlabs_034_human_phone_naturalness.py
python scripts\validate_elevenlabs_033_email_confirmation_precision.py
python scripts\validate_elevenlabs_032_final_runtime_polish.py
python scripts\validate_elevenlabs_031_runtime_elite_hardening.py
python scripts\validate_elevenlabs_030_live_transcript_failure_hardening.py
git diff --check
```

Expected: every command exits `0`.

- [ ] **Step 3: Verify forbidden files are unchanged**

```powershell
git diff --name-only -- runtime/providers/elevenlabs_agents/analysis runtime/providers/elevenlabs_agents/tests | Select-String -NotMatch 'web_design_detailed_pricing_control_tests.json'
```

Expected: no output.

- [ ] **Step 4: Commit any validator-only correction**

Only if required, stage the exact utility defect fix and commit it separately. Do not change product behavior merely to satisfy a faulty matcher.

---

### Task 8: Apply The Guarded Live Product Patch

**Files:**

- Generate: `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_agent_*.json`
- Generate: `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/unrelated_tool_fingerprint_*.json`

**Interfaces:**

- Consumes: fully green repo gate and `ELEVENLABS_API_KEY` for exact provider readback/write.
- Produces: live prompt, three in-place KB updates, and six dynamic-variable changes only.

- [ ] **Step 1: Perform a fresh live readback**

Verify before writing:

```text
agent ID/name exact
LLM gpt-5.5 / temperature 0.1 / reasoning none
17 unique KB attachments in manifest order
one built-in end_call and zero custom/server duplicates
30 Analysis criteria in existing order
Procedures inactive
unrelated tool fingerprint captured
voice, first message, phone settings, and unrelated dynamic variables captured
```

- [ ] **Step 2: Apply exactly one guarded provider operation**

```powershell
python scripts\apply_elevenlabs_040_detailed_pricing_control.py --confirm-provider-write confirm-provider-write
```

Expected: three KB update responses and one agent prompt/dynamic-variable PATCH succeed. Stop immediately on any API error; preserve the exact error and do not blindly retry.

- [ ] **Step 3: Read back and verify**

Expected final state:

```text
prompt exact repo match
six live price variables exact
three KB document IDs unchanged
17 KB attachments/order unchanged
one built-in end_call
zero custom/server end_call duplicates
unrelated tool fingerprint unchanged
30 Analysis criteria unchanged
Procedures inactive
LLM, voice, first message, phone settings, and unrelated variables unchanged
```

- [ ] **Step 4: Commit sanitized provider evidence**

```powershell
git add research/experiments/generated/ELEVENLABS-040-detailed-pricing-control
git commit -m "Record live Atlas pricing patch"
```

---

### Task 9: Create And Run The 040 Tests Inside ElevenLabs

**Files:**

- Generate: `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_mapping.json`
- Generate: `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_run_result.json`
- Generate: `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_capture.json`
- Generate: `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_independent.json`

**Interfaces:**

- Consumes: frozen repo test JSON and patched live agent.
- Produces: provider and independent results for all ten exact tests.

- [ ] **Step 1: Use the signed-in ElevenLabs dashboard**

Create or reuse a folder named exactly `ELEVENLABS-040-detailed-pricing-control`. Create exactly the ten tests from the repo JSON with unchanged scenario, history, success condition, dynamic variables, models, and turn limits. Do not edit any pre-existing test or Analysis criterion.

- [ ] **Step 2: Save the test-ID mapping**

Record each repo test ID, exact dashboard test name, and provider test ID in `live_test_mapping.json`. Sanitize all evidence.

- [ ] **Step 3: Run the ten tests once inside ElevenLabs**

Do not place a call. Save the invocation ID and provider statuses. A provider failure is evidence to inspect, not permission to loosen a criterion.

- [ ] **Step 4: Capture the invocation read-only**

```powershell
$invocationId = (Get-Content -Raw research\experiments\generated\ELEVENLABS-040-detailed-pricing-control\live_test_run_result.json | ConvertFrom-Json).invocation_id
python scripts\capture_elevenlabs_040_test_invocation.py --invocation-id $invocationId --output research\experiments\generated\ELEVENLABS-040-detailed-pricing-control\live_test_capture.json
```

- [ ] **Step 5: Run independent deterministic validation**

```powershell
python scripts\validate_elevenlabs_040_live_test_traces.py --input research\experiments\generated\ELEVENLABS-040-detailed-pricing-control\live_test_capture.json --output research\experiments\generated\ELEVENLABS-040-detailed-pricing-control\live_test_independent.json
```

Expected: `independent_status: pass`, ten passes, complete coverage, and no inconclusives.

- [ ] **Step 6: Fix only genuine product defects**

If a trace fails, classify it as product defect, provider evaluator defect, test-definition defect, or incomplete simulation. Change the prompt or active pricing KB only for a genuine product defect. Do not weaken the frozen test criterion. Rerun only the affected test until stable, then rerun the complete ten-test suite once.

- [ ] **Step 7: Commit test evidence**

```powershell
git add research/experiments/generated/ELEVENLABS-040-detailed-pricing-control
git commit -m "Verify Atlas detailed pricing behavior"
```

---

### Task 10: Final Readback, Report, And Publication

**Files:**

- Create: `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/final_live_readback.json`
- Create: `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/report.md`

**Interfaces:**

- Consumes: final live provider state and complete 040 invocation.
- Produces: final evidence, commit, and remote branch state.

- [ ] **Step 1: Repeat the read-only live verification**

Confirm the exact final prompt, six price variables, three KB document IDs, 17-document order, one built-in `end_call`, zero duplicates, unchanged unrelated-tool fingerprint, 30 Analysis criteria, inactive Procedures, and preserved LLM/voice/first-message/phone state.

- [ ] **Step 2: Rerun all validators**

Run the exact command chain from Task 7 plus both independent trace validators. Expected: every command exits `0`.

- [ ] **Step 3: Write the report**

Report:

```text
pre-change and final repo HEAD
files changed
old and new price defaults
package and add-on catalog result
unprompted-price gate result
provider and independent test counts
live agent ID/name and LLM config
KB count/order
Analysis count
Procedure status
unrelated-tool fingerprint comparison
all validator exit codes
all provider/API/browser failures
confirmation that no outbound calls ran
```

- [ ] **Step 4: Verify, commit, and push**

```powershell
git diff --check
git add research/experiments/generated/ELEVENLABS-040-detailed-pricing-control
git commit -m "Complete Atlas detailed pricing control"
git push origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

Expected: local HEAD equals `origin/main`. Do not claim PSTN readiness because no real call is part of this plan.
