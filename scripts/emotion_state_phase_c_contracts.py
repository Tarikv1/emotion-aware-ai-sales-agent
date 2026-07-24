from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from runtime.contracts.emotion_state_contracts import (
    PERCEIVED_STATE_FIELDS,
    EmotionStateContractError,
    validate_perceived_customer_state,
)


class PhaseCContractError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class PhaseCEventRejected(PhaseCContractError):
    pass


@dataclass(frozen=True)
class PhaseCSyntheticEvidenceAtomV1:
    schema_version: str
    evidence_ref: str
    independence_key: str
    operational_signal: str
    direction: str
    modality: str
    evidence_class: str
    quality_bucket: str


@dataclass(frozen=True)
class PhaseCSyntheticEvidenceFrameV1:
    schema_version: str
    fixture_only: bool
    call_session_id: str
    campaign_profile_id: str
    campaign_profile_version: str
    turn_id: str
    turn_sequence: int
    event_id: str
    input_revision: int
    evidence_atoms: tuple[PhaseCSyntheticEvidenceAtomV1, ...]


@dataclass(frozen=True)
class PhaseCEventWatermarkV1:
    expected_session_id: str
    expected_campaign_profile_id: str
    expected_campaign_profile_version: str
    last_turn_sequence: int
    turn_sequence_by_id: tuple[tuple[str, int], ...]
    turn_id_by_sequence: tuple[tuple[int, str], ...]
    last_input_revision_by_turn: tuple[tuple[str, int], ...]
    seen_event_ids: frozenset[str]
    event_history_by_id: tuple[tuple[str, str, int], ...]


@dataclass(frozen=True)
class PhaseCExpectedInternalProjectionV1:
    gross_supporting_units: tuple[tuple[str, int], ...]
    gross_opposing_units: tuple[tuple[str, int], ...]
    uncapped_net_support: tuple[tuple[str, int], ...]
    capped_net_support: tuple[tuple[str, int], ...]
    contradictory_signals: tuple[str, ...]
    seen_independence_keys: tuple[str, ...]
    internal_incumbent: str | None
    incumbent_tenure: int
    entry_confirmation_keys_by_signal: tuple[tuple[str, tuple[str, ...]], ...]
    switch_challenger: str | None
    switch_confirmation_keys: tuple[str, ...]
    release_streak: int
    contributing_evidence_refs: tuple[str, ...]
    seen_evidence_refs: tuple[str, ...]
    retired_independence_keys: tuple[str, ...]
    accepted_turn_count: int
    last_emitted_selected_signal: str | None
    last_emitted_selected_support: int | None


@dataclass(frozen=True)
class PhaseCExpectedAcceptedStepV1:
    disposition: str
    expected_output_bytes: bytes
    expected_internal: PhaseCExpectedInternalProjectionV1


@dataclass(frozen=True)
class PhaseCExpectedRejectedStepV1:
    disposition: str
    rejection_code: str
    prior_state_bytes_unchanged: bool


@dataclass(frozen=True)
class PhaseCScenarioSessionV1:
    session_alias: str
    frames: tuple[PhaseCSyntheticEvidenceFrameV1, ...]


@dataclass(frozen=True)
class PhaseCScenarioAttemptV1:
    state_session_alias: str
    frame_session_alias: str
    frame_index: int
    mutation_kind: str
    mutation_parameter: str | None


@dataclass(frozen=True)
class PhaseCScenarioV1:
    case_id: str
    family: str
    signal_family: str
    modality_family: str
    sessions: tuple[PhaseCScenarioSessionV1, ...]
    attempt_order: tuple[PhaseCScenarioAttemptV1, ...]
    expected_steps: tuple[
        PhaseCExpectedAcceptedStepV1 | PhaseCExpectedRejectedStepV1,
        ...,
    ]


