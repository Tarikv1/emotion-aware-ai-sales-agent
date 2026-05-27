# LOCAL-QWEN-BALANCED-DATASET-REVIEW-001

- Status: pass
- Dataset rows: 445
- Sampled rows: 110
- Review classifications: `{"acceptable":46,"warning":64}`
- Held-out exact overlap: false
- Held-out near-duplicate overlap: false
- Local model calls made: false
- Provider/OpenAI/TTS calls made: false
- Runtime behavior changed: false
- Response text changed: false

## Dataset Counts

- Split counts: `{"ood_test":10,"test":66,"train":304,"validation":65}`
- Semantic group counts: `{"adoption_current_tool_context":45,"individual_not_team_and_team_scope":45,"objections_and_competitor_context":45,"orientation_or_explanation":45,"plan_change_and_signup":45,"plan_fit_and_recommendation":45,"price_and_value":45,"safety_and_boundary":45,"usage_intensity":30,"use_case_scope":45}`
- Source type counts: `{"deterministic_paraphrase":267,"live_sanitized":51,"negative_control":24,"ood_control":10,"original_gold":5,"synthetic_control":88}`
- Target-card usage count: 38

## Diversity And Duplication

- Buyer text diversity: `{"average_word_count":8.93,"median_word_count":9,"row_count":445,"top_repeated_buyer_text_templates":[{"count":31,"template":"{object}"},{"count":11,"template":"{object} only"},{"count":10,"template":"i am {object}"},{"count":10,"template":"how much is {plan}"},{"count":10,"template":"can i {object}"},{"count":8,"template":"{object} {object}"},{"count":8,"template":"{object} and {object}"},{"count":8,"template":"i need {object} and {object} help"},{"count":6,"template":"this is {plan} {object} {object}"},{"count":5,"template":"we need {plan} for {object} and {object}"},{"count":5,"template":"what is the {plan} price"},{"count":5,"template":"what does {plan} cost"},{"count":5,"template":"just tell me {plan} cost"},{"count":5,"template":"tell me the {plan} price without selling me"},{"count":5,"template":"can i {object} and {object}"},{"count":5,"template":"where do i {object}"},{"count":5,"template":"ok i ll check that {object}"},{"count":5,"template":"{object} that is all"},{"count":5,"template":"sounds fine i will {object}"},{"count":5,"template":"if i choose {plan} now can i {object}"}],"total_token_count":3976,"type_token_ratio":0.066,"unique_buyer_template_count":109,"unique_buyer_text_count":445,"unique_token_count":263}`
- Say diversity: `{"top_repeated_exact_say":[{"count":15,"say":"Sounds good - you can check that and stop here."},{"count":13,"say":"wrong product is not the right fit for this plan conversation, so I would stop there."},{"count":10,"say":"For Plus price, answer the price directly first; plan fit comes after usage context."},{"count":10,"say":"For Pro price, answer the price directly first; then compare whether Pro is actually needed."},{"count":9,"say":"Got it - no current AI tool. What would you want the first AI tool to help with?"},{"count":8,"say":"Plus enough depends on use case and intensity. What would you use it for most?"},{"count":6,"say":"Got it - you already use ChatGPT. Where does that setup still fall short?"},{"count":6,"say":"Enterprise and security and procurement sounds like an Enterprise security discussion. The next step is confirming the buyer and review owner."},{"count":5,"say":"Enterprise and SSO and legal review sounds like an Enterprise security discussion. The next step is confirming the buyer and review owner."},{"count":5,"say":"For Pro cost, answer the price directly first; then compare whether Pro is actually needed."},{"count":5,"say":"For Plus cost, answer the price directly first; plan fit comes after usage context."},{"count":5,"say":"start lower and upgrade later is a plan-change question. Answer it directly, then keep the choice reversible."},{"count":5,"say":"For sign up, keep it self-serve and do not claim any signup action was taken."},{"count":5,"say":"upgrade midcycle is a plan-change question. Answer it directly, then keep the choice reversible."},{"count":5,"say":"For close this myself online, keep it self-serve and do not claim any signup action was taken."},{"count":5,"say":"Plus now and move up later is a plan-change question. Answer it directly, then keep the choice reversible."},{"count":5,"say":"For self-serve signup path, keep it self-serve and do not claim any signup action was taken."},{"count":4,"say":"plans are plan categories. I would explain them first, then ask which use case matters most."},{"count":4,"say":"model or subscription are different questions: one is the AI model, the other is the subscription plan. Which part are you choosing?"},{"count":4,"say":"For who are you with, I should stay clear: I can help compare plans, but I should not claim official affiliation."}],"top_repeated_say_patterns":[{"count":31,"pattern":"got it {object} and {object} are you using that lightly moderately or heavily"},{"count":17,"pattern":"{object} is not the right fit for this plan conversation so i would stop there"},{"count":15,"pattern":"for {object} keep it self serve and do not claim any signup action was taken"},{"count":15,"pattern":"sounds good you can check that and stop here"},{"count":12,"pattern":"understood {object} and {object} how heavily do you expect to use it"},{"count":12,"pattern":"fair {object} the plan only makes sense if the use case saves enough time or quality pain"},{"count":12,"pattern":"understood {object} no outside action is needed here"},{"count":11,"pattern":"i should not claim {object} i can still help you compare plan fit from your use case"},{"count":11,"pattern":"got it {object} how often would you use it"},{"count":11,"pattern":"i should not provide {object} i can summarize the safe next step instead"},{"count":11,"pattern":"for {object} i should answer only what is supported and avoid inventing details"},{"count":10,"pattern":"got it {object} what would you mainly use it for"},{"count":10,"pattern":"got it {object} what tasks are creating that heavier demand"},{"count":10,"pattern":"for {plan} price answer the price directly first plan fit comes after usage context"},{"count":10,"pattern":"for {plan} price answer the price directly first then compare whether {plan} is actually needed"},{"count":9,"pattern":"got it you already use {tool} where does that setup still fall short"},{"count":9,"pattern":"got it {tool} or {tool} what do you use it for most"},{"count":9,"pattern":"got it {object} what would you want the first ai tool to help with"},{"count":8,"pattern":"{object} are plan categories i would explain them first then ask which use case matters most"},{"count":8,"pattern":"for {object} i should stay clear i can help compare plans but i should not claim official affiliation"}],"unique_say_count":109,"unique_say_skeleton_count":64}`

## Consistency

- Preserve/avoid: `{"avoid_present_in_say_count":0,"preserve_missing_in_say_count":0}`
- Facts: `{"facts_not_approved_count":0}`
- Action/strategy: `{"card_mismatch_count":0}`
- Safety boundary: `{"side_effect_risk_count":0}`
- Verifier: `{"verifier_failure_count":0}`

## Sample Coverage

{"ood_rows":10,"requirements_met":{"all_ood_rows":true,"five_rows_per_semantic_group":true,"source_type_minimums":true,"test_minimum":true,"validation_minimum":true},"sampled_row_count":110,"semantic_group_counts":{"adoption_current_tool_context":29,"individual_not_team_and_team_scope":5,"objections_and_competitor_context":5,"orientation_or_explanation":5,"plan_change_and_signup":5,"plan_fit_and_recommendation":14,"price_and_value":16,"safety_and_boundary":11,"usage_intensity":5,"use_case_scope":5},"semantic_group_minimum":5,"source_type_counts":{"deterministic_paraphrase":40,"live_sanitized":15,"negative_control":10,"ood_control":10,"original_gold":4,"synthetic_control":31},"source_type_minimums":{"deterministic_paraphrase":10,"live_sanitized":10,"negative_control":10,"synthetic_control":10},"test_rows":10,"validation_rows":11}

## Representative Row Samples

### balanced_adoption_current_tool_context_001

