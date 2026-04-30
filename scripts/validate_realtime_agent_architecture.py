#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_DOC = ROOT / "docs" / "product" / "REALTIME_AGENT_ARCHITECTURE.md"
PRODUCT_BRIEF = ROOT / "docs" / "product" / "PRODUCT_BRIEF.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> None:
    architecture = read(ARCHITECTURE_DOC)
    product_brief = read(PRODUCT_BRIEF)
    roadmap = read(ROADMAP)

    for phrase in [
        "1-2 seconds",
        "bridge response",
        "Live Critical Path",
        "Sub-Agent Policy",
        "Background Specialist Modules",
        "Post-Call Learning Layer",
        "must not block",
    ]:
        assert phrase in architecture, f"Architecture doc missing: {phrase}"

    assert "REALTIME_AGENT_ARCHITECTURE.md" in product_brief, "Product brief should link runtime architecture"
    assert "1-2 second" in product_brief, "Product brief should mention live latency target"
    assert "real-time sales-agent core" in roadmap, "Roadmap should mention real-time core"
    assert "background compliance" in roadmap, "Roadmap should keep sub-agents/background modules out of live path"


if __name__ == "__main__":
    main()