ATOM_FIELDS = frozenset({
    "schema_version", "evidence_ref", "independence_key",
    "operational_signal", "direction", "modality", "evidence_class",
    "quality_bucket",
})
FRAME_FIELDS = frozenset({
    "schema_version", "fixture_only", "call_session_id",
    "campaign_profile_id", "campaign_profile_version", "turn_id",
    "turn_sequence", "event_id", "input_revision", "evidence_atoms",
})
ATOM_FIELD_ORDER = (
    "schema_version", "evidence_ref", "independence_key",
    "operational_signal", "direction", "modality", "evidence_class",
    "quality_bucket",
)
FRAME_FIELD_ORDER = (
    "schema_version", "fixture_only", "call_session_id",
    "campaign_profile_id", "campaign_profile_version", "turn_id",
    "turn_sequence", "event_id", "input_revision", "evidence_atoms",
)
OPAQUE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
EVIDENCE_REF_PATTERN = re.compile(
    r"^evidence:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
FORBIDDEN_PHASE_C_KEY_FRAGMENTS = (
    "acoustic_features", "probabilities", "model_id", "dataset_id",
    "audio_bytes", "raw_audio", "transcript_text", "raw_transcript",
    "customer_name", "customer_phone", "customer_email",
    "speaker_embedding", "voiceprint", "provider_payload", "api_key",
    "access_token", "auth_token", "password", "secret", "private_key",
    "hidden_reasoning",
)
CLASS_MODALITY = MappingProxyType({
    "unsolicited_explicit_statement": "text",
    "transcript_meaning": "text",
    "dialogue_context": "dialogue",
    "synthetic_acoustic_symbol": "acoustic",
    "weak_behavioral_proxy": "dialogue",
})
EXPECTED_SCENARIO_IDS = (
    "explicit_confusion_entry",
    "explicit_disengagement_entry",
    "explicit_frustration_entry",
    "explicit_hesitation_entry",
    "explicit_interest_entry",
    "transcript_three_turn_entry",
    "repeated_independence_zero_addition",
    "duplicate_event_rejected",
    "duplicate_reference_rejected",
    "acoustic_only_capped",
    "multimodal_two_turn_entry",
    "same_signal_contradiction",
    "low_quality_acoustic_abstains",
    "empty_frame_missing_input",
    "release_after_two_below_threshold",
    "switch_after_two_confirmations",
    "entry_tie_abstains",
    "incumbent_survives_unqualified_challenger",
    "latest_turn_correction_replay",
    "closed_turn_correction_rejected",
    "cross_session_rejected",
    "cross_campaign_rejected",
    "wrong_campaign_version_rejected",
    "noncanonical_atom_order_rejected",
    "forbidden_phase_b_field_rejected",
    "simultaneous_sessions_isolated",
    "canonical_replay_bytes",
    "dialogue_only_low_quality",
    "support_saturation",
    "opposition_below_contradiction_threshold",
)
EXPECTED_SCENARIO_CLASSIFICATIONS = MappingProxyType({
    "explicit_confusion_entry": ("entry", "confusion", "text"),
    "explicit_disengagement_entry": ("entry", "disengagement", "text"),
    "explicit_frustration_entry": ("entry", "frustration", "text"),
    "explicit_hesitation_entry": ("entry", "hesitation", "text"),
    "explicit_interest_entry": ("entry", "interest", "text"),
    "transcript_three_turn_entry": ("entry", "confusion", "text"),
    "repeated_independence_zero_addition": ("independence", "interest", "text"),
    "duplicate_event_rejected": ("rejection", "confusion", "text"),
    "duplicate_reference_rejected": ("rejection", "confusion", "text"),
    "acoustic_only_capped": ("abstention", "hesitation", "acoustic"),
    "multimodal_two_turn_entry": ("entry", "frustration", "multimodal"),
    "same_signal_contradiction": ("contradiction", "confusion", "multimodal"),
    "low_quality_acoustic_abstains": ("abstention", "hesitation", "acoustic"),
    "empty_frame_missing_input": ("abstention", "none", "none"),
    "release_after_two_below_threshold": ("hysteresis", "frustration", "text"),
    "switch_after_two_confirmations": ("hysteresis", "mixed", "text"),
    "entry_tie_abstains": ("hysteresis", "mixed", "text"),
    "incumbent_survives_unqualified_challenger": (
        "hysteresis",
        "mixed",
        "text",
    ),
    "latest_turn_correction_replay": ("correction", "interest", "text"),
    "closed_turn_correction_rejected": ("rejection", "confusion", "text"),
    "cross_session_rejected": ("rejection", "confusion", "text"),
    "cross_campaign_rejected": ("rejection", "confusion", "text"),
    "wrong_campaign_version_rejected": ("rejection", "confusion", "text"),
    "noncanonical_atom_order_rejected": ("rejection", "mixed", "text"),
    "forbidden_phase_b_field_rejected": ("rejection", "confusion", "text"),
    "simultaneous_sessions_isolated": ("isolation", "mixed", "text"),
    "canonical_replay_bytes": ("determinism", "confusion", "text"),
    "dialogue_only_low_quality": ("abstention", "hesitation", "dialogue"),
    "support_saturation": ("saturation", "confusion", "text"),
    "opposition_below_contradiction_threshold": (
        "contradiction",
        "confusion",
        "multimodal",
    ),
})
SCENARIO_MATRIX_FIELDS = frozenset({"schema_version", "policy_id", "scenarios"})
SCENARIO_FIELDS = frozenset({
    "case_id",
    "family",
    "signal_family",
    "modality_family",
    "sessions",
    "attempt_order",
    "expected_steps",
})
SCENARIO_SESSION_FIELDS = frozenset({"session_alias", "frames"})
SCENARIO_ATTEMPT_FIELDS = frozenset({
    "state_session_alias",
    "frame_session_alias",
    "frame_index",
    "mutation_kind",
    "mutation_parameter",
})
EXPECTED_ACCEPTED_FIELDS = frozenset({
    "disposition",
    "expected_output",
    "expected_internal",
})
EXPECTED_REJECTED_FIELDS = frozenset({
    "disposition",
    "rejection_code",
    "prior_state_bytes_unchanged",
})
EXPECTED_INTERNAL_FIELDS = frozenset({
    "gross_supporting_units",
    "gross_opposing_units",
    "uncapped_net_support",
    "capped_net_support",
    "contradictory_signals",
    "seen_independence_keys",
    "internal_incumbent",
    "incumbent_tenure",
    "entry_confirmation_keys_by_signal",
    "switch_challenger",
    "switch_confirmation_keys",
    "release_streak",
    "contributing_evidence_refs",
    "seen_evidence_refs",
    "retired_independence_keys",
    "accepted_turn_count",
    "last_emitted_selected_signal",
    "last_emitted_selected_support",
})
ALLOWED_SCENARIO_MUTATIONS = (
    "none",
    "reverse_atom_order",
    "add_forbidden_field",
)
SCENARIO_FORBIDDEN_FIELD_MUTATIONS = frozenset({
    "acoustic_features",
    "probabilities",
    "model_id",
    "dataset_id",
})
SCENARIO_REJECTION_CODES = frozenset({
    "duplicate_event",
    "duplicate_evidence_reference",
    "stale_turn",
    "cross_session",
    "cross_campaign",
    "wrong_campaign_version",
    "noncanonical_atom_order",
    "forbidden_field",
})
FROZEN_SCENARIO_CANONICAL_SHA256: Final[str] = (
    "D01FBD7677537A0A91D01E0EA8354D079491C13BBD81EC8BAC97E7BBC4520FB0"
)
# Per-case attempt and acceptance/rejection authority. Each step is
# (state alias, frame alias, frame index, mutation kind, mutation parameter,
#  disposition, rejection code).
EXPECTED_SCENARIO_STEP_AUTHORITY = (
    ("explicit_confusion_entry", (("A", "A", 0, "none", None, "accepted", None),)),
    ("explicit_disengagement_entry", (("A", "A", 0, "none", None, "accepted", None),)),
    ("explicit_frustration_entry", (("A", "A", 0, "none", None, "accepted", None),)),
    ("explicit_hesitation_entry", (("A", "A", 0, "none", None, "accepted", None),)),
    ("explicit_interest_entry", (("A", "A", 0, "none", None, "accepted", None),)),
    ("transcript_three_turn_entry", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
        ("A", "A", 2, "none", None, "accepted", None),
    )),
    ("repeated_independence_zero_addition", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
    )),
    ("duplicate_event_rejected", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "rejected", "duplicate_event"),
    )),
    ("duplicate_reference_rejected", (
        ("A", "A", 0, "none", None, "accepted", None),
        (
            "A", "A", 1, "none", None, "rejected",
            "duplicate_evidence_reference",
        ),
    )),
    ("acoustic_only_capped", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
        ("A", "A", 2, "none", None, "accepted", None),
    )),
    ("multimodal_two_turn_entry", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
    )),
    ("same_signal_contradiction", (("A", "A", 0, "none", None, "accepted", None),)),
    ("low_quality_acoustic_abstains", (("A", "A", 0, "none", None, "accepted", None),)),
    ("empty_frame_missing_input", (("A", "A", 0, "none", None, "accepted", None),)),
    ("release_after_two_below_threshold", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
        ("A", "A", 2, "none", None, "accepted", None),
        ("A", "A", 3, "none", None, "accepted", None),
        ("A", "A", 4, "none", None, "accepted", None),
        ("A", "A", 5, "none", None, "accepted", None),
    )),
    ("switch_after_two_confirmations", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
        ("A", "A", 2, "none", None, "accepted", None),
        ("A", "A", 3, "none", None, "accepted", None),
    )),
    ("entry_tie_abstains", (("A", "A", 0, "none", None, "accepted", None),)),
    ("incumbent_survives_unqualified_challenger", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
        ("A", "A", 2, "none", None, "accepted", None),
        ("A", "A", 3, "none", None, "accepted", None),
    )),
    ("latest_turn_correction_replay", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
    )),
    ("closed_turn_correction_rejected", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
        ("A", "A", 2, "none", None, "rejected", "stale_turn"),
    )),
    ("cross_session_rejected", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "B", 0, "none", None, "rejected", "cross_session"),
    )),
    ("cross_campaign_rejected", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "rejected", "cross_campaign"),
    )),
    ("wrong_campaign_version_rejected", (
        ("A", "A", 0, "none", None, "accepted", None),
        (
            "A", "A", 1, "none", None, "rejected",
            "wrong_campaign_version",
        ),
    )),
    ("noncanonical_atom_order_rejected", ((
        "A", "A", 0, "reverse_atom_order", None, "rejected",
        "noncanonical_atom_order",
    ),)),
    ("forbidden_phase_b_field_rejected", (
        (
            "A", "A", 0, "add_forbidden_field", "acoustic_features",
            "rejected", "forbidden_field",
        ),
        (
            "A", "A", 0, "add_forbidden_field", "probabilities",
            "rejected", "forbidden_field",
        ),
        (
            "A", "A", 0, "add_forbidden_field", "model_id",
            "rejected", "forbidden_field",
        ),
        (
            "A", "A", 0, "add_forbidden_field", "dataset_id",
            "rejected", "forbidden_field",
        ),
    )),
    ("simultaneous_sessions_isolated", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("B", "B", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
        ("B", "B", 1, "none", None, "accepted", None),
    )),
    ("canonical_replay_bytes", (
        ("A", "A", 0, "none", None, "accepted", None),
        ("A", "A", 1, "none", None, "accepted", None),
        ("A", "A", 2, "none", None, "accepted", None),
    )),
    ("dialogue_only_low_quality", (("A", "A", 0, "none", None, "accepted", None),)),
    ("support_saturation", (("A", "A", 0, "none", None, "accepted", None),)),
    (
        "opposition_below_contradiction_threshold",
        (("A", "A", 0, "none", None, "accepted", None),),
    ),
)
EXPECTED_SCENARIO_CANONICAL_SHA256_BY_CASE = (
    ("explicit_confusion_entry", "9909AD632F63B99C5859FC344C21DCFFD52B84F7036B0F2B4D31493D39186B09"),
    ("explicit_disengagement_entry", "14D063CA3E580A87BB06080FA0C8EC7DB53931DDB1C01FD964B7C3A89DF1583D"),
    ("explicit_frustration_entry", "C4014510E81E08A0AC04CE3A466453BB27374D163555DFF9776701A17551119F"),
    ("explicit_hesitation_entry", "114A3D9FD39601B090DD2FB19D177F5C958B9A95C6EA2D4C486F83465373034D"),
    ("explicit_interest_entry", "EFCD5127EA8C1545CFF39E680C61B6FB772E1085FCE8AF00965E26467FD358CE"),
    ("transcript_three_turn_entry", "E6FAE470664B5D5201B0F4BEA3AD64ED31BE077FD8774B3BE5765E988D416199"),
    ("repeated_independence_zero_addition", "DC4C0A6F1E5F19A45AB39468A66C87FEE50A858CBBAD0F9C7A4ABA239D8A794D"),
    ("duplicate_event_rejected", "167BBC419D083B135F908D1823EAF2EAE385DCB731F6592AD220B1DAEA92E67D"),
    ("duplicate_reference_rejected", "61F2A9EE41BB7FF82B311BFEFE9468F3062ACB2FF192292FD4BF5EE604D58587"),
    ("acoustic_only_capped", "C430F926882A76B8EDF84B8B4447780EEE7F23187A100F93560A4DF288930031"),
    ("multimodal_two_turn_entry", "08041615DD9AFED33EE76BF68C956EC5BF690AEE056A69EC5CBB39E0CCD92EC1"),
    ("same_signal_contradiction", "41CBA9BB6D91FE588E548CA5A019CEE7C00E940011ECC51A772AFD719E0BEB95"),
    ("low_quality_acoustic_abstains", "A0F52E987CBDD03E462BDFC59B3F8412B4EAEB62BA1E2686903AC3E9929C1C85"),
    ("empty_frame_missing_input", "1504C9C7CB96F74CF4230FAC5485B78C9702E4E6573ABB8883C4AAD07F13818B"),
    ("release_after_two_below_threshold", "F737E07E8DEA22C686E86B7AA41006E34690AC29FEEA8F3E1DF926C384F5080A"),
    ("switch_after_two_confirmations", "7C567A077C89ACC15FDF7E0581CE6EA408F7C6106BE0DA155988443C6630DF50"),
    ("entry_tie_abstains", "93828CAE2CF3AA80795624DFE129F05B9E2A8891799CB9E423936FCA40CBC3D2"),
    ("incumbent_survives_unqualified_challenger", "586B22D2099F3258FE45A667407A7C81D83411AADE34482D74288284A32D71D8"),
    ("latest_turn_correction_replay", "DD37300E263BCB11491658CA5CB718C131FFAA168FF9C639A69FF6AA901595E3"),
    ("closed_turn_correction_rejected", "4A61A56322859211748701EB16CBDC90C6A61BBA30C4587B25E84E6AC0FAC6B6"),
    ("cross_session_rejected", "B1E612D6F92A7E701C90151947DFB775480B6ED4285D54ED244A167E2263925A"),
    ("cross_campaign_rejected", "A53BC809F5ADDECE0A61CEECC23061A8AAB3085A1EA003C9259FF21B831EB597"),
    ("wrong_campaign_version_rejected", "803BDB282463B2116C5557E9D44A2BF81D4DAE268D2C64780EDCAABBC768CEC6"),
    ("noncanonical_atom_order_rejected", "46C0E807815118E24B40CF1F36566F9968675909B66D657811BE832F2D42F34C"),
    ("forbidden_phase_b_field_rejected", "B394D3C3C4AA9A87CB50B29AA6D2D431A37B593EAF815439AD18FD88F04EC36C"),
    ("simultaneous_sessions_isolated", "407470F495B082BF5153D3B8F2F9A22977D1B966771C4C11709DEBDCADA4BDC5"),
    ("canonical_replay_bytes", "1EC07EBDB964DFCDE810968C7E12ACC3F0BB11170036CB2B1F0265163DEB5452"),
    ("dialogue_only_low_quality", "FE94FE265F3E4ECB2FF77239B128AF38CCF84C4DDADE68C7834596BBEF4F32B3"),
    ("support_saturation", "318AB5EBF8E413710DBFC16E07741B2EBC768A2B0E3B8433A6BFC8ED47208AB8"),
    ("opposition_below_contradiction_threshold", "A5A5B0B344793AE31A8678D4A9D51D3463327346B699113D45F6B49A2CB11168"),
)


