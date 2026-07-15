from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceProvenanceTests(unittest.TestCase):
    def test_private_source_pin_is_exact_and_non_adapting(self) -> None:
        path = ROOT / "research/sources/creative_analysis_engine/source_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["source_repository_url"],
            "https://github.com/WisdomBreathes/creative-analysis-engine",
        )
        self.assertEqual(manifest["source_repository_url_status"], "verified_read_only")
        self.assertEqual(manifest["source_branch"], "dev")
        self.assertEqual(
            manifest["source_revision"],
            "7cb99ea2da3016cd82d0b5f805c015a808ce4e0d",
        )
        self.assertEqual(manifest["source_revision_status"], "verified_read_only")
        self.assertEqual(manifest["observed_license_status"], "absent_in_reviewed_root")
        self.assertEqual(len(manifest["reviewed_files"]), 7)
        self.assertEqual(manifest["copied_material"], [])
        self.assertEqual(manifest["translated_material"], [])
        self.assertEqual(manifest["adapted_material"], [])
        self.assertEqual(manifest["independently_reimplemented_material"], [])
        self.assertFalse(manifest["adaptation_allowed"])
        self.assertFalse(manifest["phase_b_approval"]["approved"])
        self.assertFalse(manifest["runtime_dependency_added"])
