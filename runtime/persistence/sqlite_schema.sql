PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sales_campaigns (
  campaign_id TEXT PRIMARY KEY,
  client_name TEXT,
  product_name TEXT,
  product_category TEXT,
  customer_type TEXT,
  country_or_region TEXT,
  language TEXT,
  approved_opening TEXT,
  qualification_questions_json TEXT,
  allowed_claims_json TEXT,
  forbidden_claims_json TEXT,
  required_disclosures_json TEXT,
  escalation_triggers_json TEXT,
  scheduling_goal TEXT,
  human_handoff_role TEXT,
  compliance_notes TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS leads (
  lead_id TEXT PRIMARY KEY,
  customer_type TEXT,
  full_name TEXT,
  phone_number TEXT,
  email TEXT,
  company_name TEXT,
  role_title TEXT,
  source TEXT,
  region TEXT,
  language TEXT,
  contact_status TEXT,
  consent_status TEXT,
  do_not_call INTEGER NOT NULL DEFAULT 0,
  do_not_call_reason TEXT,
  preferred_contact_time TEXT,
  owner_user_id TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS call_sessions (
  call_id TEXT PRIMARY KEY,
  campaign_id TEXT,
  lead_id TEXT NOT NULL,
  channel TEXT,
  started_at TEXT,
  ended_at TEXT,
  call_status TEXT,
  current_stage TEXT,
  current_interest_state TEXT,
  current_emotion_label TEXT,
  current_strategy TEXT,
  confidence REAL,
  transcript_storage_mode TEXT,
  transcript_text TEXT,
  call_summary TEXT,
  created_by TEXT,
  created_at TEXT,
  FOREIGN KEY (campaign_id) REFERENCES sales_campaigns (campaign_id),
  FOREIGN KEY (lead_id) REFERENCES leads (lead_id)
);

CREATE TABLE IF NOT EXISTS qualification_answers (
  answer_id TEXT PRIMARY KEY,
  call_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  stage TEXT,
  question_text TEXT,
  answer_text TEXT,
  normalized_answer_json TEXT,
  detected_emotion TEXT,
  interest_state_after_answer TEXT,
  selected_strategy TEXT,
  confidence REAL,
  created_at TEXT,
  FOREIGN KEY (call_id) REFERENCES call_sessions (call_id),
  FOREIGN KEY (lead_id) REFERENCES leads (lead_id)
);

CREATE TABLE IF NOT EXISTS turn_decisions (
  decision_id TEXT PRIMARY KEY,
  call_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  turn_index INTEGER,
  stage TEXT,
  detected_emotion TEXT,
  interest_state TEXT,
  selected_strategy TEXT,
  next_action TEXT,
  call_control TEXT,
  agent_response TEXT,
  confidence REAL,
  rationale TEXT,
  guardrail_flags_json TEXT,
  created_at TEXT,
  FOREIGN KEY (call_id) REFERENCES call_sessions (call_id),
  FOREIGN KEY (lead_id) REFERENCES leads (lead_id)
);

CREATE TABLE IF NOT EXISTS call_outcomes (
  outcome_id TEXT PRIMARY KEY,
  call_id TEXT NOT NULL,
  lead_id TEXT NOT NULL,
  call_status TEXT,
  interest_state TEXT,
  selected_strategy TEXT,
  appointment_scheduled INTEGER NOT NULL DEFAULT 0,
  appointment_time TEXT,
  escalation_reason TEXT,
  call_summary TEXT,
  next_action TEXT,
  call_control TEXT,
  created_at TEXT,
  FOREIGN KEY (call_id) REFERENCES call_sessions (call_id),
  FOREIGN KEY (lead_id) REFERENCES leads (lead_id)
);

CREATE TABLE IF NOT EXISTS appointments (
  appointment_id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL,
  call_id TEXT NOT NULL,
  scheduled_time TEXT,
  timezone TEXT,
  assigned_sales_agent_id TEXT,
  appointment_status TEXT,
  confirmation_text TEXT,
  calendar_event_id TEXT,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY (lead_id) REFERENCES leads (lead_id),
  FOREIGN KEY (call_id) REFERENCES call_sessions (call_id)
);

CREATE TABLE IF NOT EXISTS escalations (
  escalation_id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL,
  call_id TEXT NOT NULL,
  escalation_reason TEXT,
  severity TEXT,
  assigned_to TEXT,
  status TEXT,
  notes TEXT,
  created_at TEXT,
  resolved_at TEXT,
  FOREIGN KEY (lead_id) REFERENCES leads (lead_id),
  FOREIGN KEY (call_id) REFERENCES call_sessions (call_id)
);

CREATE INDEX IF NOT EXISTS idx_leads_contact_status ON leads (contact_status);
CREATE INDEX IF NOT EXISTS idx_sales_campaigns_product_category ON sales_campaigns (product_category);
CREATE INDEX IF NOT EXISTS idx_call_sessions_lead_id ON call_sessions (lead_id);
CREATE INDEX IF NOT EXISTS idx_qualification_answers_call_id ON qualification_answers (call_id);
CREATE INDEX IF NOT EXISTS idx_turn_decisions_call_id ON turn_decisions (call_id);
CREATE INDEX IF NOT EXISTS idx_call_outcomes_interest_state ON call_outcomes (interest_state);
CREATE INDEX IF NOT EXISTS idx_appointments_lead_id ON appointments (lead_id);
CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalations (status);