FROZEN_POLICY_CANONICAL_JSON: Final[str] = r'''{
  "abstained_allowed_effects": ["preserve"],
  "abstention_primary_priority": ["contradictory_evidence", "low_audio_quality", "missing_input", "insufficient_evidence"],
  "abstention_reason_order": ["phase_a_no_audio", "insufficient_evidence", "contradictory_evidence", "low_audio_quality", "missing_input", "stale_input"],
  "acoustic_only_cap": 400,
  "acoustic_only_allowed_effects": ["preserve"],
  "agreement_bonus": 100,
  "agreement_eligibility": "newly_contributing_positive_support_atoms_only",
  "agreement_requirements": {"distinct_evidence_refs": 2, "distinct_independence_keys": 2, "distinct_modalities": 2},
  "allowed_effect_order": ["preserve", "soften", "shorten", "clarify", "acknowledge", "handoff", "abstain", "stop"],
  "allowed_effects_by_signal": {
    "confusion": ["preserve", "shorten", "clarify", "acknowledge", "handoff"],
    "disengagement": ["preserve", "soften", "shorten", "acknowledge", "handoff"],
    "frustration": ["preserve", "soften", "shorten", "acknowledge", "handoff"],
    "hesitation": ["preserve", "clarify", "acknowledge"],
    "interest": ["preserve"]
  },
  "allowed_modalities_by_evidence_class": {
    "dialogue_context": ["dialogue"],
    "synthetic_acoustic_symbol": ["acoustic"],
    "transcript_meaning": ["text"],
    "unsolicited_explicit_statement": ["text"],
    "weak_behavioral_proxy": ["dialogue"]
  },
  "base_support_units": {"dialogue_context": 300, "synthetic_acoustic_symbol": 180, "transcript_meaning": 450, "unsolicited_explicit_statement": 700, "weak_behavioral_proxy": 100},
  "blocked_effect_order": ["expand_action_set", "increase_persuasion_intensity", "create_new_close", "override_refusal", "override_do_not_call", "rewrite_protected_text", "exploit_vulnerability", "voice_only_emotional_appeal", "unsupported_claim", "automatic_close_or_payment"],
  "canonical_direction_order": ["supports", "opposes"],
  "canonical_evidence_class_order": ["unsolicited_explicit_statement", "transcript_meaning", "dialogue_context", "synthetic_acoustic_symbol", "weak_behavioral_proxy"],
  "canonical_modality_order": ["text", "dialogue", "acoustic"],
  "canonical_quality_order": ["high", "medium", "low", "unusable"],
  "canonical_signal_order": ["confusion", "disengagement", "frustration", "hesitation", "interest"],
  "confirmation_counts": {"entry": 2, "explicit_statement_entry": 1, "release": 2, "switch": 2},
  "confirmation_key_policy": "one_canonical_new_supporting_key_per_signal_per_turn",
  "confidence_bucket_thresholds": {"high": 750, "medium": 550},
  "contradiction_cap": 350,
  "contradiction_thresholds": {"gross_opposition": 300, "gross_support": 300},
  "correction_policy": "most_recent_turn_exact_next_revision_only",
  "evidence_policy_version": "emotion-state-evidence-v2",
  "emitted_abstention_reasons": ["insufficient_evidence", "contradictory_evidence", "low_audio_quality", "missing_input"],
  "entry_threshold": 550,
  "explicit_entry_evidence_class": "unsolicited_explicit_statement",
  "fixture_only": true,
  "minimum_switch_advantage": 150,
  "policy_id": "emotion-state-phase-c0-synthetic-v1",
  "quality_multipliers": {"high": 1000, "low": 400, "medium": 750, "unusable": 0},
  "quality_cap_basis": "highest_nonzero_current_contributing_quality",
  "release_threshold": 350,
  "retained_support_milli": 800,
  "rounding_policy": "integer_floor_toward_zero",
  "scale": 1000,
  "schema_version": "PhaseCFrozenEvidencePolicyV1",
  "support_saturation": 1000,
  "switch_threshold": 650,
  "tie_policy": {"incumbent": "retain_unless_all_switch_conditions_pass", "no_incumbent": "abstain"},
  "total_quality_caps": {"high": 1000, "low": 400, "medium": 750, "unusable": 0},
  "trajectory_delta_threshold": 100,
  "visibility_threshold": 200
}'''