- split: train
- source_type: synthetic_control
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_chatgpt_user
- sanitized_buyer_text: I use ChatGPT now.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT"],"preserve":["ChatGPT"],"rel":"none","say":"Got it - you already use ChatGPT. Where does that setup still fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_user","update":{"adoption":"current_chatgpt_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use ChatGPT. Where does that setup still fall short?
- preserve: `["ChatGPT"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_adoption_current_tool_context_002

- split: train
- source_type: synthetic_control
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_other_ai_user
- sanitized_buyer_text: I use Claude.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["Claude"],"preserve":["Claude"],"rel":"none","say":"Got it - you already use Claude. What gap are you trying to solve beyond that?","strategy":"diagnose_before_recommend","sub":"current_other_ai_user","update":{"adoption":"current_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Claude"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use Claude. What gap are you trying to solve beyond that?
- preserve: `["Claude"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_adoption_current_tool_context_003

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_and_other_ai
- sanitized_buyer_text: I use ChatGPT and other AI tools.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT or"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","other AI tools"],"preserve":["ChatGPT","other AI tools"],"rel":"and","say":"Got it - you use ChatGPT and other AI tools. Where does the current setup fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_and_other_ai_user","update":{"adoption":"current_chatgpt_and_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","other AI tools"],"must_not_include":["ChatGPT or"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you use ChatGPT and other AI tools. Where does the current setup fall short?
- preserve: `["ChatGPT","other AI tools"]`
- avoid: `["ChatGPT or"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_adoption_current_tool_context_004

- split: train
- source_type: original_gold
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_or_other_uncertain
- sanitized_buyer_text: I use ChatGPT or maybe Claude.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT and Claude"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","Claude"],"preserve":["ChatGPT","Claude"],"rel":"or","say":"Got it - ChatGPT or Claude. What do you use it for most?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"current_chatgpt_or_other_ai_unknown","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","Claude"],"must_not_include":["ChatGPT and Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - ChatGPT or Claude. What do you use it for most?
- preserve: `["ChatGPT","Claude"]`
- avoid: `["ChatGPT and Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_adoption_current_tool_context_005

- split: train
- source_type: synthetic_control
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_no_current_ai_tool
- sanitized_buyer_text: I do not use any AI tool right now.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["already use ChatGPT","already use Claude"],"block":["adoption_state"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"information","neg":"none","obj":["no current AI tool"],"preserve":["no current AI tool"],"rel":"none","say":"Got it - no current AI tool. What would you want the first AI tool to help with?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["no current AI tool"],"must_not_include":["already use ChatGPT","already use Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - no current AI tool. What would you want the first AI tool to help with?
- preserve: `["no current AI tool"]`
- avoid: `["already use ChatGPT","already use Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_orientation_or_explanation_046

- split: train
- source_type: live_sanitized
- semantic_group: orientation_or_explanation
- target_card_id: orientation_plan_categories
- sanitized_buyer_text: What are these plans?
- target_compact_json: `{"act":"orientation_or_explanation","action":"answer_plan_category","avoid":["guaranteed","unlimited"],"block":[],"buyer":"confused","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"information","neg":"none","obj":["plans"],"preserve":["plans"],"rel":"none","say":"plans are plan categories. I would explain them first, then ask which use case matters most.","strategy":"explain_without_overclaiming","sub":"plan_category_explanation","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["plans"],"must_not_include":["guaranteed","unlimited"],"next_action":"answer_plan_category","one_next_step":"answer_plan_category","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: plans are plan categories. I would explain them first, then ask which use case matters most.
- preserve: `["plans"]`
- avoid: `["guaranteed","unlimited"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_orientation_or_explanation_047

- split: train
- source_type: synthetic_control
- semantic_group: orientation_or_explanation
- target_card_id: orientation_model_vs_subscription
- sanitized_buyer_text: Is this a model or a subscription?
- target_compact_json: `{"act":"orientation_or_explanation","action":"answer_plan_category","avoid":["internal policy","guaranteed"],"block":[],"buyer":"confused","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"information","neg":"none","obj":["model","subscription"],"preserve":["model","subscription"],"rel":"or","say":"model or subscription are different questions: one is the AI model, the other is the subscription plan. Which part are you choosing?","strategy":"explain_without_overclaiming","sub":"model_vs_subscription_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["model","subscription"],"must_not_include":["internal policy","guaranteed"],"next_action":"answer_plan_category","one_next_step":"answer_plan_category","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: model or subscription are different questions: one is the AI model, the other is the subscription plan. Which part are you choosing?
- preserve: `["model","subscription"]`
- avoid: `["internal policy","guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_orientation_or_explanation_048

- split: train
- source_type: synthetic_control
- semantic_group: orientation_or_explanation
- target_card_id: orientation_source_disclosure
- sanitized_buyer_text: Who are you with?
- target_compact_json: `{"act":"source_question","action":"answer_source","avoid":["official OpenAI","we at OpenAI"],"block":[],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"information","neg":"none","obj":["who are you with"],"preserve":["who are you with"],"rel":"none","say":"For who are you with, I should stay clear: I can help compare plans, but I should not claim official affiliation.","strategy":"answer_without_inventing_facts","sub":"source_disclosure_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["who are you with"],"must_not_include":["official OpenAI","we at OpenAI"],"next_action":"answer_source","one_next_step":"answer_source","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For who are you with, I should stay clear: I can help compare plans, but I should not claim official affiliation.
- preserve: `["who are you with"]`
- avoid: `["official OpenAI","we at OpenAI"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_orientation_or_explanation_049

- split: train
- source_type: original_gold
- semantic_group: orientation_or_explanation
- target_card_id: orientation_affiliation_boundary
- sanitized_buyer_text: Are you from OpenAI?
- target_compact_json: `{"act":"affiliation_question","action":"answer_affiliation_boundary","avoid":["we at OpenAI","official OpenAI"],"block":[],"buyer":"skeptical","conf":0.9,"facts":[],"flags":[],"intent":"information","neg":"none","obj":["from OpenAI"],"preserve":["from OpenAI"],"rel":"none","say":"I should not claim from OpenAI. I can still help you compare plan fit from your use case.","strategy":"answer_without_inventing_facts","sub":"affiliation_boundary_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["from OpenAI"],"must_not_include":["we at OpenAI","official OpenAI"],"next_action":"answer_affiliation_boundary","one_next_step":"answer_affiliation_boundary","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: I should not claim from OpenAI. I can still help you compare plan fit from your use case.
- preserve: `["from OpenAI"]`
- avoid: `["we at OpenAI","official OpenAI"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_orientation_or_explanation_050

- split: train
- source_type: deterministic_paraphrase
- semantic_group: orientation_or_explanation
- target_card_id: orientation_plan_categories
- sanitized_buyer_text: Explain Free, Plus, Pro, Business, and Enterprise. Right now.
- target_compact_json: `{"act":"orientation_or_explanation","action":"answer_plan_category","avoid":["guaranteed","unlimited"],"block":[],"buyer":"confused","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"information","neg":"none","obj":["Free","Plus","Pro","Business","Enterprise"],"preserve":["Free","Plus","Pro","Business","Enterprise"],"rel":"and","say":"Free and Plus and Pro and Business and Enterprise are plan categories. I would explain them first, then ask which use case matters most.","strategy":"explain_without_overclaiming","sub":"plan_category_explanation","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Free","Plus","Pro","Business","Enterprise"],"must_not_include":["guaranteed","unlimited"],"next_action":"answer_plan_category","one_next_step":"answer_plan_category","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Free and Plus and Pro and Business and Enterprise are plan categories. I would explain them first, then ask which use case matters most.
- preserve: `["Free","Plus","Pro","Business","Enterprise"]`
- avoid: `["guaranteed","unlimited"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_individual_not_team_and_team_scope_091

- split: train
- source_type: original_gold
- semantic_group: individual_not_team_and_team_scope
- target_card_id: team_not_team_personal
- sanitized_buyer_text: I'm by myself, not a team.
- target_compact_json: `{"act":"team_scope","action":"ask_individual_usage_intensity","avoid":["team plan","business workspace","Enterprise route"],"block":["team_state"],"buyer":"individual_user","conf":0.9,"facts":[],"flags":[],"intent":"information","neg":"team_state","obj":["by myself","not a team"],"preserve":["by myself","not a team"],"rel":"and","say":"Understood - by myself and not a team. How heavily do you expect to use it?","strategy":"preserve_buyer_words","sub":"not_team_personal_use","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["by myself","not a team"],"must_not_include":["team plan","business workspace","Enterprise route"],"next_action":"ask_individual_usage_intensity","one_next_step":"ask_individual_usage_intensity","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Understood - by myself and not a team. How heavily do you expect to use it?
- preserve: `["by myself","not a team"]`
- avoid: `["team plan","business workspace","Enterprise route"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_individual_not_team_and_team_scope_092

- split: train
- source_type: synthetic_control
- semantic_group: individual_not_team_and_team_scope
- target_card_id: team_personal_use
- sanitized_buyer_text: This is personal use only.
- target_compact_json: `{"act":"team_scope","action":"ask_individual_usage_intensity","avoid":["team plan","procurement"],"block":["team_state"],"buyer":"individual_user","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"information","neg":"team_state","obj":["personal use only"],"preserve":["personal use only"],"rel":"none","say":"Got it - personal use only. How heavily do you expect to use it?","strategy":"diagnose_before_recommend","sub":"personal_use","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["personal use only"],"must_not_include":["team plan","procurement"],"next_action":"ask_individual_usage_intensity","one_next_step":"ask_individual_usage_intensity","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - personal use only. How heavily do you expect to use it?
- preserve: `["personal use only"]`
- avoid: `["team plan","procurement"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_individual_not_team_and_team_scope_093

- split: train
- source_type: synthetic_control
- semantic_group: individual_not_team_and_team_scope
- target_card_id: team_controls_positive
- sanitized_buyer_text: We need team admin and employees.
- target_compact_json: `{"act":"team_scope","action":"answer_team_controls","avoid":["individual only"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"high","neg":"none","obj":["team admin","employees"],"preserve":["team admin","employees"],"rel":"and","say":"team admin and employees points to a team controls path. Who owns admin or security review?","strategy":"explain_without_overclaiming","sub":"team_controls_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":true,"use":[]}}`
- expanded_action_summary: `{"must_include":["team admin","employees"],"must_not_include":["individual only"],"next_action":"answer_team_controls","one_next_step":"answer_team_controls","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: team admin and employees points to a team controls path. Who owns admin or security review?
- preserve: `["team admin","employees"]`
- avoid: `["individual only"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_individual_not_team_and_team_scope_094

- split: train
- source_type: synthetic_control
- semantic_group: individual_not_team_and_team_scope
- target_card_id: team_enterprise_security
- sanitized_buyer_text: This is Enterprise security procurement.
- target_compact_json: `{"act":"team_scope","action":"answer_team_controls","avoid":["personal use only"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"high","neg":"none","obj":["Enterprise","security","procurement"],"preserve":["Enterprise","security","procurement"],"rel":"and","say":"Enterprise and security and procurement sounds like an Enterprise security discussion. The next step is confirming the buyer and review owner.","strategy":"answer_without_inventing_facts","sub":"enterprise_security_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":true,"use":[]}}`
- expanded_action_summary: `{"must_include":["Enterprise","security","procurement"],"must_not_include":["personal use only"],"next_action":"answer_team_controls","one_next_step":"answer_team_controls","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Enterprise and security and procurement sounds like an Enterprise security discussion. The next step is confirming the buyer and review owner.
- preserve: `["Enterprise","security","procurement"]`
- avoid: `["personal use only"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_individual_not_team_and_team_scope_095

- split: train
- source_type: deterministic_paraphrase
- semantic_group: individual_not_team_and_team_scope
- target_card_id: team_not_team_personal
- sanitized_buyer_text: Just me, no company. Right now.
- target_compact_json: `{"act":"team_scope","action":"ask_individual_usage_intensity","avoid":["team plan","business workspace","Enterprise route"],"block":["team_state"],"buyer":"individual_user","conf":0.9,"facts":[],"flags":[],"intent":"information","neg":"team_state","obj":["just me","no company"],"preserve":["just me","no company"],"rel":"and","say":"Understood - just me and no company. How heavily do you expect to use it?","strategy":"preserve_buyer_words","sub":"not_team_personal_use","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["just me","no company"],"must_not_include":["team plan","business workspace","Enterprise route"],"next_action":"ask_individual_usage_intensity","one_next_step":"ask_individual_usage_intensity","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Understood - just me and no company. How heavily do you expect to use it?
- preserve: `["just me","no company"]`
- avoid: `["team plan","business workspace","Enterprise route"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_use_case_scope_136

- split: train
- source_type: live_sanitized
- semantic_group: use_case_scope
- target_card_id: use_case_coding_voice
- sanitized_buyer_text: coding workflow and probably voice
- target_compact_json: `{"act":"use_case_scope","action":"ask_usage_intensity","avoid":["writing"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["coding workflow","voice"],"preserve":["coding workflow","voice"],"rel":"and","say":"Got it - coding workflow and voice. Are you using that lightly, moderately, or heavily?","strategy":"diagnose_before_recommend","sub":"coding_voice_use_case","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":["coding workflow","voice"]}}`
- expanded_action_summary: `{"must_include":["coding workflow","voice"],"must_not_include":["writing"],"next_action":"ask_usage_intensity","one_next_step":"ask_usage_intensity","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - coding workflow and voice. Are you using that lightly, moderately, or heavily?
- preserve: `["coding workflow","voice"]`
- avoid: `["writing"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_use_case_scope_137

- split: train
- source_type: synthetic_control
- semantic_group: use_case_scope
- target_card_id: use_case_coding_writing
- sanitized_buyer_text: coding and writing
- target_compact_json: `{"act":"use_case_scope","action":"ask_usage_intensity","avoid":["voice"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["coding","writing"],"preserve":["coding","writing"],"rel":"and","say":"Got it - coding and writing. Are you using that lightly, moderately, or heavily?","strategy":"diagnose_before_recommend","sub":"coding_writing_use_case","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":["coding","writing"]}}`
- expanded_action_summary: `{"must_include":["coding","writing"],"must_not_include":["voice"],"next_action":"ask_usage_intensity","one_next_step":"ask_usage_intensity","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - coding and writing. Are you using that lightly, moderately, or heavily?
- preserve: `["coding","writing"]`
- avoid: `["voice"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_use_case_scope_138

- split: train
- source_type: live_sanitized
- semantic_group: use_case_scope
- target_card_id: use_case_coding_research
- sanitized_buyer_text: coding and research
- target_compact_json: `{"act":"use_case_scope","action":"ask_usage_intensity","avoid":["voice"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["coding","research"],"preserve":["coding","research"],"rel":"and","say":"Got it - coding and research. Are you using that lightly, moderately, or heavily?","strategy":"diagnose_before_recommend","sub":"coding_research_use_case","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":["coding","research"]}}`
- expanded_action_summary: `{"must_include":["coding","research"],"must_not_include":["voice"],"next_action":"ask_usage_intensity","one_next_step":"ask_usage_intensity","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - coding and research. Are you using that lightly, moderately, or heavily?
- preserve: `["coding","research"]`
- avoid: `["voice"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_use_case_scope_139

- split: train
- source_type: synthetic_control
- semantic_group: use_case_scope
- target_card_id: use_case_single_mode
- sanitized_buyer_text: voice only
- target_compact_json: `{"act":"use_case_scope","action":"ask_usage_intensity","avoid":[],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["voice"],"preserve":["voice"],"rel":"none","say":"Got it - voice. How often would you use it?","strategy":"diagnose_before_recommend","sub":"coding_voice_use_case","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":["voice"]}}`
- expanded_action_summary: `{"must_include":["voice"],"must_not_include":[],"next_action":"ask_usage_intensity","one_next_step":"ask_usage_intensity","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - voice. How often would you use it?
- preserve: `["voice"]`
- avoid: `[]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_use_case_scope_140

- split: train
- source_type: live_sanitized
- semantic_group: use_case_scope
- target_card_id: use_case_coding_voice
- sanitized_buyer_text: I need coding and voice help. Right now.
- target_compact_json: `{"act":"use_case_scope","action":"ask_usage_intensity","avoid":["writing"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["coding","voice"],"preserve":["coding","voice"],"rel":"and","say":"Got it - coding and voice. Are you using that lightly, moderately, or heavily?","strategy":"diagnose_before_recommend","sub":"coding_voice_use_case","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":["coding","voice"]}}`
- expanded_action_summary: `{"must_include":["coding","voice"],"must_not_include":["writing"],"next_action":"ask_usage_intensity","one_next_step":"ask_usage_intensity","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - coding and voice. Are you using that lightly, moderately, or heavily?
- preserve: `["coding","voice"]`
- avoid: `["writing"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_usage_intensity_181

- split: train
- source_type: synthetic_control
- semantic_group: usage_intensity
- target_card_id: usage_light_occasional
- sanitized_buyer_text: light use
- target_compact_json: `{"act":"usage_intensity","action":"ask_use_case_gap","avoid":["heavy daily"],"block":[],"buyer":"light_usage","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["light use"],"preserve":["light use"],"rel":"none","say":"Got it - light use. What would you mainly use it for?","strategy":"diagnose_before_recommend","sub":"light_occasional_use","update":{"adoption":"","close":"","intensity":"light_occasional_use","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["light use"],"must_not_include":["heavy daily"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - light use. What would you mainly use it for?
- preserve: `["light use"]`
- avoid: `["heavy daily"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_usage_intensity_182

- split: train
- source_type: synthetic_control
- semantic_group: usage_intensity
- target_card_id: usage_heavy_daily
- sanitized_buyer_text: heavy daily use
- target_compact_json: `{"act":"usage_intensity","action":"ask_use_case_gap","avoid":["light use"],"block":[],"buyer":"high_usage","conf":0.9,"facts":[],"flags":[],"intent":"high","neg":"none","obj":["heavy daily use"],"preserve":["heavy daily use"],"rel":"none","say":"Got it - heavy daily use. What tasks are creating that heavier demand?","strategy":"diagnose_before_recommend","sub":"heavy_daily_use","update":{"adoption":"","close":"","intensity":"heavy_daily_use","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["heavy daily use"],"must_not_include":["light use"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - heavy daily use. What tasks are creating that heavier demand?
- preserve: `["heavy daily use"]`
- avoid: `["light use"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_usage_intensity_183

- split: train
- source_type: synthetic_control
- semantic_group: usage_intensity
- target_card_id: usage_moderate
- sanitized_buyer_text: moderate use
- target_compact_json: `{"act":"usage_intensity","action":"ask_use_case_gap","avoid":["heavy daily"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["moderate use"],"preserve":["moderate use"],"rel":"none","say":"Got it - moderate use. What use case should the plan fit around?","strategy":"diagnose_before_recommend","sub":"occasional_use","update":{"adoption":"","close":"","intensity":"occasional_use","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["moderate use"],"must_not_include":["heavy daily"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - moderate use. What use case should the plan fit around?
- preserve: `["moderate use"]`
- avoid: `["heavy daily"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_usage_intensity_184

- split: train
- source_type: deterministic_paraphrase
- semantic_group: usage_intensity
- target_card_id: usage_light_occasional
- sanitized_buyer_text: only occasional use Right now.
- target_compact_json: `{"act":"usage_intensity","action":"ask_use_case_gap","avoid":["heavy daily"],"block":[],"buyer":"light_usage","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["occasional use"],"preserve":["occasional use"],"rel":"none","say":"Got it - occasional use. What would you mainly use it for?","strategy":"diagnose_before_recommend","sub":"occasional_use","update":{"adoption":"","close":"","intensity":"occasional_use","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["occasional use"],"must_not_include":["heavy daily"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - occasional use. What would you mainly use it for?
- preserve: `["occasional use"]`
- avoid: `["heavy daily"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_usage_intensity_185

- split: train
- source_type: deterministic_paraphrase
- semantic_group: usage_intensity
- target_card_id: usage_heavy_daily
- sanitized_buyer_text: I am hitting limits. Right now.
- target_compact_json: `{"act":"usage_intensity","action":"ask_use_case_gap","avoid":["light use"],"block":[],"buyer":"high_usage","conf":0.9,"facts":[],"flags":[],"intent":"high","neg":"none","obj":["hitting limits"],"preserve":["hitting limits"],"rel":"none","say":"Got it - hitting limits. What tasks are creating that heavier demand?","strategy":"diagnose_before_recommend","sub":"heavy_daily_use","update":{"adoption":"","close":"","intensity":"heavy_daily_use","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["hitting limits"],"must_not_include":["light use"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - hitting limits. What tasks are creating that heavier demand?
- preserve: `["hitting limits"]`
- avoid: `["light use"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_211

- split: train
- source_type: synthetic_control
- semantic_group: price_and_value
- target_card_id: price_plus_direct
- sanitized_buyer_text: How much is Plus?
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["recommend Pro"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Plus price"],"preserve":["Plus price"],"rel":"none","say":"For Plus price, answer the price directly first; plan fit comes after usage context.","strategy":"answer_without_inventing_facts","sub":"plus_price_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus price"],"must_not_include":["recommend Pro"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Plus price, answer the price directly first; plan fit comes after usage context.
- preserve: `["Plus price"]`
- avoid: `["recommend Pro"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_price_and_value_212

- split: train
- source_type: synthetic_control
- semantic_group: price_and_value
- target_card_id: price_pro_direct
- sanitized_buyer_text: How much is Pro?
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Pro price"],"preserve":["Pro price"],"rel":"none","say":"For Pro price, answer the price directly first; then compare whether Pro is actually needed.","strategy":"answer_without_inventing_facts","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Pro price"],"must_not_include":["guaranteed"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Pro price, answer the price directly first; then compare whether Pro is actually needed.
- preserve: `["Pro price"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_price_and_value_213

- split: train
- source_type: synthetic_control
- semantic_group: price_and_value
- target_card_id: price_objection_value
- sanitized_buyer_text: That is too expensive.
- target_compact_json: `{"act":"price_objection","action":"reframe_price_objection","avoid":["cheap","guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["too expensive"],"preserve":["too expensive"],"rel":"none","say":"Fair - too expensive. The plan only makes sense if the use case saves enough time or quality pain.","strategy":"value_reframe","sub":"price_objection","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["too expensive"],"must_not_include":["cheap","guaranteed"],"next_action":"reframe_price_objection","one_next_step":"reframe_price_objection","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Fair - too expensive. The plan only makes sense if the use case saves enough time or quality pain.
- preserve: `["too expensive"]`
- avoid: `["cheap","guaranteed"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_price_and_value_214

- split: train
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_plus_direct
- sanitized_buyer_text: What is the Plus price? Right now.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["recommend Pro"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Plus price"],"preserve":["Plus price"],"rel":"none","say":"For Plus price, answer the price directly first; plan fit comes after usage context.","strategy":"answer_without_inventing_facts","sub":"plus_price_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus price"],"must_not_include":["recommend Pro"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Plus price, answer the price directly first; plan fit comes after usage context.
- preserve: `["Plus price"]`
- avoid: `["recommend Pro"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_215

- split: train
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_pro_direct
- sanitized_buyer_text: What does Pro cost? Right now.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Pro cost"],"preserve":["Pro cost"],"rel":"none","say":"For Pro cost, answer the price directly first; then compare whether Pro is actually needed.","strategy":"answer_without_inventing_facts","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Pro cost"],"must_not_include":["guaranteed"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Pro cost, answer the price directly first; then compare whether Pro is actually needed.
- preserve: `["Pro cost"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_256

- split: train
- source_type: synthetic_control
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_plus_enough
- sanitized_buyer_text: Is Plus enough?
- target_compact_json: `{"act":"plan_fit_question","action":"answer_plan_fit","avoid":["definitely Pro","guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"medium","neg":"none","obj":["Plus enough"],"preserve":["Plus enough"],"rel":"none","say":"Plus enough depends on use case and intensity. What would you use it for most?","strategy":"value_before_plan_selection","sub":"plus_sufficiency_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus enough"],"must_not_include":["definitely Pro","guaranteed"],"next_action":"answer_plan_fit","one_next_step":"answer_plan_fit","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Plus enough depends on use case and intensity. What would you use it for most?
- preserve: `["Plus enough"]`
- avoid: `["definitely Pro","guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_plan_fit_and_recommendation_257

- split: train
- source_type: synthetic_control
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_pro_choice
- sanitized_buyer_text: Is Pro better?
- target_compact_json: `{"act":"pro_tier_question","action":"answer_plan_fit","avoid":["guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"medium","neg":"none","obj":["Pro better"],"preserve":["Pro better"],"rel":"none","say":"Pro better is worth checking only if usage or limits justify it. How heavy is your usage?","strategy":"value_before_plan_selection","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Pro better"],"must_not_include":["guaranteed"],"next_action":"answer_plan_fit","one_next_step":"answer_plan_fit","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Pro better is worth checking only if usage or limits justify it. How heavy is your usage?
- preserve: `["Pro better"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_plan_fit_and_recommendation_258

- split: train
- source_type: synthetic_control
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_recommend_after_context
- sanitized_buyer_text: I code daily and hit limits, so recommend one.
- target_compact_json: `{"act":"plan_fit_question","action":"recommend_plan","avoid":["team plan","guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"high","neg":"none","obj":["code daily","hit limits"],"preserve":["code daily","hit limits"],"rel":"and","say":"Given code daily and hit limits, I would recommend Pro as the first plan to evaluate.","strategy":"choice_close","sub":"plus_sufficiency_question","update":{"adoption":"","close":"","intensity":"heavy_daily_use","recommend":"Pro","team":false,"use":["code daily","hit limits"]}}`
- expanded_action_summary: `{"must_include":["code daily","hit limits"],"must_not_include":["team plan","guaranteed"],"next_action":"recommend_plan","one_next_step":"recommend_plan","should_ask_question":false,"should_close":true,"should_disqualify":false,"should_recommend":false}`
- say: Given code daily and hit limits, I would recommend Pro as the first plan to evaluate.
- preserve: `["code daily","hit limits"]`
- avoid: `["team plan","guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_plan_fit_and_recommendation_259

- split: train
- source_type: synthetic_control
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_no_fit_free_enough
- sanitized_buyer_text: Free is enough for now.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["push Pro","team plan"],"block":["paid_recommendation"],"buyer":"not_interested","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"low","neg":"none","obj":["Free enough"],"preserve":["Free enough"],"rel":"none","say":"If Free enough, I would not push a paid plan now.","strategy":"no_fit_close","sub":"no_interest","update":{"adoption":"","close":"not_ready","intensity":"","recommend":"Free","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Free enough"],"must_not_include":["push Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: If Free enough, I would not push a paid plan now.
- preserve: `["Free enough"]`
- avoid: `["push Pro","team plan"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_plan_fit_and_recommendation_270

- split: train
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_recommend_after_context
- sanitized_buyer_text: I code daily and hit limits, so recommend one. Before I choose anything.
- target_compact_json: `{"act":"plan_fit_question","action":"recommend_plan","avoid":["team plan","guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"high","neg":"none","obj":["code daily","hit limits"],"preserve":["code daily","hit limits"],"rel":"and","say":"Given code daily and hit limits, I would recommend Pro as the first plan to evaluate.","strategy":"choice_close","sub":"plus_sufficiency_question","update":{"adoption":"","close":"","intensity":"heavy_daily_use","recommend":"Pro","team":false,"use":["code daily","hit limits"]}}`
- expanded_action_summary: `{"must_include":["code daily","hit limits"],"must_not_include":["team plan","guaranteed"],"next_action":"recommend_plan","one_next_step":"recommend_plan","should_ask_question":false,"should_close":true,"should_disqualify":false,"should_recommend":false}`
- say: Given code daily and hit limits, I would recommend Pro as the first plan to evaluate.
- preserve: `["code daily","hit limits"]`
- avoid: `["team plan","guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_change_and_signup_301

- split: train
- source_type: synthetic_control
- semantic_group: plan_change_and_signup
- target_card_id: plan_change_upgrade_later
- sanitized_buyer_text: Can I start lower and upgrade later?
- target_compact_json: `{"act":"plan_change_question","action":"answer_plan_change","avoid":["calendar","email","CRM"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"high","neg":"none","obj":["start lower","upgrade later"],"preserve":["start lower","upgrade later"],"rel":"and","say":"start lower and upgrade later is a plan-change question. Answer it directly, then keep the choice reversible.","strategy":"choice_close","sub":"midcycle_upgrade_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["start lower","upgrade later"],"must_not_include":["calendar","email","CRM"],"next_action":"answer_plan_change","one_next_step":"answer_plan_change","should_ask_question":false,"should_close":true,"should_disqualify":false,"should_recommend":false}`
- say: start lower and upgrade later is a plan-change question. Answer it directly, then keep the choice reversible.
- preserve: `["start lower","upgrade later"]`
- avoid: `["calendar","email","CRM"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_plan_change_and_signup_302

- split: train
- source_type: live_sanitized
- semantic_group: plan_change_and_signup
- target_card_id: plan_change_signup_path
- sanitized_buyer_text: Where do I sign up?
- target_compact_json: `{"act":"signup_question","action":"answer_signup_path","avoid":["sent email","created calendar","CRM"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"high","neg":"none","obj":["sign up"],"preserve":["sign up"],"rel":"none","say":"For sign up, keep it self-serve and do not claim any signup action was taken.","strategy":"choice_close","sub":"signup_path_question","update":{"adoption":"","close":"signup_path","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["sign up"],"must_not_include":["sent email","created calendar","CRM"],"next_action":"answer_signup_path","one_next_step":"answer_signup_path","should_ask_question":false,"should_close":true,"should_disqualify":false,"should_recommend":false}`
- say: For sign up, keep it self-serve and do not claim any signup action was taken.
- preserve: `["sign up"]`
- avoid: `["sent email","created calendar","CRM"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_plan_change_and_signup_303

- split: train
- source_type: original_gold
- semantic_group: plan_change_and_signup
- target_card_id: plan_change_terminal_close
- sanitized_buyer_text: Ok, I'll check that, thanks.
- target_compact_json: `{"act":"terminal_acceptance","action":"terminal_close","avoid":["email","calendar","CRM","?"],"block":["new_question"],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["thanks"],"preserve":[],"rel":"none","say":"Sounds good - you can check that and stop here.","strategy":"terminal_close","sub":"terminal_thanks_acceptance","update":{"adoption":"","close":"accepted","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["thanks"],"must_not_include":["email","calendar","CRM","?"],"next_action":"terminal_close","one_next_step":"terminal_close","should_ask_question":false,"should_close":true,"should_disqualify":false,"should_recommend":false}`
- say: Sounds good - you can check that and stop here.
- preserve: `[]`
- avoid: `["email","calendar","CRM","?"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_plan_change_and_signup_312

- split: train
- source_type: deterministic_paraphrase
- semantic_group: plan_change_and_signup
- target_card_id: plan_change_terminal_close
- sanitized_buyer_text: Ok, I'll check that, thanks. Before I choose anything.
- target_compact_json: `{"act":"terminal_acceptance","action":"terminal_close","avoid":["email","calendar","CRM","?"],"block":["new_question"],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["thanks"],"preserve":[],"rel":"none","say":"Sounds good - you can check that and stop here.","strategy":"terminal_close","sub":"terminal_thanks_acceptance","update":{"adoption":"","close":"accepted","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["thanks"],"must_not_include":["email","calendar","CRM","?"],"next_action":"terminal_close","one_next_step":"terminal_close","should_ask_question":false,"should_close":true,"should_disqualify":false,"should_recommend":false}`
- say: Sounds good - you can check that and stop here.
- preserve: `[]`
- avoid: `["email","calendar","CRM","?"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_change_and_signup_315

- split: train
- source_type: deterministic_paraphrase
- semantic_group: plan_change_and_signup
- target_card_id: plan_change_terminal_close
- sanitized_buyer_text: Thanks, that is all. In this call.
- target_compact_json: `{"act":"terminal_acceptance","action":"terminal_close","avoid":["email","calendar","CRM","?"],"block":["new_question"],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["thanks"],"preserve":[],"rel":"none","say":"Sounds good - you can check that and stop here.","strategy":"terminal_close","sub":"terminal_thanks_acceptance","update":{"adoption":"","close":"accepted","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["thanks"],"must_not_include":["email","calendar","CRM","?"],"next_action":"terminal_close","one_next_step":"terminal_close","should_ask_question":false,"should_close":true,"should_disqualify":false,"should_recommend":false}`
- say: Sounds good - you can check that and stop here.
- preserve: `[]`
- avoid: `["email","calendar","CRM","?"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_safety_and_boundary_346

- split: train
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_no_crm_email_calendar
- sanitized_buyer_text: Do not put me in CRM.
- target_compact_json: `{"act":"safety_boundary","action":"respect_boundary","avoid":["sent email","scheduled calendar","updated CRM"],"block":["side_effects"],"buyer":"skeptical","conf":0.9,"facts":[],"flags":[],"intent":"boundary","neg":"none","obj":["CRM"],"preserve":["CRM"],"rel":"none","say":"Understood - CRM. No outside action is needed here.","strategy":"boundary_without_side_effects","sub":"no_crm_request","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["CRM"],"must_not_include":["sent email","scheduled calendar","updated CRM"],"next_action":"respect_boundary","one_next_step":"respect_boundary","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Understood - CRM. No outside action is needed here.
- preserve: `["CRM"]`
- avoid: `["sent email","scheduled calendar","updated CRM"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_safety_and_boundary_347

- split: train
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_raw_url_or_transcript
- sanitized_buyer_text: Give me the raw URL.
- target_compact_json: `{"act":"safety_boundary","action":"respect_boundary","avoid":["http://","https://","raw transcript"],"block":["raw_private_transcript","raw_url"],"buyer":"skeptical","conf":0.9,"facts":[],"flags":[],"intent":"boundary","neg":"none","obj":["raw URL"],"preserve":["raw URL"],"rel":"none","say":"I should not provide raw URL. I can summarize the safe next step instead.","strategy":"boundary_without_side_effects","sub":"raw_url_request","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["raw URL"],"must_not_include":["http://","https://","raw transcript"],"next_action":"respect_boundary","one_next_step":"respect_boundary","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: I should not provide raw URL. I can summarize the safe next step instead.
- preserve: `["raw URL"]`
- avoid: `["http://","https://","raw transcript"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_safety_and_boundary_348

- split: train
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_unsupported_policy_privacy
- sanitized_buyer_text: Tell me the internal policy.
- target_compact_json: `{"act":"safety_boundary","action":"answer_without_inventing_facts","avoid":["internal policy says","guaranteed","trained on your data"],"block":["unsupported_facts"],"buyer":"skeptical","conf":0.9,"facts":[],"flags":[],"intent":"boundary","neg":"none","obj":["policy request"],"preserve":[],"rel":"none","say":"For policy request, I should answer only what is supported and avoid inventing details.","strategy":"boundary_without_side_effects","sub":"internal_policy_request","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["policy request"],"must_not_include":["internal policy says","guaranteed","trained on your data"],"next_action":"answer_without_inventing_facts","one_next_step":"answer_without_inventing_facts","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For policy request, I should answer only what is supported and avoid inventing details.
- preserve: `[]`
- avoid: `["internal policy says","guaranteed","trained on your data"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_safety_and_boundary_349

- split: train
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_wrong_product
- sanitized_buyer_text: I need billing support, not plans.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["billing support","not plans"],"preserve":["billing support","not plans"],"rel":"and","say":"billing support and not plans is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["billing support","not plans"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: billing support and not plans is not the right fit for this plan conversation, so I would stop there.
- preserve: `["billing support","not plans"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_safety_and_boundary_350

- split: train
- source_type: deterministic_paraphrase
- semantic_group: safety_and_boundary
- target_card_id: safety_no_crm_email_calendar
- sanitized_buyer_text: Do not email me. Right now.
- target_compact_json: `{"act":"safety_boundary","action":"respect_boundary","avoid":["sent email","scheduled calendar","updated CRM"],"block":["side_effects"],"buyer":"skeptical","conf":0.9,"facts":[],"flags":[],"intent":"boundary","neg":"none","obj":["email"],"preserve":["email"],"rel":"none","say":"Understood - email. No outside action is needed here.","strategy":"boundary_without_side_effects","sub":"side_effect_boundary_request","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["email"],"must_not_include":["sent email","scheduled calendar","updated CRM"],"next_action":"respect_boundary","one_next_step":"respect_boundary","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Understood - email. No outside action is needed here.
- preserve: `["email"]`
- avoid: `["sent email","scheduled calendar","updated CRM"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_objections_and_competitor_context_391

- split: train
- source_type: synthetic_control
- semantic_group: objections_and_competitor_context
- target_card_id: objection_competitor_current_tool
- sanitized_buyer_text: I use Claude, why switch?
- target_compact_json: `{"act":"competitor_objection","action":"compare_competitor_context","avoid":["switch now","guaranteed better"],"block":["recommendation"],"buyer":"skeptical","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"medium","neg":"none","obj":["Claude","why switch"],"preserve":["Claude","why switch"],"rel":"and","say":"If Claude and why switch, the comparison should start with what your current tool fails to cover.","strategy":"compare_options","sub":"current_competitor_tool","update":{"adoption":"current_competitor_tool","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Claude","why switch"],"must_not_include":["switch now","guaranteed better"],"next_action":"compare_competitor_context","one_next_step":"compare_competitor_context","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: If Claude and why switch, the comparison should start with what your current tool fails to cover.
- preserve: `["Claude","why switch"]`
- avoid: `["switch now","guaranteed better"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_objections_and_competitor_context_392

- split: train
- source_type: synthetic_control
- semantic_group: objections_and_competitor_context
- target_card_id: objection_chatgpt_vs_current_tool
- sanitized_buyer_text: ChatGPT vs Claude, why switch?
- target_compact_json: `{"act":"competitor_objection","action":"compare_competitor_context","avoid":["guaranteed better"],"block":["recommendation"],"buyer":"skeptical","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","Claude"],"preserve":["ChatGPT","Claude"],"rel":"or","say":"ChatGPT or Claude should be compared by use case first, not by a premature plan recommendation.","strategy":"value_before_plan_selection","sub":"current_competitor_tool","update":{"adoption":"current_competitor_tool","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","Claude"],"must_not_include":["guaranteed better"],"next_action":"compare_competitor_context","one_next_step":"compare_competitor_context","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: ChatGPT or Claude should be compared by use case first, not by a premature plan recommendation.
- preserve: `["ChatGPT","Claude"]`
- avoid: `["guaranteed better"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_objections_and_competitor_context_394

- split: train
- source_type: synthetic_control
- semantic_group: objections_and_competitor_context
- target_card_id: objection_price_with_current_tool
- sanitized_buyer_text: Claude is enough and price matters.
- target_compact_json: `{"act":"price_objection","action":"reframe_price_objection","avoid":["cheap","guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["Claude is enough","price matters"],"preserve":["Claude is enough","price matters"],"rel":"and","say":"Fair - Claude is enough and price matters. I would only compare paid value if the current tool has a real gap.","strategy":"value_reframe","sub":"current_competitor_tool","update":{"adoption":"current_competitor_tool","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Claude is enough","price matters"],"must_not_include":["cheap","guaranteed"],"next_action":"reframe_price_objection","one_next_step":"reframe_price_objection","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Fair - Claude is enough and price matters. I would only compare paid value if the current tool has a real gap.
- preserve: `["Claude is enough","price matters"]`
- avoid: `["cheap","guaranteed"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_objections_and_competitor_context_402

- split: train
- source_type: deterministic_paraphrase
- semantic_group: objections_and_competitor_context
- target_card_id: objection_price_with_current_tool
- sanitized_buyer_text: Gemini works and I do not want another bill. For this plan decision.
- target_compact_json: `{"act":"price_objection","action":"reframe_price_objection","avoid":["cheap","guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["Gemini works","another bill"],"preserve":["Gemini works","another bill"],"rel":"and","say":"Fair - Gemini works and another bill. I would only compare paid value if the current tool has a real gap.","strategy":"value_reframe","sub":"current_competitor_tool","update":{"adoption":"current_competitor_tool","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Gemini works","another bill"],"must_not_include":["cheap","guaranteed"],"next_action":"reframe_price_objection","one_next_step":"reframe_price_objection","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Fair - Gemini works and another bill. I would only compare paid value if the current tool has a real gap.
- preserve: `["Gemini works","another bill"]`
- avoid: `["cheap","guaranteed"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_objections_and_competitor_context_405

- split: train
- source_type: deterministic_paraphrase
- semantic_group: objections_and_competitor_context
- target_card_id: objection_not_interested
- sanitized_buyer_text: Not interested. Before I choose anything.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["push Pro","calendar","email"],"block":["recommendation"],"buyer":"not_interested","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["not interested"],"preserve":["not interested"],"rel":"none","say":"Understood - not interested. I would not push the plan further.","strategy":"no_fit_close","sub":"no_interest","update":{"adoption":"","close":"not_interested","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["not interested"],"must_not_include":["push Pro","calendar","email"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: Understood - not interested. I would not push the plan further.
- preserve: `["not interested"]`
- avoid: `["push Pro","calendar","email"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_006

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_chatgpt_user
- sanitized_buyer_text: Mostly ChatGPT at the moment. Right now.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT"],"preserve":["ChatGPT"],"rel":"none","say":"Got it - you already use ChatGPT. Where does that setup still fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_user","update":{"adoption":"current_chatgpt_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use ChatGPT. Where does that setup still fall short?
- preserve: `["ChatGPT"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_007

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_other_ai_user
- sanitized_buyer_text: Right now I use Gemini. Right now.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["Gemini"],"preserve":["Gemini"],"rel":"none","say":"Got it - you already use Gemini. What gap are you trying to solve beyond that?","strategy":"diagnose_before_recommend","sub":"current_other_ai_user","update":{"adoption":"current_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Gemini"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use Gemini. What gap are you trying to solve beyond that?
- preserve: `["Gemini"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_008

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_and_other_ai
- sanitized_buyer_text: I use ChatGPT and Claude together. Right now.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT or"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","Claude"],"preserve":["ChatGPT","Claude"],"rel":"and","say":"Got it - you use ChatGPT and Claude. Where does the current setup fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_and_other_ai_user","update":{"adoption":"current_chatgpt_and_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","Claude"],"must_not_include":["ChatGPT or"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you use ChatGPT and Claude. Where does the current setup fall short?
- preserve: `["ChatGPT","Claude"]`
- avoid: `["ChatGPT or"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_009

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_or_other_uncertain
- sanitized_buyer_text: It might be ChatGPT or cloud. Right now.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT and Claude"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","cloud"],"preserve":["ChatGPT","cloud"],"rel":"or","say":"Got it - ChatGPT or cloud. What do you use it for most?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"current_chatgpt_or_other_ai_unknown","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","cloud"],"must_not_include":["ChatGPT and Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - ChatGPT or cloud. What do you use it for most?
- preserve: `["ChatGPT","cloud"]`
- avoid: `["ChatGPT and Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_010

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_no_current_ai_tool
- sanitized_buyer_text: No current AI tool for me. Right now.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["already use ChatGPT","already use Claude"],"block":["adoption_state"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"information","neg":"none","obj":["no current AI tool"],"preserve":["no current AI tool"],"rel":"none","say":"Got it - no current AI tool. What would you want the first AI tool to help with?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["no current AI tool"],"must_not_include":["already use ChatGPT","already use Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - no current AI tool. What would you want the first AI tool to help with?
- preserve: `["no current AI tool"]`
- avoid: `["already use ChatGPT","already use Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_011

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_chatgpt_user
- sanitized_buyer_text: I am already using check GPT. For this plan decision.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["check GPT"],"preserve":["check GPT"],"rel":"none","say":"Got it - you already use check GPT. Where does that setup still fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_user","update":{"adoption":"current_chatgpt_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["check GPT"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use check GPT. Where does that setup still fall short?
- preserve: `["check GPT"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_012

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_other_ai_user
- sanitized_buyer_text: I use Copilot for most things. For this plan decision.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["Copilot"],"preserve":["Copilot"],"rel":"none","say":"Got it - you already use Copilot. What gap are you trying to solve beyond that?","strategy":"diagnose_before_recommend","sub":"current_other_ai_user","update":{"adoption":"current_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Copilot"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use Copilot. What gap are you trying to solve beyond that?
- preserve: `["Copilot"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_013

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_and_other_ai
- sanitized_buyer_text: I have ChatGPT and Gemini open most days. For this plan decision.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT or"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","Gemini"],"preserve":["ChatGPT","Gemini"],"rel":"and","say":"Got it - you use ChatGPT and Gemini. Where does the current setup fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_and_other_ai_user","update":{"adoption":"current_chatgpt_and_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","Gemini"],"must_not_include":["ChatGPT or"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you use ChatGPT and Gemini. Where does the current setup fall short?
- preserve: `["ChatGPT","Gemini"]`
- avoid: `["ChatGPT or"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_014

- split: train
- source_type: live_sanitized
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_or_other_uncertain
- sanitized_buyer_text: I am not sure if it is chacha PT or Claude. For this plan decision.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT and Claude"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["chacha PT","Claude"],"preserve":["chacha PT","Claude"],"rel":"or","say":"Got it - chacha PT or Claude. What do you use it for most?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"current_chatgpt_or_other_ai_unknown","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["chacha PT","Claude"],"must_not_include":["ChatGPT and Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - chacha PT or Claude. What do you use it for most?
- preserve: `["chacha PT","Claude"]`
- avoid: `["ChatGPT and Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_016

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_chatgpt_user
- sanitized_buyer_text: I use ChatGPT now. Before I choose anything.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT"],"preserve":["ChatGPT"],"rel":"none","say":"Got it - you already use ChatGPT. Where does that setup still fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_user","update":{"adoption":"current_chatgpt_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use ChatGPT. Where does that setup still fall short?
- preserve: `["ChatGPT"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_017

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_other_ai_user
- sanitized_buyer_text: I think it is cloud or Claude. Before I choose anything.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["cloud","Claude"],"preserve":["cloud","Claude"],"rel":"none","say":"Got it - you already use cloud and Claude. What gap are you trying to solve beyond that?","strategy":"diagnose_before_recommend","sub":"current_other_ai_user","update":{"adoption":"current_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["cloud","Claude"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use cloud and Claude. What gap are you trying to solve beyond that?
- preserve: `["cloud","Claude"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_018

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_and_other_ai
- sanitized_buyer_text: I use ChatGPT and other AI tools. Before I choose anything.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT or"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","other AI tools"],"preserve":["ChatGPT","other AI tools"],"rel":"and","say":"Got it - you use ChatGPT and other AI tools. Where does the current setup fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_and_other_ai_user","update":{"adoption":"current_chatgpt_and_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","other AI tools"],"must_not_include":["ChatGPT or"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you use ChatGPT and other AI tools. Where does the current setup fall short?
- preserve: `["ChatGPT","other AI tools"]`
- avoid: `["ChatGPT or"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_019

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_or_other_uncertain
- sanitized_buyer_text: I use ChatGPT or maybe Claude. Before I choose anything.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT and Claude"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","Claude"],"preserve":["ChatGPT","Claude"],"rel":"or","say":"Got it - ChatGPT or Claude. What do you use it for most?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"current_chatgpt_or_other_ai_unknown","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","Claude"],"must_not_include":["ChatGPT and Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - ChatGPT or Claude. What do you use it for most?
- preserve: `["ChatGPT","Claude"]`
- avoid: `["ChatGPT and Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_020

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_no_current_ai_tool
- sanitized_buyer_text: I do not use any AI tool right now. Before I choose anything.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["already use ChatGPT","already use Claude"],"block":["adoption_state"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"information","neg":"none","obj":["no current AI tool"],"preserve":["no current AI tool"],"rel":"none","say":"Got it - no current AI tool. What would you want the first AI tool to help with?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["no current AI tool"],"must_not_include":["already use ChatGPT","already use Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - no current AI tool. What would you want the first AI tool to help with?
- preserve: `["no current AI tool"]`
- avoid: `["already use ChatGPT","already use Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_031

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_chatgpt_user
- sanitized_buyer_text: I use ChatGPT now. For my setup.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT"],"preserve":["ChatGPT"],"rel":"none","say":"Got it - you already use ChatGPT. Where does that setup still fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_user","update":{"adoption":"current_chatgpt_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use ChatGPT. Where does that setup still fall short?
- preserve: `["ChatGPT"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_032

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_other_ai_user
- sanitized_buyer_text: Right now I use Gemini. For my setup.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["Gemini"],"preserve":["Gemini"],"rel":"none","say":"Got it - you already use Gemini. What gap are you trying to solve beyond that?","strategy":"diagnose_before_recommend","sub":"current_other_ai_user","update":{"adoption":"current_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Gemini"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use Gemini. What gap are you trying to solve beyond that?
- preserve: `["Gemini"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_033

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_and_other_ai
- sanitized_buyer_text: I use ChatGPT and other AI tools. For my setup.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT or"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","other AI tools"],"preserve":["ChatGPT","other AI tools"],"rel":"and","say":"Got it - you use ChatGPT and other AI tools. Where does the current setup fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_and_other_ai_user","update":{"adoption":"current_chatgpt_and_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","other AI tools"],"must_not_include":["ChatGPT or"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you use ChatGPT and other AI tools. Where does the current setup fall short?
- preserve: `["ChatGPT","other AI tools"]`
- avoid: `["ChatGPT or"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_034

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_or_other_uncertain
- sanitized_buyer_text: I use ChatGPT or maybe Claude. For my setup.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT and Claude"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","Claude"],"preserve":["ChatGPT","Claude"],"rel":"or","say":"Got it - ChatGPT or Claude. What do you use it for most?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"current_chatgpt_or_other_ai_unknown","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","Claude"],"must_not_include":["ChatGPT and Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - ChatGPT or Claude. What do you use it for most?
- preserve: `["ChatGPT","Claude"]`
- avoid: `["ChatGPT and Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_035

- split: train
- source_type: deterministic_paraphrase
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_no_current_ai_tool
- sanitized_buyer_text: I do not use any AI tool right now. For my setup.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["already use ChatGPT","already use Claude"],"block":["adoption_state"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"information","neg":"none","obj":["no current AI tool"],"preserve":["no current AI tool"],"rel":"none","say":"Got it - no current AI tool. What would you want the first AI tool to help with?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["no current AI tool"],"must_not_include":["already use ChatGPT","already use Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - no current AI tool. What would you want the first AI tool to help with?
- preserve: `["no current AI tool"]`
- avoid: `["already use ChatGPT","already use Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_026

- split: train
- source_type: synthetic_control
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_chatgpt_user
- sanitized_buyer_text: I am already using check GPT. That is my current context.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["check GPT"],"preserve":["check GPT"],"rel":"none","say":"Got it - you already use check GPT. Where does that setup still fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_user","update":{"adoption":"current_chatgpt_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["check GPT"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use check GPT. Where does that setup still fall short?
- preserve: `["check GPT"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_027

- split: train
- source_type: synthetic_control
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_current_other_ai_user
- sanitized_buyer_text: I use Claude. That is my current context.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["recommend Pro"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["Claude"],"preserve":["Claude"],"rel":"none","say":"Got it - you already use Claude. What gap are you trying to solve beyond that?","strategy":"diagnose_before_recommend","sub":"current_other_ai_user","update":{"adoption":"current_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Claude"],"must_not_include":["recommend Pro"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you already use Claude. What gap are you trying to solve beyond that?
- preserve: `["Claude"]`
- avoid: `["recommend Pro"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_028

- split: train
- source_type: synthetic_control
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_and_other_ai
- sanitized_buyer_text: I have ChatGPT and Gemini open most days. That is my current context.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT or"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["ChatGPT","Gemini"],"preserve":["ChatGPT","Gemini"],"rel":"and","say":"Got it - you use ChatGPT and Gemini. Where does the current setup fall short?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_and_other_ai_user","update":{"adoption":"current_chatgpt_and_other_ai_user","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["ChatGPT","Gemini"],"must_not_include":["ChatGPT or"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - you use ChatGPT and Gemini. Where does the current setup fall short?
- preserve: `["ChatGPT","Gemini"]`
- avoid: `["ChatGPT or"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_029

- split: train
- source_type: synthetic_control
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_chatgpt_or_other_uncertain
- sanitized_buyer_text: I am not sure if it is chacha PT or Claude. That is my current context.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["ChatGPT and Claude"],"block":[],"buyer":"evaluating","conf":0.9,"facts":[],"flags":[],"intent":"medium","neg":"none","obj":["chacha PT","Claude"],"preserve":["chacha PT","Claude"],"rel":"or","say":"Got it - chacha PT or Claude. What do you use it for most?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"current_chatgpt_or_other_ai_unknown","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["chacha PT","Claude"],"must_not_include":["ChatGPT and Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - chacha PT or Claude. What do you use it for most?
- preserve: `["chacha PT","Claude"]`
- avoid: `["ChatGPT and Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_adoption_current_tool_context_030

- split: train
- source_type: synthetic_control
- semantic_group: adoption_current_tool_context
- target_card_id: adoption_no_current_ai_tool
- sanitized_buyer_text: I have not tried ChatGPT or another AI tool yet. That is my current context.
- target_compact_json: `{"act":"current_tool_context","action":"ask_use_case_gap","avoid":["already use ChatGPT","already use Claude"],"block":["adoption_state"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"information","neg":"none","obj":["no current AI tool"],"preserve":["no current AI tool"],"rel":"none","say":"Got it - no current AI tool. What would you want the first AI tool to help with?","strategy":"diagnose_before_recommend","sub":"current_chatgpt_or_other_ai_unknown","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["no current AI tool"],"must_not_include":["already use ChatGPT","already use Claude"],"next_action":"ask_use_case_gap","one_next_step":"ask_use_case_gap","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":true}`
- say: Got it - no current AI tool. What would you want the first AI tool to help with?
- preserve: `["no current AI tool"]`
- avoid: `["already use ChatGPT","already use Claude"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_safety_and_boundary_354

- split: train
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_no_crm_email_calendar
- sanitized_buyer_text: Do not schedule calendar. For this plan decision.
- target_compact_json: `{"act":"safety_boundary","action":"respect_boundary","avoid":["sent email","scheduled calendar","updated CRM"],"block":["side_effects"],"buyer":"skeptical","conf":0.9,"facts":[],"flags":[],"intent":"boundary","neg":"none","obj":["calendar"],"preserve":["calendar"],"rel":"none","say":"Understood - calendar. No outside action is needed here.","strategy":"boundary_without_side_effects","sub":"no_calendar_request","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["calendar"],"must_not_include":["sent email","scheduled calendar","updated CRM"],"next_action":"respect_boundary","one_next_step":"respect_boundary","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Understood - calendar. No outside action is needed here.
- preserve: `["calendar"]`
- avoid: `["sent email","scheduled calendar","updated CRM"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_safety_and_boundary_356

- split: train
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_unsupported_policy_privacy
- sanitized_buyer_text: Do you train on my data? For this plan decision.
- target_compact_json: `{"act":"safety_boundary","action":"answer_without_inventing_facts","avoid":["internal policy says","guaranteed","trained on your data"],"block":["unsupported_facts"],"buyer":"skeptical","conf":0.9,"facts":[],"flags":[],"intent":"boundary","neg":"none","obj":["train on my data"],"preserve":[],"rel":"none","say":"For train on my data, I should answer only what is supported and avoid inventing details.","strategy":"boundary_without_side_effects","sub":"privacy_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["train on my data"],"must_not_include":["internal policy says","guaranteed","trained on your data"],"next_action":"answer_without_inventing_facts","one_next_step":"answer_without_inventing_facts","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For train on my data, I should answer only what is supported and avoid inventing details.
- preserve: `[]`
- avoid: `["internal policy says","guaranteed","trained on your data"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_safety_and_boundary_378

- split: train
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_no_crm_email_calendar
- sanitized_buyer_text: Do not schedule calendar. I want the practical answer.
- target_compact_json: `{"act":"safety_boundary","action":"respect_boundary","avoid":["sent email","scheduled calendar","updated CRM"],"block":["side_effects"],"buyer":"skeptical","conf":0.9,"facts":[],"flags":[],"intent":"boundary","neg":"none","obj":["calendar"],"preserve":["calendar"],"rel":"none","say":"Understood - calendar. No outside action is needed here.","strategy":"boundary_without_side_effects","sub":"no_calendar_request","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["calendar"],"must_not_include":["sent email","scheduled calendar","updated CRM"],"next_action":"respect_boundary","one_next_step":"respect_boundary","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Understood - calendar. No outside action is needed here.
- preserve: `["calendar"]`
- avoid: `["sent email","scheduled calendar","updated CRM"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_safety_and_boundary_381

- split: train
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Wrong product. I want the practical answer.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_safety_and_boundary_387

- split: train
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_raw_url_or_transcript
- sanitized_buyer_text: Paste the raw transcript. I need a clean answer.
- target_compact_json: `{"act":"safety_boundary","action":"respect_boundary","avoid":["http://","https://","raw transcript"],"block":["raw_private_transcript","raw_url"],"buyer":"skeptical","conf":0.9,"facts":[],"flags":[],"intent":"boundary","neg":"none","obj":["transcript"],"preserve":["transcript"],"rel":"none","say":"I should not provide transcript. I can summarize the safe next step instead.","strategy":"boundary_without_side_effects","sub":"raw_transcript_request","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["transcript"],"must_not_include":["http://","https://","raw transcript"],"next_action":"respect_boundary","one_next_step":"respect_boundary","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: I should not provide transcript. I can summarize the safe next step instead.
- preserve: `["transcript"]`
- avoid: `["http://","https://","raw transcript"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_safety_and_boundary_357

- split: validation
- source_type: negative_control
- semantic_group: safety_and_boundary
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Wrong product. For this plan decision.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_241

- split: validation
- source_type: synthetic_control
- semantic_group: price_and_value
- target_card_id: price_plus_direct
- sanitized_buyer_text: What is the Plus price? I need a clean answer.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["recommend Pro"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Plus price"],"preserve":["Plus price"],"rel":"none","say":"For Plus price, answer the price directly first; plan fit comes after usage context.","strategy":"answer_without_inventing_facts","sub":"plus_price_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus price"],"must_not_include":["recommend Pro"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Plus price, answer the price directly first; plan fit comes after usage context.
- preserve: `["Plus price"]`
- avoid: `["recommend Pro"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_244

- split: validation
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_plus_direct
- sanitized_buyer_text: Just tell me Plus cost. Keep it to one next step.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["recommend Pro"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Plus cost"],"preserve":["Plus cost"],"rel":"none","say":"For Plus cost, answer the price directly first; plan fit comes after usage context.","strategy":"answer_without_inventing_facts","sub":"plus_price_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus cost"],"must_not_include":["recommend Pro"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Plus cost, answer the price directly first; plan fit comes after usage context.
- preserve: `["Plus cost"]`
- avoid: `["recommend Pro"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_247

- split: validation
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_plus_direct
- sanitized_buyer_text: How much is Plus? Variant 2.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["recommend Pro"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Plus price"],"preserve":["Plus price"],"rel":"none","say":"For Plus price, answer the price directly first; plan fit comes after usage context.","strategy":"answer_without_inventing_facts","sub":"plus_price_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus price"],"must_not_include":["recommend Pro"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Plus price, answer the price directly first; plan fit comes after usage context.
- preserve: `["Plus price"]`
- avoid: `["recommend Pro"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_250

- split: validation
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_plus_direct
- sanitized_buyer_text: What is the Plus price? Right now. Variant 2.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["recommend Pro"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Plus price"],"preserve":["Plus price"],"rel":"none","say":"For Plus price, answer the price directly first; plan fit comes after usage context.","strategy":"answer_without_inventing_facts","sub":"plus_price_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus price"],"must_not_include":["recommend Pro"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Plus price, answer the price directly first; plan fit comes after usage context.
- preserve: `["Plus price"]`
- avoid: `["recommend Pro"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_253

- split: validation
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_plus_direct
- sanitized_buyer_text: Just tell me Plus cost. For this plan decision. Variant 2.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["recommend Pro"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Plus cost"],"preserve":["Plus cost"],"rel":"none","say":"For Plus cost, answer the price directly first; plan fit comes after usage context.","strategy":"answer_without_inventing_facts","sub":"plus_price_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus cost"],"must_not_include":["recommend Pro"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Plus cost, answer the price directly first; plan fit comes after usage context.
- preserve: `["Plus cost"]`
- avoid: `["recommend Pro"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_260

- split: validation
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_plus_enough
- sanitized_buyer_text: Would Plus be enough for me? Right now.
- target_compact_json: `{"act":"plan_fit_question","action":"answer_plan_fit","avoid":["definitely Pro","guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"medium","neg":"none","obj":["Plus enough"],"preserve":["Plus enough"],"rel":"none","say":"Plus enough depends on use case and intensity. What would you use it for most?","strategy":"value_before_plan_selection","sub":"plus_sufficiency_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus enough"],"must_not_include":["definitely Pro","guaranteed"],"next_action":"answer_plan_fit","one_next_step":"answer_plan_fit","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Plus enough depends on use case and intensity. What would you use it for most?
- preserve: `["Plus enough"]`
- avoid: `["definitely Pro","guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_262

- split: validation
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_recommend_after_context
- sanitized_buyer_text: For heavy coding and research, which plan? Right now.
- target_compact_json: `{"act":"plan_fit_question","action":"recommend_plan","avoid":["team plan","guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"high","neg":"none","obj":["heavy coding","research"],"preserve":["heavy coding","research"],"rel":"and","say":"Given heavy coding and research, I would recommend Pro as the first plan to evaluate.","strategy":"choice_close","sub":"plus_sufficiency_question","update":{"adoption":"","close":"","intensity":"heavy_daily_use","recommend":"Pro","team":false,"use":["heavy coding","research"]}}`
- expanded_action_summary: `{"must_include":["heavy coding","research"],"must_not_include":["team plan","guaranteed"],"next_action":"recommend_plan","one_next_step":"recommend_plan","should_ask_question":false,"should_close":true,"should_disqualify":false,"should_recommend":false}`
- say: Given heavy coding and research, I would recommend Pro as the first plan to evaluate.
- preserve: `["heavy coding","research"]`
- avoid: `["team plan","guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_264

- split: validation
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_plus_enough
- sanitized_buyer_text: Can I stay on Plus? For this plan decision.
- target_compact_json: `{"act":"plan_fit_question","action":"answer_plan_fit","avoid":["definitely Pro","guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"medium","neg":"none","obj":["Plus"],"preserve":["Plus"],"rel":"none","say":"Plus depends on use case and intensity. What would you use it for most?","strategy":"value_before_plan_selection","sub":"plus_sufficiency_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus"],"must_not_include":["definitely Pro","guaranteed"],"next_action":"answer_plan_fit","one_next_step":"answer_plan_fit","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Plus depends on use case and intensity. What would you use it for most?
- preserve: `["Plus"]`
- avoid: `["definitely Pro","guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_266

- split: validation
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_recommend_after_context
- sanitized_buyer_text: I use it every day for coding and voice; pick a plan. For this plan decision.
- target_compact_json: `{"act":"plan_fit_question","action":"recommend_plan","avoid":["team plan","guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"high","neg":"none","obj":["every day","coding","voice"],"preserve":["every day","coding","voice"],"rel":"and","say":"Given every day and coding and voice, I would recommend Pro as the first plan to evaluate.","strategy":"choice_close","sub":"plus_sufficiency_question","update":{"adoption":"","close":"","intensity":"heavy_daily_use","recommend":"Pro","team":false,"use":["every day","coding","voice"]}}`
- expanded_action_summary: `{"must_include":["every day","coding","voice"],"must_not_include":["team plan","guaranteed"],"next_action":"recommend_plan","one_next_step":"recommend_plan","should_ask_question":false,"should_close":true,"should_disqualify":false,"should_recommend":false}`
- say: Given every day and coding and voice, I would recommend Pro as the first plan to evaluate.
- preserve: `["every day","coding","voice"]`
- avoid: `["team plan","guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_268

- split: validation
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_plus_enough
- sanitized_buyer_text: Is Plus enough? Before I choose anything.
- target_compact_json: `{"act":"plan_fit_question","action":"answer_plan_fit","avoid":["definitely Pro","guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"medium","neg":"none","obj":["Plus enough"],"preserve":["Plus enough"],"rel":"none","say":"Plus enough depends on use case and intensity. What would you use it for most?","strategy":"value_before_plan_selection","sub":"plus_sufficiency_question","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus enough"],"must_not_include":["definitely Pro","guaranteed"],"next_action":"answer_plan_fit","one_next_step":"answer_plan_fit","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Plus enough depends on use case and intensity. What would you use it for most?
- preserve: `["Plus enough"]`
- avoid: `["definitely Pro","guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_239

- split: test
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_pro_direct
- sanitized_buyer_text: How much is Pro? I am deciding today.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Pro price"],"preserve":["Pro price"],"rel":"none","say":"For Pro price, answer the price directly first; then compare whether Pro is actually needed.","strategy":"answer_without_inventing_facts","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Pro price"],"must_not_include":["guaranteed"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Pro price, answer the price directly first; then compare whether Pro is actually needed.
- preserve: `["Pro price"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_242

- split: test
- source_type: synthetic_control
- semantic_group: price_and_value
- target_card_id: price_pro_direct
- sanitized_buyer_text: What does Pro cost? I need a clean answer.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Pro cost"],"preserve":["Pro cost"],"rel":"none","say":"For Pro cost, answer the price directly first; then compare whether Pro is actually needed.","strategy":"answer_without_inventing_facts","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Pro cost"],"must_not_include":["guaranteed"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Pro cost, answer the price directly first; then compare whether Pro is actually needed.
- preserve: `["Pro cost"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_245

- split: test
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_pro_direct
- sanitized_buyer_text: Tell me the Pro price without selling me. Keep it to one next step.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Pro price"],"preserve":["Pro price"],"rel":"none","say":"For Pro price, answer the price directly first; then compare whether Pro is actually needed.","strategy":"answer_without_inventing_facts","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Pro price"],"must_not_include":["guaranteed"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Pro price, answer the price directly first; then compare whether Pro is actually needed.
- preserve: `["Pro price"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_248

- split: test
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_pro_direct
- sanitized_buyer_text: How much is Pro? Variant 2.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Pro price"],"preserve":["Pro price"],"rel":"none","say":"For Pro price, answer the price directly first; then compare whether Pro is actually needed.","strategy":"answer_without_inventing_facts","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Pro price"],"must_not_include":["guaranteed"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Pro price, answer the price directly first; then compare whether Pro is actually needed.
- preserve: `["Pro price"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_251

- split: test
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_pro_direct
- sanitized_buyer_text: What does Pro cost? Right now. Variant 2.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Pro cost"],"preserve":["Pro cost"],"rel":"none","say":"For Pro cost, answer the price directly first; then compare whether Pro is actually needed.","strategy":"answer_without_inventing_facts","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Pro cost"],"must_not_include":["guaranteed"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Pro cost, answer the price directly first; then compare whether Pro is actually needed.
- preserve: `["Pro cost"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_price_and_value_254

- split: test
- source_type: deterministic_paraphrase
- semantic_group: price_and_value
- target_card_id: price_pro_direct
- sanitized_buyer_text: Tell me the Pro price without selling me. For this plan decision. Variant 2.
- target_compact_json: `{"act":"price_question","action":"answer_price","avoid":["guaranteed"],"block":["recommendation"],"buyer":"price_sensitive","conf":0.9,"facts":["public_plan_names","current_public_plan_prices"],"flags":[],"intent":"information","neg":"none","obj":["Pro price"],"preserve":["Pro price"],"rel":"none","say":"For Pro price, answer the price directly first; then compare whether Pro is actually needed.","strategy":"answer_without_inventing_facts","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Pro price"],"must_not_include":["guaranteed"],"next_action":"answer_price","one_next_step":"answer_price","should_ask_question":false,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: For Pro price, answer the price directly first; then compare whether Pro is actually needed.
- preserve: `["Pro price"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names","current_public_plan_prices"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_261

- split: test
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_pro_choice
- sanitized_buyer_text: Should I choose Pro? Right now.
- target_compact_json: `{"act":"pro_tier_question","action":"answer_plan_fit","avoid":["guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"medium","neg":"none","obj":["choose Pro"],"preserve":["choose Pro"],"rel":"none","say":"choose Pro is worth checking only if usage or limits justify it. How heavy is your usage?","strategy":"value_before_plan_selection","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["choose Pro"],"must_not_include":["guaranteed"],"next_action":"answer_plan_fit","one_next_step":"answer_plan_fit","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: choose Pro is worth checking only if usage or limits justify it. How heavy is your usage?
- preserve: `["choose Pro"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_263

- split: test
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_no_fit_free_enough
- sanitized_buyer_text: No paid plan fits me. Right now.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["push Pro","team plan"],"block":["paid_recommendation"],"buyer":"not_interested","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"low","neg":"none","obj":["no paid plan"],"preserve":["no paid plan"],"rel":"none","say":"If no paid plan, I would not push a paid plan now.","strategy":"no_fit_close","sub":"no_interest","update":{"adoption":"","close":"not_ready","intensity":"","recommend":"Free","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["no paid plan"],"must_not_include":["push Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: If no paid plan, I would not push a paid plan now.
- preserve: `["no paid plan"]`
- avoid: `["push Pro","team plan"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_265

- split: test
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_pro_choice
- sanitized_buyer_text: Plus vs Pro, what fits? For this plan decision.
- target_compact_json: `{"act":"pro_tier_question","action":"answer_plan_fit","avoid":["guaranteed"],"block":[],"buyer":"evaluating","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"medium","neg":"none","obj":["Plus","Pro"],"preserve":["Plus","Pro"],"rel":"or","say":"Plus or Pro is worth checking only if usage or limits justify it. How heavy is your usage?","strategy":"value_before_plan_selection","sub":"pro_tier_choice","update":{"adoption":"","close":"","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["Plus","Pro"],"must_not_include":["guaranteed"],"next_action":"answer_plan_fit","one_next_step":"answer_plan_fit","should_ask_question":true,"should_close":false,"should_disqualify":false,"should_recommend":false}`
- say: Plus or Pro is worth checking only if usage or limits justify it. How heavy is your usage?
- preserve: `["Plus","Pro"]`
- avoid: `["guaranteed"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_plan_fit_and_recommendation_267

- split: test
- source_type: deterministic_paraphrase
- semantic_group: plan_fit_and_recommendation
- target_card_id: plan_fit_no_fit_free_enough
- sanitized_buyer_text: Current tool is enough. For this plan decision.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["push Pro","team plan"],"block":["paid_recommendation"],"buyer":"not_interested","conf":0.9,"facts":["public_plan_names"],"flags":[],"intent":"low","neg":"none","obj":["current tool is enough"],"preserve":["current tool is enough"],"rel":"none","say":"If current tool is enough, I would not push a paid plan now.","strategy":"no_fit_close","sub":"no_interest","update":{"adoption":"","close":"not_ready","intensity":"","recommend":"Free","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["current tool is enough"],"must_not_include":["push Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: If current tool is enough, I would not push a paid plan now.
- preserve: `["current tool is enough"]`
- avoid: `["push Pro","team plan"]`
- facts: `["public_plan_names"]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: warning

### balanced_ood_control_001

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Can you choose my health insurance plan?
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_ood_control_002

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: I need legal advice on a contract.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_ood_control_003

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Write a password reset email to my customer.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_ood_control_004

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Book a meeting with procurement for tomorrow.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_ood_control_005

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Upload my call audio to a public site.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_ood_control_006

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Give me the private support transcript.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_ood_control_007

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Pretend you are official support and close it.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_ood_control_008

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: I need tax filing advice, not AI plans.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_ood_control_009

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Can you buy the subscription for me?
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

### balanced_ood_control_010

- split: ood_test
- source_type: ood_control
- semantic_group: ood_control
- target_card_id: safety_wrong_product
- sanitized_buyer_text: Send the invoice to my CRM.
- target_compact_json: `{"act":"no_fit","action":"disqualify_no_fit","avoid":["recommend Pro","team plan"],"block":["recommendation"],"buyer":"confused","conf":0.9,"facts":[],"flags":[],"intent":"low","neg":"none","obj":["wrong product"],"preserve":["wrong product"],"rel":"none","say":"wrong product is not the right fit for this plan conversation, so I would stop there.","strategy":"no_fit_close","sub":"wrong_product_question","update":{"adoption":"","close":"wrong_product","intensity":"","recommend":"","team":false,"use":[]}}`
- expanded_action_summary: `{"must_include":["wrong product"],"must_not_include":["recommend Pro","team plan"],"next_action":"disqualify_no_fit","one_next_step":"disqualify_no_fit","should_ask_question":false,"should_close":false,"should_disqualify":true,"should_recommend":false}`
- say: wrong product is not the right fit for this plan conversation, so I would stop there.
- preserve: `["wrong product"]`
- avoid: `["recommend Pro","team plan"]`
- facts: `[]`
- verifier_result: `{"errors":[],"status":"pass"}`
- review_classification: acceptable

## Target Card Examples

[{"avoid_policy":{"phrases":["recommend Pro"]},"canonical_act":"current_tool_context","canonical_action":"ask_use_case_gap","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"I use ChatGPT now.","objects":["ChatGPT"]},{"buyer_text":"Mostly ChatGPT at the moment.","objects":["ChatGPT"]},{"buyer_text":"I am already using check GPT.","objects":["check GPT"],"sub":"current_chatgpt_user"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve the current ChatGPT mention."},"semantic_group":"adoption_current_tool_context","target_card_id":"adoption_current_chatgpt_user"},{"avoid_policy":{"phrases":["recommend Pro"]},"canonical_act":"current_tool_context","canonical_action":"ask_use_case_gap","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"I use Claude.","objects":["Claude"]},{"buyer_text":"Right now I use Gemini.","objects":["Gemini"]},{"buyer_text":"I use Copilot for most things.","objects":["Copilot"]}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve the current non-ChatGPT AI tool mention."},"semantic_group":"adoption_current_tool_context","target_card_id":"adoption_current_other_ai_user"},{"avoid_policy":{"phrases":["ChatGPT or"]},"canonical_act":"current_tool_context","canonical_action":"ask_use_case_gap","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"I use ChatGPT and other AI tools.","objects":["ChatGPT","other AI tools"],"rel":"and"},{"buyer_text":"I use ChatGPT and Claude together.","objects":["ChatGPT","Claude"],"rel":"and"},{"buyer_text":"I have ChatGPT and Gemini open most days.","objects":["ChatGPT","Gemini"],"rel":"and"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve ChatGPT and the other AI tool; do not turn AND into OR."},"semantic_group":"adoption_current_tool_context","target_card_id":"adoption_chatgpt_and_other_ai"},{"avoid_policy":{"phrases":["ChatGPT and Claude"]},"canonical_act":"current_tool_context","canonical_action":"ask_use_case_gap","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"I use ChatGPT or maybe Claude.","objects":["ChatGPT","Claude"],"rel":"or"},{"buyer_text":"It might be ChatGPT or cloud.","objects":["ChatGPT","cloud"],"rel":"or"},{"buyer_text":"I am not sure if it is chacha PT or Claude.","objects":["chacha PT","Claude"],"rel":"or"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve uncertainty and OR relation."},"semantic_group":"adoption_current_tool_context","target_card_id":"adoption_chatgpt_or_other_uncertain"},{"avoid_policy":{"phrases":["already use ChatGPT","already use Claude"]},"canonical_act":"current_tool_context","canonical_action":"ask_use_case_gap","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"I do not use any AI tool right now.","objects":["no current AI tool"]},{"buyer_text":"No current AI tool for me.","objects":["no current AI tool"]},{"buyer_text":"I have not tried ChatGPT or another AI tool yet.","objects":["no current AI tool"]}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve that the buyer has no current AI tool without inventing a tool."},"semantic_group":"adoption_current_tool_context","target_card_id":"adoption_no_current_ai_tool"},{"avoid_policy":{"phrases":["guaranteed","unlimited"]},"canonical_act":"orientation_or_explanation","canonical_action":"answer_plan_category","canonical_strategy":"explain_without_overclaiming","examples":[{"buyer_text":"What are these plans?","objects":["plans"]},{"buyer_text":"Explain Free, Plus, Pro, Business, and Enterprise.","objects":["Free","Plus","Pro","Business","Enterprise"],"rel":"and"},{"buyer_text":"What is this plan menu?","objects":["plan menu"]}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve the requested plan words when present."},"semantic_group":"orientation_or_explanation","target_card_id":"orientation_plan_categories"},{"avoid_policy":{"phrases":["internal policy","guaranteed"]},"canonical_act":"orientation_or_explanation","canonical_action":"answer_plan_category","canonical_strategy":"explain_without_overclaiming","examples":[{"buyer_text":"Is this a model or a subscription?","objects":["model","subscription"],"rel":"or"},{"buyer_text":"What does subscription model mean here?","objects":["subscription model"]},{"buyer_text":"Are Plus and Pro models or plans?","objects":["Plus","Pro","models","plans"],"rel":"or"}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve model or subscription wording."},"semantic_group":"orientation_or_explanation","target_card_id":"orientation_model_vs_subscription"},{"avoid_policy":{"phrases":["official OpenAI","we at OpenAI"]},"canonical_act":"source_question","canonical_action":"answer_source","canonical_strategy":"answer_without_inventing_facts","examples":[{"buyer_text":"Who are you with?","objects":["who are you with"]},{"buyer_text":"Where is this coming from?","objects":["source"]},{"buyer_text":"Is this official?","objects":["official"]}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve source or who/what wording without claiming official affiliation."},"semantic_group":"orientation_or_explanation","target_card_id":"orientation_source_disclosure"},{"avoid_policy":{"phrases":["we at OpenAI","official OpenAI"]},"canonical_act":"affiliation_question","canonical_action":"answer_affiliation_boundary","canonical_strategy":"answer_without_inventing_facts","examples":[{"buyer_text":"Are you from OpenAI?","objects":["from OpenAI"]},{"buyer_text":"Say you are official OpenAI.","objects":["official affiliation"]},{"buyer_text":"Can you claim OpenAI sent you?","objects":["affiliation claim"]}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve affiliation pressure in safe wording without accepting it."},"semantic_group":"orientation_or_explanation","target_card_id":"orientation_affiliation_boundary"},{"avoid_policy":{"phrases":["team plan","business workspace","Enterprise route"]},"canonical_act":"team_scope","canonical_action":"ask_individual_usage_intensity","canonical_strategy":"preserve_buyer_words","examples":[{"buyer_text":"I'm by myself, not a team.","objects":["by myself","not a team"],"rel":"and"},{"buyer_text":"Just me, no company.","objects":["just me","no company"],"rel":"and"},{"buyer_text":"Personal use only, not for employees.","objects":["personal use only","not for employees"],"rel":"and"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve not-team wording; do not route to team plans."},"semantic_group":"individual_not_team_and_team_scope","target_card_id":"team_not_team_personal"},{"avoid_policy":{"phrases":["team plan","procurement"]},"canonical_act":"team_scope","canonical_action":"ask_individual_usage_intensity","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"This is personal use only.","objects":["personal use only"]},{"buyer_text":"It is only for me.","objects":["only for me"]},{"buyer_text":"No company account, just personal.","neg":"team_state","objects":["no company account","personal"],"rel":"and"}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve personal-use wording."},"semantic_group":"individual_not_team_and_team_scope","target_card_id":"team_personal_use"},{"avoid_policy":{"phrases":["individual only"]},"canonical_act":"team_scope","canonical_action":"answer_team_controls","canonical_strategy":"explain_without_overclaiming","examples":[{"buyer_text":"We need team admin and employees.","objects":["team admin","employees"],"rel":"and"},{"buyer_text":"Our company cares about SSO and procurement.","objects":["company","SSO","procurement"],"rel":"and"},{"buyer_text":"Security controls for employees matter.","objects":["security controls","employees"],"rel":"and"}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve team/company/admin/security terms."},"semantic_group":"individual_not_team_and_team_scope","target_card_id":"team_controls_positive"},{"avoid_policy":{"phrases":["personal use only"]},"canonical_act":"team_scope","canonical_action":"answer_team_controls","canonical_strategy":"answer_without_inventing_facts","examples":[{"buyer_text":"This is Enterprise security procurement.","objects":["Enterprise","security","procurement"],"rel":"and"},{"buyer_text":"We need Enterprise for SSO and legal review.","objects":["Enterprise","SSO","legal review"],"rel":"and"}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve Enterprise/security/procurement intent."},"semantic_group":"individual_not_team_and_team_scope","target_card_id":"team_enterprise_security"},{"avoid_policy":{"phrases":["writing"]},"canonical_act":"use_case_scope","canonical_action":"ask_usage_intensity","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"coding workflow and probably voice","objects":["coding workflow","voice"],"rel":"and"},{"buyer_text":"I need coding and voice help.","objects":["coding","voice"],"rel":"and"},{"buyer_text":"Voice for coding would matter.","objects":["voice","coding"],"rel":"and"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve coding and voice; do not rewrite voice as writing."},"semantic_group":"use_case_scope","target_card_id":"use_case_coding_voice"},{"avoid_policy":{"phrases":["voice"]},"canonical_act":"use_case_scope","canonical_action":"ask_usage_intensity","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"coding and writing","objects":["coding","writing"],"rel":"and"},{"buyer_text":"I need writing and coding help.","objects":["writing","coding"],"rel":"and"},{"buyer_text":"Mostly code reviews and writing emails.","objects":["code reviews","writing emails"],"rel":"and"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve coding and writing."},"semantic_group":"use_case_scope","target_card_id":"use_case_coding_writing"},{"avoid_policy":{"phrases":["voice"]},"canonical_act":"use_case_scope","canonical_action":"ask_usage_intensity","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"coding and research","objects":["coding","research"],"rel":"and"},{"buyer_text":"I need research plus coding.","objects":["research","coding"],"rel":"and"},{"buyer_text":"Coding or research, I am not sure which.","objects":["coding","research"],"rel":"or"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve coding and research."},"semantic_group":"use_case_scope","target_card_id":"use_case_coding_research"},{"avoid_policy":{"phrases":[]},"canonical_act":"use_case_scope","canonical_action":"ask_usage_intensity","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"voice only","objects":["voice"],"sub":"coding_voice_use_case"},{"buyer_text":"writing only","objects":["writing"],"sub":"coding_writing_use_case"},{"buyer_text":"research only","objects":["research"],"sub":"coding_research_use_case"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve voice-only, writing-only, or research-only wording."},"semantic_group":"use_case_scope","target_card_id":"use_case_single_mode"},{"avoid_policy":{"phrases":["heavy daily"]},"canonical_act":"usage_intensity","canonical_action":"ask_use_case_gap","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"light use","objects":["light use"],"sub":"light_occasional_use"},{"buyer_text":"only occasional use","objects":["occasional use"],"sub":"occasional_use"},{"buyer_text":"I am not hitting limits.","objects":["not hitting limits"],"sub":"light_occasional_use"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve light or occasional wording."},"semantic_group":"usage_intensity","target_card_id":"usage_light_occasional"},{"avoid_policy":{"phrases":["light use"]},"canonical_act":"usage_intensity","canonical_action":"ask_use_case_gap","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"heavy daily use","objects":["heavy daily use"]},{"buyer_text":"I am hitting limits.","objects":["hitting limits"]},{"buyer_text":"a little heavy maybe more than a little","objects":["a little heavy maybe more than a little"]}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve heavy, daily, or limits wording."},"semantic_group":"usage_intensity","target_card_id":"usage_heavy_daily"},{"avoid_policy":{"phrases":["heavy daily"]},"canonical_act":"usage_intensity","canonical_action":"ask_use_case_gap","canonical_strategy":"diagnose_before_recommend","examples":[{"buyer_text":"moderate use","objects":["moderate use"]},{"buyer_text":"not light, not heavy, moderate.","objects":["moderate"]},{"buyer_text":"I use it sometimes but not every day.","objects":["sometimes","not every day"],"rel":"and"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve moderate wording without pretending it is heavy."},"semantic_group":"usage_intensity","target_card_id":"usage_moderate"},{"avoid_policy":{"phrases":["recommend Pro"]},"canonical_act":"price_question","canonical_action":"answer_price","canonical_strategy":"answer_without_inventing_facts","examples":[{"buyer_text":"How much is Plus?","objects":["Plus price"]},{"buyer_text":"What is the Plus price?","objects":["Plus price"]},{"buyer_text":"Just tell me Plus cost.","objects":["Plus cost"]}],"facts_policy":{"fact_ids":["public_plan_names","current_public_plan_prices"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve Plus price wording and answer price before fit."},"semantic_group":"price_and_value","target_card_id":"price_plus_direct"},{"avoid_policy":{"phrases":["guaranteed"]},"canonical_act":"price_question","canonical_action":"answer_price","canonical_strategy":"answer_without_inventing_facts","examples":[{"buyer_text":"How much is Pro?","objects":["Pro price"]},{"buyer_text":"What does Pro cost?","objects":["Pro cost"]},{"buyer_text":"Tell me the Pro price without selling me.","objects":["Pro price"]}],"facts_policy":{"fact_ids":["public_plan_names","current_public_plan_prices"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve Pro price wording and answer price before fit."},"semantic_group":"price_and_value","target_card_id":"price_pro_direct"},{"avoid_policy":{"phrases":["cheap","guaranteed"]},"canonical_act":"price_objection","canonical_action":"reframe_price_objection","canonical_strategy":"value_reframe","examples":[{"buyer_text":"That is too expensive.","objects":["too expensive"]},{"buyer_text":"Why should I pay?","objects":["why should I pay"]},{"buyer_text":"I am budget sensitive.","objects":["budget sensitive"]}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve the objection wording."},"semantic_group":"price_and_value","target_card_id":"price_objection_value"},{"avoid_policy":{"phrases":["definitely Pro","guaranteed"]},"canonical_act":"plan_fit_question","canonical_action":"answer_plan_fit","canonical_strategy":"value_before_plan_selection","examples":[{"buyer_text":"Is Plus enough?","objects":["Plus enough"]},{"buyer_text":"Would Plus be enough for me?","objects":["Plus enough"]},{"buyer_text":"Can I stay on Plus?","objects":["Plus"]}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve Plus enough wording."},"semantic_group":"plan_fit_and_recommendation","target_card_id":"plan_fit_plus_enough"},{"avoid_policy":{"phrases":["guaranteed"]},"canonical_act":"pro_tier_question","canonical_action":"answer_plan_fit","canonical_strategy":"value_before_plan_selection","examples":[{"buyer_text":"Is Pro better?","objects":["Pro better"]},{"buyer_text":"Should I choose Pro?","objects":["choose Pro"]},{"buyer_text":"Plus vs Pro, what fits?","objects":["Plus","Pro"],"rel":"or"}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve Pro choice wording."},"semantic_group":"plan_fit_and_recommendation","target_card_id":"plan_fit_pro_choice"},{"avoid_policy":{"phrases":["team plan","guaranteed"]},"canonical_act":"plan_fit_question","canonical_action":"recommend_plan","canonical_strategy":"choice_close","examples":[{"buyer_text":"I code daily and hit limits, so recommend one.","objects":["code daily","hit limits"],"rel":"and"},{"buyer_text":"For heavy coding and research, which plan?","objects":["heavy coding","research"],"rel":"and"},{"buyer_text":"I use it every day for coding and voice; pick a plan.","objects":["every day","coding","voice"],"rel":"and"}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Recommend only after enough use-case and intensity context is present."},"semantic_group":"plan_fit_and_recommendation","target_card_id":"plan_fit_recommend_after_context"},{"avoid_policy":{"phrases":["push Pro","team plan"]},"canonical_act":"no_fit","canonical_action":"disqualify_no_fit","canonical_strategy":"no_fit_close","examples":[{"buyer_text":"Free is enough for now.","objects":["Free enough"]},{"buyer_text":"No paid plan fits me.","objects":["no paid plan"]},{"buyer_text":"Current tool is enough.","objects":["current tool is enough"]}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve Free enough or no-fit wording."},"semantic_group":"plan_fit_and_recommendation","target_card_id":"plan_fit_no_fit_free_enough"},{"avoid_policy":{"phrases":["calendar","email","CRM"]},"canonical_act":"plan_change_question","canonical_action":"answer_plan_change","canonical_strategy":"choice_close","examples":[{"buyer_text":"Can I start lower and upgrade later?","objects":["start lower","upgrade later"],"rel":"and"},{"buyer_text":"Can I upgrade midcycle?","objects":["upgrade midcycle"]},{"buyer_text":"If I choose Plus now, can I move up later?","objects":["Plus now","move up later"],"rel":"and"}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve start lower, upgrade later, or midcycle wording."},"semantic_group":"plan_change_and_signup","target_card_id":"plan_change_upgrade_later"},{"avoid_policy":{"phrases":["sent email","created calendar","CRM"]},"canonical_act":"signup_question","canonical_action":"answer_signup_path","canonical_strategy":"choice_close","examples":[{"buyer_text":"Where do I sign up?","objects":["sign up"]},{"buyer_text":"Show me the self-serve signup path.","objects":["self-serve signup path"]},{"buyer_text":"Can I close this myself online?","objects":["close this myself online"]}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve signup or self-serve path wording."},"semantic_group":"plan_change_and_signup","target_card_id":"plan_change_signup_path"},{"avoid_policy":{"phrases":["email","calendar","CRM","?"]},"canonical_act":"terminal_acceptance","canonical_action":"terminal_close","canonical_strategy":"terminal_close","examples":[{"buyer_text":"Ok, I'll check that, thanks.","objects":["thanks"]},{"buyer_text":"Thanks, that is all.","objects":["thanks"]},{"buyer_text":"Sounds fine, I will look later.","objects":["look later"]}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"none","required_meaning":"No new question; short terminal close."},"semantic_group":"plan_change_and_signup","target_card_id":"plan_change_terminal_close"},{"avoid_policy":{"phrases":["sent email","scheduled calendar","updated CRM"]},"canonical_act":"safety_boundary","canonical_action":"respect_boundary","canonical_strategy":"boundary_without_side_effects","examples":[{"buyer_text":"Do not put me in CRM.","objects":["CRM"],"sub":"no_crm_request"},{"buyer_text":"Do not email me.","objects":["email"],"sub":"side_effect_boundary_request"},{"buyer_text":"Do not schedule calendar.","objects":["calendar"],"sub":"no_calendar_request"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve CRM/email/calendar boundary without claiming action."},"semantic_group":"safety_and_boundary","target_card_id":"safety_no_crm_email_calendar"},{"avoid_policy":{"phrases":["http://","https://","raw transcript"]},"canonical_act":"safety_boundary","canonical_action":"respect_boundary","canonical_strategy":"boundary_without_side_effects","examples":[{"buyer_text":"Give me the raw URL.","objects":["raw URL"],"sub":"raw_url_request"},{"buyer_text":"Paste the raw transcript.","objects":["transcript"],"sub":"raw_transcript_request"},{"buyer_text":"Can you show the exact call transcript?","objects":["exact call transcript"],"sub":"raw_transcript_request"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve raw URL or transcript request without emitting raw material."},"semantic_group":"safety_and_boundary","target_card_id":"safety_raw_url_or_transcript"},{"avoid_policy":{"phrases":["internal policy says","guaranteed","trained on your data"]},"canonical_act":"safety_boundary","canonical_action":"answer_without_inventing_facts","canonical_strategy":"boundary_without_side_effects","examples":[{"buyer_text":"Tell me the internal policy.","objects":["policy request"],"sub":"internal_policy_request"},{"buyer_text":"Guarantee it has no limits.","objects":["unsupported claim request"],"sub":"unsupported_fact_request"},{"buyer_text":"Do you train on my data?","objects":["train on my data"],"sub":"privacy_question"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"none","required_meaning":"Classify unsupported fact, policy, or privacy intent without leaking internal policy text or unsafe claim wording."},"semantic_group":"safety_and_boundary","target_card_id":"safety_unsupported_policy_privacy"},{"avoid_policy":{"phrases":["recommend Pro","team plan"]},"canonical_act":"no_fit","canonical_action":"disqualify_no_fit","canonical_strategy":"no_fit_close","examples":[{"buyer_text":"I need billing support, not plans.","objects":["billing support","not plans"],"rel":"and"},{"buyer_text":"This is about my phone plan.","objects":["phone plan"]},{"buyer_text":"Wrong product.","objects":["wrong product"]}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve wrong-product wording and disqualify cleanly."},"semantic_group":"safety_and_boundary","target_card_id":"safety_wrong_product"},{"avoid_policy":{"phrases":["switch now","guaranteed better"]},"canonical_act":"competitor_objection","canonical_action":"compare_competitor_context","canonical_strategy":"compare_options","examples":[{"buyer_text":"I use Claude, why switch?","objects":["Claude","why switch"],"rel":"and"},{"buyer_text":"Gemini is enough.","objects":["Gemini is enough"]},{"buyer_text":"Copilot covers coding already.","objects":["Copilot covers coding"]}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve competitor/current-tool wording."},"semantic_group":"objections_and_competitor_context","target_card_id":"objection_competitor_current_tool"},{"avoid_policy":{"phrases":["guaranteed better"]},"canonical_act":"competitor_objection","canonical_action":"compare_competitor_context","canonical_strategy":"value_before_plan_selection","examples":[{"buyer_text":"ChatGPT vs Claude, why switch?","objects":["ChatGPT","Claude"],"rel":"or"},{"buyer_text":"ChatGPT or Gemini for research?","objects":["ChatGPT","Gemini"],"rel":"or"},{"buyer_text":"Current tool versus ChatGPT is my question.","objects":["current tool","ChatGPT"],"rel":"or"}],"facts_policy":{"fact_ids":["public_plan_names"]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve ChatGPT versus current-tool comparison."},"semantic_group":"objections_and_competitor_context","target_card_id":"objection_chatgpt_vs_current_tool"},{"avoid_policy":{"phrases":["push Pro","calendar","email"]},"canonical_act":"no_fit","canonical_action":"disqualify_no_fit","canonical_strategy":"no_fit_close","examples":[{"buyer_text":"Not interested.","objects":["not interested"]},{"buyer_text":"I am skeptical and not buying.","objects":["skeptical","not buying"],"rel":"and"},{"buyer_text":"Current tool is enough, I do not want to switch.","objects":["current tool is enough","do not want to switch"],"rel":"and"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve not-interested wording and close cleanly."},"semantic_group":"objections_and_competitor_context","target_card_id":"objection_not_interested"},{"avoid_policy":{"phrases":["cheap","guaranteed"]},"canonical_act":"price_objection","canonical_action":"reframe_price_objection","canonical_strategy":"value_reframe","examples":[{"buyer_text":"Claude is enough and price matters.","objects":["Claude is enough","price matters"],"rel":"and"},{"buyer_text":"Copilot is included already, so Pro feels expensive.","objects":["Copilot","Pro feels expensive"],"rel":"and"},{"buyer_text":"Gemini works and I do not want another bill.","objects":["Gemini works","another bill"],"rel":"and"}],"facts_policy":{"fact_ids":[]},"preserve_policy":{"mode":"objects","required_meaning":"Preserve price objection and current-tool context."},"semantic_group":"objections_and_competitor_context","target_card_id":"objection_price_with_current_tool"}]