def canonical_json_bytes(payload: Any) -> bytes:
    try:
        text = json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PhaseCContractError("payload is not canonical JSON") from exc
    return (text + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _reject_constant(value: str) -> None:
    raise PhaseCContractError(f"non-finite JSON constant is forbidden: {value}")


def _parse_finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise PhaseCContractError(f"non-finite JSON number is forbidden: {value}")
    return parsed


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PhaseCContractError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
            parse_float=_parse_finite_float,
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PhaseCContractError(f"invalid JSON: {path.name}") from exc
    if type(value) is not dict:
        raise PhaseCContractError("top-level JSON value must be an object")
    return value


def _validate_exact(actual: Any, expected: Any, path: str) -> None:
    if type(expected) is dict:
        if type(actual) is not dict or set(actual) != set(expected):
            raise PhaseCContractError(f"policy object mismatch: {path}")
        for key in expected:
            _validate_exact(actual[key], expected[key], f"{path}.{key}")
        return
    if type(expected) is list:
        if type(actual) is not list or len(actual) != len(expected):
            raise PhaseCContractError(f"policy array mismatch: {path}")
        for index, expected_value in enumerate(expected):
            _validate_exact(actual[index], expected_value, f"{path}[{index}]")
        return
    if type(actual) is not type(expected) or actual != expected:
        raise PhaseCContractError(f"policy scalar mismatch: {path}")


def validate_phase_c_policy(payload: dict[str, Any]) -> dict[str, Any]:
    expected = json.loads(
        FROZEN_POLICY_CANONICAL_JSON,
        parse_constant=_reject_constant,
        object_pairs_hook=_unique_object,
    )
    _validate_exact(payload, expected, "policy")
    return payload


def _scan_forbidden_phase_c_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if type(key) is str and any(
                fragment in key.lower()
                for fragment in FORBIDDEN_PHASE_C_KEY_FRAGMENTS
            ):
                raise PhaseCContractError("forbidden_field")
            _scan_forbidden_phase_c_keys(child)
    elif type(value) is list:
        for child in value:
            _scan_forbidden_phase_c_keys(child)


def _require_fields(payload: dict[str, Any], fields: frozenset[str], prefix: str) -> None:
    if not fields.issubset(payload):
        raise PhaseCContractError(f"{prefix}_missing_fields")
    if set(payload) != fields:
        raise PhaseCContractError(f"{prefix}_unknown_fields")


def _require_opaque_identifier(value: Any) -> None:
    if type(value) is not str or OPAQUE_ID_PATTERN.fullmatch(value) is None:
        raise PhaseCContractError("invalid_opaque_identifier")


def _validate_atom_payload(
    payload: dict[str, Any],
    policy: dict[str, Any],
) -> PhaseCSyntheticEvidenceAtomV1:
    _scan_forbidden_phase_c_keys(payload)
    _require_fields(payload, ATOM_FIELDS, "atom")
    if payload["schema_version"] != "PhaseCSyntheticEvidenceAtomV1":
        raise PhaseCContractError("atom_schema")
    if any(type(payload[field]) is not str for field in ATOM_FIELD_ORDER):
        raise PhaseCContractError("atom_field_type")
    if EVIDENCE_REF_PATTERN.fullmatch(payload["evidence_ref"]) is None:
        raise PhaseCContractError("invalid_evidence_reference")
    _require_opaque_identifier(payload["independence_key"])
    enum_orders = (
        ("operational_signal", "canonical_signal_order"),
        ("direction", "canonical_direction_order"),
        ("modality", "canonical_modality_order"),
        ("evidence_class", "canonical_evidence_class_order"),
        ("quality_bucket", "canonical_quality_order"),
    )
    if any(payload[field] not in policy[order] for field, order in enum_orders):
        raise PhaseCContractError("unknown_atom_enum")
    if CLASS_MODALITY[payload["evidence_class"]] != payload["modality"]:
        raise PhaseCContractError("class_modality_mismatch")
    return PhaseCSyntheticEvidenceAtomV1(
        **{field: payload[field] for field in ATOM_FIELD_ORDER},
    )


def parse_phase_c_atom(
    payload: Any,
    policy: dict[str, Any],
) -> PhaseCSyntheticEvidenceAtomV1:
    validate_phase_c_policy(policy)
    _scan_forbidden_phase_c_keys(payload)
    if type(payload) is not dict:
        raise PhaseCContractError("atom_not_object")
    atom = _validate_atom_payload(dict(payload), policy)
    validate_phase_c_atom(atom, policy)
    return atom


def _atom_to_payload(atom: PhaseCSyntheticEvidenceAtomV1) -> dict[str, Any]:
    if type(atom) is not PhaseCSyntheticEvidenceAtomV1:
        raise PhaseCContractError("atom_field_type")
    return {field: getattr(atom, field) for field in ATOM_FIELD_ORDER}


def validate_phase_c_atom(
    atom: PhaseCSyntheticEvidenceAtomV1,
    policy: dict[str, Any],
) -> None:
    validate_phase_c_policy(policy)
    _validate_atom_payload(_atom_to_payload(atom), policy)


def atom_sort_key(
    atom: PhaseCSyntheticEvidenceAtomV1,
    policy: dict[str, Any],
) -> tuple[int, int, int, int, int, str, str]:
    validate_phase_c_atom(atom, policy)
    signal_order = policy["canonical_signal_order"]
    direction_order = policy["canonical_direction_order"]
    modality_order = policy["canonical_modality_order"]
    evidence_class_order = policy["canonical_evidence_class_order"]
    quality_order = policy["canonical_quality_order"]
    return (
        signal_order.index(atom.operational_signal),
        direction_order.index(atom.direction),
        modality_order.index(atom.modality),
        evidence_class_order.index(atom.evidence_class),
        quality_order.index(atom.quality_bucket),
        atom.independence_key,
        atom.evidence_ref,
    )


def _validate_frame_payload(
    payload: dict[str, Any],
    policy: dict[str, Any],
) -> PhaseCSyntheticEvidenceFrameV1:
    _scan_forbidden_phase_c_keys(payload)
    _require_fields(payload, FRAME_FIELDS, "frame")
    if payload["schema_version"] != "PhaseCSyntheticEvidenceFrameV1":
        raise PhaseCContractError("frame_schema")
    if payload["fixture_only"] is not True:
        raise PhaseCContractError("fixture_only_required")
    string_fields = (
        "call_session_id", "campaign_profile_id", "campaign_profile_version",
        "turn_id", "event_id",
    )
    if (
        type(payload["fixture_only"]) is not bool
        or any(type(payload[field]) is not str for field in string_fields)
        or type(payload["turn_sequence"]) is not int
        or type(payload["input_revision"]) is not int
        or type(payload["evidence_atoms"]) is not list
    ):
        raise PhaseCContractError("frame_field_type")
    for field in string_fields:
        _require_opaque_identifier(payload[field])
    atoms_list: list[PhaseCSyntheticEvidenceAtomV1] = []
    for item in payload["evidence_atoms"]:
        if type(item) is not dict:
            raise PhaseCContractError("atom_not_object")
        atoms_list.append(_validate_atom_payload(dict(item), policy))
    atoms = tuple(atoms_list)
    if len({atom.evidence_ref for atom in atoms}) != len(atoms):
        raise PhaseCContractError("duplicate_evidence_reference")
    if len({atom.independence_key for atom in atoms}) != len(atoms):
        raise PhaseCContractError("duplicate_independence_key")
    if atoms != tuple(sorted(atoms, key=lambda atom: atom_sort_key(atom, policy))):
        raise PhaseCContractError("noncanonical_atom_order")
    if payload["turn_sequence"] < 0 or payload["input_revision"] < 0:
        raise PhaseCContractError("invalid_event_counter")
    return PhaseCSyntheticEvidenceFrameV1(
        schema_version=payload["schema_version"],
        fixture_only=payload["fixture_only"],
        call_session_id=payload["call_session_id"],
        campaign_profile_id=payload["campaign_profile_id"],
        campaign_profile_version=payload["campaign_profile_version"],
        turn_id=payload["turn_id"],
        turn_sequence=payload["turn_sequence"],
        event_id=payload["event_id"],
        input_revision=payload["input_revision"],
        evidence_atoms=atoms,
    )


def parse_phase_c_frame(
    payload: Any,
    policy: dict[str, Any],
) -> PhaseCSyntheticEvidenceFrameV1:
    validate_phase_c_policy(policy)
    _scan_forbidden_phase_c_keys(payload)
    if type(payload) is not dict:
        raise PhaseCContractError("frame_not_object")
    frame = _validate_frame_payload(dict(payload), policy)
    validate_phase_c_frame(frame, policy)
    return frame


def _frame_to_payload(frame: PhaseCSyntheticEvidenceFrameV1) -> dict[str, Any]:
    if type(frame) is not PhaseCSyntheticEvidenceFrameV1:
        raise PhaseCContractError("frame_field_type")
    if type(frame.evidence_atoms) is not tuple:
        raise PhaseCContractError("frame_field_type")
    return {
        "schema_version": frame.schema_version,
        "fixture_only": frame.fixture_only,
        "call_session_id": frame.call_session_id,
        "campaign_profile_id": frame.campaign_profile_id,
        "campaign_profile_version": frame.campaign_profile_version,
        "turn_id": frame.turn_id,
        "turn_sequence": frame.turn_sequence,
        "event_id": frame.event_id,
        "input_revision": frame.input_revision,
        "evidence_atoms": [_atom_to_payload(atom) for atom in frame.evidence_atoms],
    }


def validate_phase_c_frame(
    frame: PhaseCSyntheticEvidenceFrameV1,
    policy: dict[str, Any],
) -> None:
    validate_phase_c_policy(policy)
    _validate_frame_payload(_frame_to_payload(frame), policy)


def _frozen_phase_c_policy() -> dict[str, Any]:
    return validate_phase_c_policy(json.loads(FROZEN_POLICY_CANONICAL_JSON))


def phase_c_frame_to_payload(
    frame: PhaseCSyntheticEvidenceFrameV1,
) -> dict[str, Any]:
    policy = _frozen_phase_c_policy()
    validate_phase_c_frame(frame, policy)
    payload = _frame_to_payload(frame)
    if parse_phase_c_frame(payload, policy) != frame:
        raise PhaseCContractError("frame_round_trip_failed")
    return payload


def scenario_payload_sha256(payload: dict[str, Any]) -> str:
    if type(payload) is not dict:
        raise PhaseCContractError("scenario_matrix_not_object")
    return sha256_bytes(canonical_json_bytes(payload))


def _require_scenario_fields(
    payload: Any,
    fields: frozenset[str],
    prefix: str,
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise PhaseCContractError(f"{prefix}_not_object")
    _require_fields(payload, fields, prefix)
    return payload


def _parse_string_tuple(
    value: Any,
    *,
    prefix: str,
    evidence_refs: bool = False,
) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise PhaseCContractError(f"{prefix}_type")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise PhaseCContractError(f"{prefix}_duplicate")
    if evidence_refs:
        if any(EVIDENCE_REF_PATTERN.fullmatch(item) is None for item in result):
            raise PhaseCContractError(f"{prefix}_reference")
    else:
        for item in result:
            _require_opaque_identifier(item)
    return result


def _unique_authority_order(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


def _validate_identity_sequence(
    values: tuple[str, ...],
    authority: tuple[str, ...],
    *,
    unknown_code: str,
    order_code: str | None,
) -> None:
    ordered_authority = _unique_authority_order(authority)
    if any(value not in ordered_authority for value in values):
        raise PhaseCContractError(unknown_code)
    if order_code is not None and tuple(
        value for value in ordered_authority if value in values
    ) != values:
        raise PhaseCContractError(order_code)


def _parse_dense_signal_int_map(
    value: Any,
    policy: dict[str, Any],
    prefix: str,
) -> tuple[tuple[str, int], ...]:
    signals = tuple(policy["canonical_signal_order"])
    if type(value) is not dict or tuple(value) != signals:
        raise PhaseCContractError(f"{prefix}_signal_order")
    result: list[tuple[str, int]] = []
    for signal in signals:
        units = value[signal]
        if type(units) is not int or units < 0:
            raise PhaseCContractError(f"{prefix}_units")
        result.append((signal, units))
    return tuple(result)


def _parse_entry_confirmation_map(
    value: Any,
    policy: dict[str, Any],
    known_independence_keys: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    signals = tuple(policy["canonical_signal_order"])
    if type(value) is not dict or tuple(value) != signals:
        raise PhaseCContractError("expected_internal_entry_signal_order")
    result: list[tuple[str, tuple[str, ...]]] = []
    for signal in signals:
        keys = _parse_string_tuple(
            value[signal],
            prefix="expected_internal_entry_keys",
        )
        _validate_identity_sequence(
            keys,
            known_independence_keys,
            unknown_code="scenario_internal_unknown_key",
            order_code="scenario_internal_key_order",
        )
        result.append((signal, keys))
    return tuple(result)


def _parse_expected_internal(
    payload: Any,
    policy: dict[str, Any],
    known_independence_keys: tuple[str, ...],
    known_evidence_refs: tuple[str, ...],
) -> PhaseCExpectedInternalProjectionV1:
    internal = _require_scenario_fields(
        payload,
        EXPECTED_INTERNAL_FIELDS,
        "expected_internal",
    )
    numeric_fields = (
        "gross_supporting_units",
        "gross_opposing_units",
        "uncapped_net_support",
        "capped_net_support",
    )
    numeric = {
        field: _parse_dense_signal_int_map(internal[field], policy, field)
        for field in numeric_fields
    }
    signals = tuple(policy["canonical_signal_order"])
    contradictory = _parse_string_tuple(
        internal["contradictory_signals"],
        prefix="expected_internal_contradictory_signals",
    )
    if (
        any(signal not in signals for signal in contradictory)
        or tuple(signal for signal in signals if signal in contradictory)
        != contradictory
    ):
        raise PhaseCContractError("expected_internal_contradictory_signal_order")
    seen_keys = _parse_string_tuple(
        internal["seen_independence_keys"],
        prefix="expected_internal_seen_keys",
    )
    _validate_identity_sequence(
        seen_keys,
        known_independence_keys,
        unknown_code="scenario_internal_unknown_key",
        order_code="scenario_internal_key_order",
    )
    entry = _parse_entry_confirmation_map(
        internal["entry_confirmation_keys_by_signal"],
        policy,
        known_independence_keys,
    )
    switch_keys = _parse_string_tuple(
        internal["switch_confirmation_keys"],
        prefix="expected_internal_switch_keys",
    )
    _validate_identity_sequence(
        switch_keys,
        known_independence_keys,
        unknown_code="scenario_internal_unknown_key",
        order_code="scenario_internal_key_order",
    )
    contributing_refs = _parse_string_tuple(
        internal["contributing_evidence_refs"],
        prefix="expected_internal_contributing_refs",
        evidence_refs=True,
    )
    _validate_identity_sequence(
        contributing_refs,
        known_evidence_refs,
        unknown_code="scenario_internal_unknown_reference",
        order_code=None,
    )
    seen_refs = _parse_string_tuple(
        internal["seen_evidence_refs"],
        prefix="expected_internal_seen_refs",
        evidence_refs=True,
    )
    _validate_identity_sequence(
        seen_refs,
        known_evidence_refs,
        unknown_code="scenario_internal_unknown_reference",
        order_code="scenario_internal_reference_order",
    )
    retired_keys = _parse_string_tuple(
        internal["retired_independence_keys"],
        prefix="expected_internal_retired_keys",
    )
    _validate_identity_sequence(
        retired_keys,
        known_independence_keys,
        unknown_code="scenario_internal_unknown_key",
        order_code="scenario_internal_key_order",
    )
    if not set(contributing_refs).issubset(seen_refs):
        raise PhaseCContractError("expected_internal_reference_coverage")
    if not set(retired_keys).issubset(seen_keys):
        raise PhaseCContractError("expected_internal_key_coverage")
    incumbent = internal["internal_incumbent"]
    challenger = internal["switch_challenger"]
    last_signal = internal["last_emitted_selected_signal"]
    if incumbent is not None and (
        type(incumbent) is not str or incumbent not in signals
    ):
        raise PhaseCContractError("expected_internal_incumbent")
    if challenger is not None and (
        type(challenger) is not str
        or challenger not in signals
        or challenger == incumbent
    ):
        raise PhaseCContractError("expected_internal_switch_challenger")
    if last_signal is not None and (
        type(last_signal) is not str or last_signal not in signals
    ):
        raise PhaseCContractError("expected_internal_last_signal")
    integer_fields = (
        "incumbent_tenure",
        "release_streak",
        "accepted_turn_count",
    )
    if any(
        type(internal[field]) is not int or internal[field] < 0
        for field in integer_fields
    ):
        raise PhaseCContractError("expected_internal_counter")
    last_support = internal["last_emitted_selected_support"]
    if (last_signal is None) != (last_support is None):
        raise PhaseCContractError("expected_internal_last_emission_pair")
    if last_support is not None and (
        type(last_support) is not int or last_support < 0
    ):
        raise PhaseCContractError("expected_internal_last_support")
    if incumbent is None and internal["incumbent_tenure"] != 0:
        raise PhaseCContractError("expected_internal_incumbent_tenure")
    entry_keys = tuple(
        key
        for _, keys in entry
        for key in keys
    )
    if (
        not set(entry_keys).issubset(seen_keys)
        or not set(switch_keys).issubset(seen_keys)
        or internal["accepted_turn_count"] < 1
        or (
            incumbent is None
            and (
                challenger is not None
                or switch_keys
                or internal["release_streak"] != 0
                or last_signal is not None
            )
        )
        or (
            incumbent is not None
            and (
                internal["incumbent_tenure"] < 1
                or entry_keys
                or (challenger is None) != (not switch_keys)
                or (
                    internal["release_streak"] > 0
                    and (challenger is not None or switch_keys)
                )
                or (
                    last_signal is not None
                    and last_signal != incumbent
                )
            )
        )
        or internal["release_streak"] >= policy["confirmation_counts"]["release"]
    ):
        raise PhaseCContractError("expected_internal_hysteresis")
    return PhaseCExpectedInternalProjectionV1(
        **numeric,
        contradictory_signals=contradictory,
        seen_independence_keys=seen_keys,
        internal_incumbent=incumbent,
        incumbent_tenure=internal["incumbent_tenure"],
        entry_confirmation_keys_by_signal=entry,
        switch_challenger=challenger,
        switch_confirmation_keys=switch_keys,
        release_streak=internal["release_streak"],
        contributing_evidence_refs=contributing_refs,
        seen_evidence_refs=seen_refs,
        retired_independence_keys=retired_keys,
        accepted_turn_count=internal["accepted_turn_count"],
        last_emitted_selected_signal=last_signal,
        last_emitted_selected_support=last_support,
    )


def _parse_expected_step(
    payload: Any,
    policy: dict[str, Any],
    known_independence_keys: tuple[str, ...],
    known_evidence_refs: tuple[str, ...],
) -> PhaseCExpectedAcceptedStepV1 | PhaseCExpectedRejectedStepV1:
    if type(payload) is not dict:
        raise PhaseCContractError("expected_step_not_object")
    disposition = payload.get("disposition")
    if disposition == "accepted":
        accepted = _require_scenario_fields(
            payload,
            EXPECTED_ACCEPTED_FIELDS,
            "expected_accepted_step",
        )
        output = accepted["expected_output"]
        if type(output) is not dict or set(output) != PERCEIVED_STATE_FIELDS:
            raise PhaseCContractError("expected_output_fields")
        reasons = output["abstention_reasons"]
        if type(reasons) is list and tuple(reasons) != tuple(
            reason
            for reason in policy["abstention_reason_order"]
            if reason in reasons
        ):
            raise PhaseCContractError("scenario_abstention_reason_order")
        if (
            output["runtime_approved"] is not False
            or output["valence_estimate"] != "not_inferable"
            or output["activation_estimate"] != "not_inferable"
            or output["engagement_estimate"] != "not_inferable"
        ):
            raise PhaseCContractError("expected_output_phase_c_boundary")
        try:
            validate_perceived_customer_state(output)
        except EmotionStateContractError as exc:
            raise PhaseCContractError("expected_output_contract") from exc
        return PhaseCExpectedAcceptedStepV1(
            disposition="accepted",
            expected_output_bytes=canonical_json_bytes(output),
            expected_internal=_parse_expected_internal(
                accepted["expected_internal"],
                policy,
                known_independence_keys,
                known_evidence_refs,
            ),
        )
    if disposition == "rejected":
        rejected = _require_scenario_fields(
            payload,
            EXPECTED_REJECTED_FIELDS,
            "expected_rejected_step",
        )
        if (
            type(rejected["rejection_code"]) is not str
            or rejected["rejection_code"] not in SCENARIO_REJECTION_CODES
            or rejected["prior_state_bytes_unchanged"] is not True
        ):
            raise PhaseCContractError("expected_rejection")
        return PhaseCExpectedRejectedStepV1(
            disposition="rejected",
            rejection_code=rejected["rejection_code"],
            prior_state_bytes_unchanged=True,
        )
    raise PhaseCContractError("expected_step_disposition")


def validate_phase_c_scenario_payload(
    payload: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[PhaseCScenarioV1, ...]:
    validate_phase_c_policy(policy)
    root = _require_scenario_fields(
        payload,
        SCENARIO_MATRIX_FIELDS,
        "scenario_matrix",
    )
    if root["schema_version"] != "PhaseCScenarioMatrixV1":
        raise PhaseCContractError("scenario_matrix_schema")
    if root["policy_id"] != "emotion-state-phase-c0-synthetic-v1":
        raise PhaseCContractError("scenario_matrix_policy")
    if type(root["scenarios"]) is not list:
        raise PhaseCContractError("scenario_matrix_scenarios_type")
    _scan_forbidden_phase_c_keys({
        "sessions": [
            scenario.get("sessions")
            for scenario in root["scenarios"]
            if type(scenario) is dict
        ],
    })
    parsed: list[PhaseCScenarioV1] = []
    case_ids: list[str] = []
    for raw_scenario in root["scenarios"]:
        scenario = _require_scenario_fields(
            raw_scenario,
            SCENARIO_FIELDS,
            "scenario",
        )
        if any(
            type(scenario[field]) is not str
            for field in ("case_id", "family", "signal_family", "modality_family")
        ):
            raise PhaseCContractError("scenario_scalar_type")
        case_id = scenario["case_id"]
        case_ids.append(case_id)
        expected_classification = EXPECTED_SCENARIO_CLASSIFICATIONS.get(case_id)
        if expected_classification is None or (
            scenario["family"],
            scenario["signal_family"],
            scenario["modality_family"],
        ) != expected_classification:
            raise PhaseCContractError("scenario_classification")
        if type(scenario["sessions"]) is not list:
            raise PhaseCContractError("scenario_sessions_type")
        raw_aliases: list[str] = []
        sessions: list[PhaseCScenarioSessionV1] = []
        for raw_session in scenario["sessions"]:
            session = _require_scenario_fields(
                raw_session,
                SCENARIO_SESSION_FIELDS,
                "scenario_session",
            )
            if (
                type(session["session_alias"]) is not str
                or type(session["frames"]) is not list
            ):
                raise PhaseCContractError("scenario_session_type")
            alias = session["session_alias"]
            raw_aliases.append(alias)
            sessions.append(PhaseCScenarioSessionV1(
                session_alias=alias,
                frames=tuple(
                    parse_phase_c_frame(frame, policy)
                    for frame in session["frames"]
                ),
            ))
        aliases = tuple(raw_aliases)
        if aliases not in (("A",), ("A", "B")) or len(set(aliases)) != len(aliases):
            raise PhaseCContractError("scenario_session_aliases")
        known_independence_keys = tuple(
            atom.independence_key
            for session in sessions
            for frame in session.frames
            for atom in frame.evidence_atoms
        )
        known_evidence_refs = tuple(
            atom.evidence_ref
            for session in sessions
            for frame in session.frames
            for atom in frame.evidence_atoms
        )
        if type(scenario["attempt_order"]) is not list:
            raise PhaseCContractError("scenario_attempts_type")
        attempts: list[PhaseCScenarioAttemptV1] = []
        for raw_attempt in scenario["attempt_order"]:
            attempt = _require_scenario_fields(
                raw_attempt,
                SCENARIO_ATTEMPT_FIELDS,
                "scenario_attempt",
            )
            if (
                type(attempt["state_session_alias"]) is not str
                or type(attempt["frame_session_alias"]) is not str
                or type(attempt["frame_index"]) is not int
                or type(attempt["mutation_kind"]) is not str
                or (
                    attempt["mutation_parameter"] is not None
                    and type(attempt["mutation_parameter"]) is not str
                )
            ):
                raise PhaseCContractError("scenario_attempt_type")
            state_alias = attempt["state_session_alias"]
            frame_alias = attempt["frame_session_alias"]
            if state_alias not in aliases or frame_alias not in aliases:
                raise PhaseCContractError("scenario_attempt_alias")
            source = sessions[aliases.index(frame_alias)]
            frame_index = attempt["frame_index"]
            if frame_index < 0 or frame_index >= len(source.frames):
                raise PhaseCContractError("scenario_attempt_frame_index")
            kind = attempt["mutation_kind"]
            parameter = attempt["mutation_parameter"]
            if kind not in ALLOWED_SCENARIO_MUTATIONS:
                raise PhaseCContractError("scenario_attempt_mutation")
            if kind in ("none", "reverse_atom_order") and parameter is not None:
                raise PhaseCContractError("scenario_attempt_mutation_parameter")
            if kind == "reverse_atom_order" and len(source.frames[frame_index].evidence_atoms) < 2:
                raise PhaseCContractError("scenario_attempt_reverse_size")
            if kind == "add_forbidden_field" and (
                parameter not in SCENARIO_FORBIDDEN_FIELD_MUTATIONS
            ):
                raise PhaseCContractError("scenario_attempt_mutation_parameter")
            attempts.append(PhaseCScenarioAttemptV1(
                state_session_alias=state_alias,
                frame_session_alias=frame_alias,
                frame_index=frame_index,
                mutation_kind=kind,
                mutation_parameter=parameter,
            ))
        if type(scenario["expected_steps"]) is not list:
            raise PhaseCContractError("scenario_expected_steps_type")
        raw_expected_steps = scenario["expected_steps"]
        if len(raw_expected_steps) != len(attempts):
            raise PhaseCContractError("scenario_expected_step_count")
        authority = _scenario_step_authority(case_id)
        actual_attempt_authority = tuple(
            (
                attempt.state_session_alias,
                attempt.frame_session_alias,
                attempt.frame_index,
                attempt.mutation_kind,
                attempt.mutation_parameter,
            )
            for attempt in attempts
        )
        expected_attempt_authority = tuple(step[:5] for step in authority)
        if actual_attempt_authority != expected_attempt_authority:
            raise PhaseCContractError("scenario_attempt_authority")
        actual_dispositions = tuple(
            expected.get("disposition")
            if type(expected) is dict
            else None
            for expected in raw_expected_steps
        )
        expected_dispositions = tuple(step[5] for step in authority)
        if actual_dispositions != expected_dispositions:
            raise PhaseCContractError("scenario_disposition_authority")
        actual_rejections = tuple(
            expected.get("rejection_code")
            if (
                type(expected) is dict
                and expected.get("disposition") == "rejected"
            )
            else None
            for expected in raw_expected_steps
        )
        expected_rejections = tuple(step[6] for step in authority)
        if actual_rejections != expected_rejections:
            raise PhaseCContractError("scenario_rejection_authority")
        expected_steps = tuple(
            _parse_expected_step(
                step,
                policy,
                known_independence_keys,
                known_evidence_refs,
            )
            for step in raw_expected_steps
        )
        for attempt, expected in zip(attempts, expected_steps, strict=True):
            if attempt.mutation_kind == "reverse_atom_order" and (
                type(expected) is not PhaseCExpectedRejectedStepV1
                or expected.rejection_code != "noncanonical_atom_order"
            ):
                raise PhaseCContractError("scenario_reverse_expectation")
            if attempt.mutation_kind == "add_forbidden_field" and (
                type(expected) is not PhaseCExpectedRejectedStepV1
                or expected.rejection_code != "forbidden_field"
            ):
                raise PhaseCContractError("scenario_forbidden_expectation")
        parsed.append(PhaseCScenarioV1(
            case_id=case_id,
            family=scenario["family"],
            signal_family=scenario["signal_family"],
            modality_family=scenario["modality_family"],
            sessions=tuple(sessions),
            attempt_order=tuple(attempts),
            expected_steps=expected_steps,
        ))
    if tuple(case_ids) != EXPECTED_SCENARIO_IDS or len(set(case_ids)) != len(case_ids):
        raise PhaseCContractError("scenario_ids")
    if scenario_payload_sha256(payload) != FROZEN_SCENARIO_CANONICAL_SHA256:
        raise PhaseCContractError("scenario_authority_digest")
    return tuple(parsed)


def load_and_validate_phase_c_scenarios(
    path: Path,
    policy: dict[str, Any],
) -> tuple[PhaseCScenarioV1, ...]:
    payload = load_json_strict(path)
    before = scenario_payload_sha256(payload)
    scenarios = validate_phase_c_scenario_payload(payload, policy)
    if scenario_payload_sha256(payload) != before:
        raise PhaseCContractError("scenario_payload_mutated")
    return scenarios


def _scenario_step_authority(
    case_id: str,
) -> tuple[tuple[Any, ...], ...]:
    authority = next(
        (
            steps
            for authority_case_id, steps in EXPECTED_SCENARIO_STEP_AUTHORITY
            if authority_case_id == case_id
        ),
        None,
    )
    if authority is None:
        raise PhaseCContractError("scenario_ids")
    return authority


def _validate_scenario_attempt_dataclass(
    attempt: PhaseCScenarioAttemptV1,
    sessions: tuple[PhaseCScenarioSessionV1, ...],
    aliases: tuple[str, ...],
) -> None:
    if type(attempt) is not PhaseCScenarioAttemptV1:
        raise PhaseCContractError("scenario_attempt_type")
    if (
        type(attempt.state_session_alias) is not str
        or type(attempt.frame_session_alias) is not str
        or type(attempt.frame_index) is not int
        or type(attempt.mutation_kind) is not str
        or (
            attempt.mutation_parameter is not None
            and type(attempt.mutation_parameter) is not str
        )
    ):
        raise PhaseCContractError("scenario_attempt_type")
    if (
        attempt.state_session_alias not in aliases
        or attempt.frame_session_alias not in aliases
    ):
        raise PhaseCContractError("scenario_attempt_alias")
    source = sessions[aliases.index(attempt.frame_session_alias)]
    if attempt.frame_index < 0 or attempt.frame_index >= len(source.frames):
        raise PhaseCContractError("scenario_attempt_frame_index")
    if attempt.mutation_kind not in ALLOWED_SCENARIO_MUTATIONS:
        raise PhaseCContractError("scenario_attempt_mutation")
    if (
        attempt.mutation_kind in ("none", "reverse_atom_order")
        and attempt.mutation_parameter is not None
    ):
        raise PhaseCContractError("scenario_attempt_mutation_parameter")
    if (
        attempt.mutation_kind == "reverse_atom_order"
        and len(source.frames[attempt.frame_index].evidence_atoms) < 2
    ):
        raise PhaseCContractError("scenario_attempt_reverse_size")
    if (
        attempt.mutation_kind == "add_forbidden_field"
        and attempt.mutation_parameter not in SCENARIO_FORBIDDEN_FIELD_MUTATIONS
    ):
        raise PhaseCContractError("scenario_attempt_mutation_parameter")


def _expected_internal_to_payload(
    internal: PhaseCExpectedInternalProjectionV1,
) -> dict[str, Any]:
    if type(internal) is not PhaseCExpectedInternalProjectionV1:
        raise PhaseCContractError("expected_internal_not_object")
    return {
        "gross_supporting_units": dict(internal.gross_supporting_units),
        "gross_opposing_units": dict(internal.gross_opposing_units),
        "uncapped_net_support": dict(internal.uncapped_net_support),
        "capped_net_support": dict(internal.capped_net_support),
        "contradictory_signals": list(internal.contradictory_signals),
        "seen_independence_keys": list(internal.seen_independence_keys),
        "internal_incumbent": internal.internal_incumbent,
        "incumbent_tenure": internal.incumbent_tenure,
        "entry_confirmation_keys_by_signal": {
            signal: list(keys)
            for signal, keys in internal.entry_confirmation_keys_by_signal
        },
        "switch_challenger": internal.switch_challenger,
        "switch_confirmation_keys": list(internal.switch_confirmation_keys),
        "release_streak": internal.release_streak,
        "contributing_evidence_refs": list(internal.contributing_evidence_refs),
        "seen_evidence_refs": list(internal.seen_evidence_refs),
        "retired_independence_keys": list(internal.retired_independence_keys),
        "accepted_turn_count": internal.accepted_turn_count,
        "last_emitted_selected_signal": internal.last_emitted_selected_signal,
        "last_emitted_selected_support": internal.last_emitted_selected_support,
    }


def _expected_step_dataclass_to_payload(
    expected: PhaseCExpectedAcceptedStepV1 | PhaseCExpectedRejectedStepV1,
) -> dict[str, Any]:
    if type(expected) is PhaseCExpectedRejectedStepV1:
        return {
            "disposition": expected.disposition,
            "rejection_code": expected.rejection_code,
            "prior_state_bytes_unchanged": expected.prior_state_bytes_unchanged,
        }
    if type(expected) is not PhaseCExpectedAcceptedStepV1:
        raise PhaseCContractError("expected_step_disposition")
    if type(expected.expected_output_bytes) is not bytes:
        raise PhaseCContractError("expected_output_contract")
    try:
        output = json.loads(
            expected.expected_output_bytes.decode("utf-8"),
            parse_constant=_reject_constant,
            parse_float=_parse_finite_float,
            object_pairs_hook=_unique_object,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PhaseCContractError("expected_output_contract") from exc
    if (
        type(output) is not dict
        or canonical_json_bytes(output) != expected.expected_output_bytes
    ):
        raise PhaseCContractError("expected_output_contract")
    return {
        "disposition": expected.disposition,
        "expected_output": output,
        "expected_internal": _expected_internal_to_payload(
            expected.expected_internal,
        ),
    }


def _phase_c_scenario_dataclass_to_payload(
    scenario: PhaseCScenarioV1,
) -> dict[str, Any]:
    return {
        "case_id": scenario.case_id,
        "family": scenario.family,
        "signal_family": scenario.signal_family,
        "modality_family": scenario.modality_family,
        "sessions": [
            {
                "session_alias": session.session_alias,
                "frames": [
                    phase_c_frame_to_payload(frame)
                    for frame in session.frames
                ],
            }
            for session in scenario.sessions
        ],
        "attempt_order": [
            {
                "state_session_alias": attempt.state_session_alias,
                "frame_session_alias": attempt.frame_session_alias,
                "frame_index": attempt.frame_index,
                "mutation_kind": attempt.mutation_kind,
                "mutation_parameter": attempt.mutation_parameter,
            }
            for attempt in scenario.attempt_order
        ],
        "expected_steps": [
            _expected_step_dataclass_to_payload(expected)
            for expected in scenario.expected_steps
        ],
    }


def _validate_phase_c_scenario_dataclass(
    scenario: PhaseCScenarioV1,
    policy: dict[str, Any],
) -> tuple[str, ...]:
    if type(scenario) is not PhaseCScenarioV1:
        raise PhaseCContractError("scenario_type")
    expected_classification = EXPECTED_SCENARIO_CLASSIFICATIONS.get(
        scenario.case_id,
    )
    if expected_classification is None or (
        scenario.family,
        scenario.signal_family,
        scenario.modality_family,
    ) != expected_classification:
        raise PhaseCContractError("scenario_classification")
    if type(scenario.sessions) is not tuple or any(
        type(session) is not PhaseCScenarioSessionV1
        for session in scenario.sessions
    ):
        raise PhaseCContractError("scenario_session_type")
    aliases = tuple(session.session_alias for session in scenario.sessions)
    if aliases not in (("A",), ("A", "B")) or len(set(aliases)) != len(aliases):
        raise PhaseCContractError("scenario_session_aliases")
    for session in scenario.sessions:
        if (
            type(session.session_alias) is not str
            or type(session.frames) is not tuple
        ):
            raise PhaseCContractError("scenario_session_type")
        for frame in session.frames:
            validate_phase_c_frame(frame, policy)
            if frame.call_session_id != (
                f"session:{scenario.case_id}:{session.session_alias}"
            ):
                raise PhaseCContractError("scenario_frame_identity")
    if (
        type(scenario.attempt_order) is not tuple
        or type(scenario.expected_steps) is not tuple
    ):
        raise PhaseCContractError("scenario_attempt_type")
    if len(scenario.attempt_order) != len(scenario.expected_steps):
        raise PhaseCContractError("scenario_expected_step_count")
    for attempt in scenario.attempt_order:
        _validate_scenario_attempt_dataclass(
            attempt,
            scenario.sessions,
            aliases,
        )
    known_independence_keys = tuple(
        atom.independence_key
        for session in scenario.sessions
        for frame in session.frames
        for atom in frame.evidence_atoms
    )
    known_evidence_refs = tuple(
        atom.evidence_ref
        for session in scenario.sessions
        for frame in session.frames
        for atom in frame.evidence_atoms
    )
    authority = _scenario_step_authority(scenario.case_id)
    actual_attempt_authority = tuple(
        (
            attempt.state_session_alias,
            attempt.frame_session_alias,
            attempt.frame_index,
            attempt.mutation_kind,
            attempt.mutation_parameter,
        )
        for attempt in scenario.attempt_order
    )
    if actual_attempt_authority != tuple(step[:5] for step in authority):
        raise PhaseCContractError("scenario_attempt_authority")
    if tuple(
        step.disposition
        if type(step) in (
            PhaseCExpectedAcceptedStepV1,
            PhaseCExpectedRejectedStepV1,
        )
        else None
        for step in scenario.expected_steps
    ) != tuple(
        step[5] for step in authority
    ):
        raise PhaseCContractError("scenario_disposition_authority")
    if tuple(
        step.rejection_code
        if type(step) is PhaseCExpectedRejectedStepV1
        else None
        for step in scenario.expected_steps
    ) != tuple(step[6] for step in authority):
        raise PhaseCContractError("scenario_rejection_authority")
    for expected in scenario.expected_steps:
        _parse_expected_step(
            _expected_step_dataclass_to_payload(expected),
            policy,
            known_independence_keys,
            known_evidence_refs,
        )
    expected_digest = next(
        (
            digest
            for case_id, digest in EXPECTED_SCENARIO_CANONICAL_SHA256_BY_CASE
            if case_id == scenario.case_id
        ),
        None,
    )
    if (
        expected_digest is None
        or sha256_bytes(canonical_json_bytes(
            _phase_c_scenario_dataclass_to_payload(scenario),
        )) != expected_digest
    ):
        raise PhaseCContractError("scenario_dataclass_authority_digest")
    return aliases


def materialize_phase_c_scenario_attempt_payload(
    scenario: PhaseCScenarioV1,
    attempt: PhaseCScenarioAttemptV1,
) -> dict[str, Any]:
    policy = _frozen_phase_c_policy()
    aliases = _validate_phase_c_scenario_dataclass(scenario, policy)
    _validate_scenario_attempt_dataclass(
        attempt,
        scenario.sessions,
        aliases,
    )
    if scenario.attempt_order.count(attempt) != 1:
        raise PhaseCContractError("scenario_attempt_membership")
    sessions = {session.session_alias: session for session in scenario.sessions}
    source = sessions[attempt.frame_session_alias]
    payload = deepcopy(phase_c_frame_to_payload(source.frames[attempt.frame_index]))
    if attempt.mutation_kind == "none":
        if attempt.mutation_parameter is not None:
            raise PhaseCContractError("scenario_attempt_mutation_parameter")
        return payload
    if attempt.mutation_kind == "reverse_atom_order":
        if attempt.mutation_parameter is not None or len(payload["evidence_atoms"]) < 2:
            raise PhaseCContractError("scenario_attempt_mutation_parameter")
        payload["evidence_atoms"] = list(reversed(payload["evidence_atoms"]))
        return payload
    if (
        attempt.mutation_kind == "add_forbidden_field"
        and attempt.mutation_parameter in SCENARIO_FORBIDDEN_FIELD_MUTATIONS
    ):
        payload[attempt.mutation_parameter] = {}
        return payload
    raise PhaseCContractError("scenario_attempt_mutation")


def _validated_phase_c_event_watermark_maps(
    watermark: PhaseCEventWatermarkV1,
) -> tuple[dict[str, int], dict[int, str], dict[str, int], dict[str, tuple[str, int]]]:
    if type(watermark) is not PhaseCEventWatermarkV1:
        raise PhaseCContractError("event_watermark_type")
    for value in (
        watermark.expected_session_id,
        watermark.expected_campaign_profile_id,
        watermark.expected_campaign_profile_version,
    ):
        _require_opaque_identifier(value)
    if type(watermark.last_turn_sequence) is not int or watermark.last_turn_sequence < -1:
        raise PhaseCContractError("event_watermark_counter")
    tuple_maps = (
        watermark.turn_sequence_by_id,
        watermark.turn_id_by_sequence,
        watermark.last_input_revision_by_turn,
    )
    if (
        any(type(value) is not tuple for value in tuple_maps)
        or type(watermark.seen_event_ids) is not frozenset
        or type(watermark.event_history_by_id) is not tuple
    ):
        raise PhaseCContractError("event_watermark_collections")
    if any(type(pair) is not tuple or len(pair) != 2 for pairs in tuple_maps for pair in pairs):
        raise PhaseCContractError("event_watermark_entries")
    if any(type(entry) is not tuple or len(entry) != 3 for entry in watermark.event_history_by_id):
        raise PhaseCContractError("event_watermark_history")
    for turn_id, sequence in watermark.turn_sequence_by_id:
        _require_opaque_identifier(turn_id)
        if type(sequence) is not int or sequence < 0:
            raise PhaseCContractError("event_watermark_sequence")
    for sequence, turn_id in watermark.turn_id_by_sequence:
        if type(sequence) is not int or sequence < 0:
            raise PhaseCContractError("event_watermark_sequence")
        _require_opaque_identifier(turn_id)
    for turn_id, revision in watermark.last_input_revision_by_turn:
        _require_opaque_identifier(turn_id)
        if type(revision) is not int or revision < 0:
            raise PhaseCContractError("event_watermark_revision")
    sequence_by_id = dict(watermark.turn_sequence_by_id)
    id_by_sequence = dict(watermark.turn_id_by_sequence)
    revision_by_turn = dict(watermark.last_input_revision_by_turn)
    if any(len(mapping) != len(source) for mapping, source in (
        (sequence_by_id, watermark.turn_sequence_by_id),
        (id_by_sequence, watermark.turn_id_by_sequence),
        (revision_by_turn, watermark.last_input_revision_by_turn),
    )):
        raise PhaseCContractError("event_watermark_duplicate_map_key")
    for event_id in watermark.seen_event_ids:
        _require_opaque_identifier(event_id)
    history_by_id: dict[str, tuple[str, int]] = {}
    seen_turn_revisions: set[tuple[str, int]] = set()
    revisions_by_turn: dict[str, list[int]] = {}
    for event_id, turn_id, revision in watermark.event_history_by_id:
        _require_opaque_identifier(event_id)
        _require_opaque_identifier(turn_id)
        if type(revision) is not int or revision < 0:
            raise PhaseCContractError("event_watermark_revision")
        if event_id in history_by_id or (turn_id, revision) in seen_turn_revisions:
            raise PhaseCContractError("event_watermark_duplicate_history")
        history_by_id[event_id] = (turn_id, revision)
        seen_turn_revisions.add((turn_id, revision))
        revisions_by_turn.setdefault(turn_id, []).append(revision)
    if (
        len(sequence_by_id) != len(id_by_sequence)
        or len(set(sequence_by_id.values())) != len(sequence_by_id)
        or len(set(id_by_sequence.values())) != len(id_by_sequence)
        or {sequence: turn_id for turn_id, sequence in sequence_by_id.items()} != id_by_sequence
    ):
        raise PhaseCContractError("event_watermark_turn_map_inverse")
    if set(revision_by_turn) != set(sequence_by_id) or set(revisions_by_turn) != set(sequence_by_id):
        raise PhaseCContractError("event_watermark_coverage")
    if frozenset(history_by_id) != watermark.seen_event_ids:
        raise PhaseCContractError("event_watermark_event_history")
    for turn_id, last_revision in revision_by_turn.items():
        revisions = sorted(revisions_by_turn[turn_id])
        if revisions != list(range(last_revision + 1)):
            raise PhaseCContractError("event_watermark_revision_history")
    if watermark.last_turn_sequence != max(id_by_sequence, default=-1):
        raise PhaseCContractError("event_watermark_last_turn")
    return sequence_by_id, id_by_sequence, revision_by_turn, history_by_id


def validate_phase_c_event_watermark(
    watermark: PhaseCEventWatermarkV1,
) -> tuple[dict[str, int], dict[int, str], dict[str, int], dict[str, tuple[str, int]]]:
    return _validated_phase_c_event_watermark_maps(watermark)


def initial_phase_c_watermark(frame: PhaseCSyntheticEvidenceFrameV1) -> PhaseCEventWatermarkV1:
    validate_phase_c_frame(frame, _frozen_phase_c_policy())
    return PhaseCEventWatermarkV1(
        expected_session_id=frame.call_session_id,
        expected_campaign_profile_id=frame.campaign_profile_id,
        expected_campaign_profile_version=frame.campaign_profile_version,
        last_turn_sequence=-1,
        turn_sequence_by_id=(),
        turn_id_by_sequence=(),
        last_input_revision_by_turn=(),
        seen_event_ids=frozenset(),
        event_history_by_id=(),
    )


def validate_phase_c_event_identity(
    frame: PhaseCSyntheticEvidenceFrameV1,
    watermark: PhaseCEventWatermarkV1,
) -> PhaseCEventWatermarkV1:
    sequence_by_id, id_by_sequence, revision_by_turn, history_by_id = (
        validate_phase_c_event_watermark(watermark)
    )
    validate_phase_c_frame(frame, _frozen_phase_c_policy())

    def reject(code: str) -> None:
        raise PhaseCEventRejected(code)

    if frame.call_session_id != watermark.expected_session_id:
        reject("cross_session")
    if frame.campaign_profile_id != watermark.expected_campaign_profile_id:
        reject("cross_campaign")
    if frame.campaign_profile_version != watermark.expected_campaign_profile_version:
        reject("wrong_campaign_version")
    if frame.event_id in watermark.seen_event_ids:
        reject("duplicate_event")
    if frame.turn_id in sequence_by_id and sequence_by_id[frame.turn_id] != frame.turn_sequence:
        reject("turn_id_rebound")
    if frame.turn_sequence in id_by_sequence and id_by_sequence[frame.turn_sequence] != frame.turn_id:
        reject("turn_sequence_rebound")
    if frame.turn_sequence < watermark.last_turn_sequence:
        reject("stale_turn")
    if frame.turn_id in sequence_by_id:
        if frame.input_revision != revision_by_turn[frame.turn_id] + 1:
            reject("invalid_revision")
    else:
        if frame.turn_sequence <= watermark.last_turn_sequence:
            reject("stale_turn")
        if frame.input_revision != 0:
            reject("invalid_revision")
        sequence_by_id[frame.turn_id] = frame.turn_sequence
        id_by_sequence[frame.turn_sequence] = frame.turn_id
    revision_by_turn[frame.turn_id] = frame.input_revision
    history_by_id[frame.event_id] = (frame.turn_id, frame.input_revision)
    return PhaseCEventWatermarkV1(
        expected_session_id=watermark.expected_session_id,
        expected_campaign_profile_id=watermark.expected_campaign_profile_id,
        expected_campaign_profile_version=watermark.expected_campaign_profile_version,
        last_turn_sequence=max(watermark.last_turn_sequence, frame.turn_sequence),
        turn_sequence_by_id=tuple(sorted(sequence_by_id.items())),
        turn_id_by_sequence=tuple(sorted(id_by_sequence.items())),
        last_input_revision_by_turn=tuple(sorted(revision_by_turn.items())),
        seen_event_ids=frozenset(history_by_id),
        event_history_by_id=tuple(sorted(
            (event_id, turn_id, revision)
            for event_id, (turn_id, revision) in history_by_id.items()
        )),
    )
