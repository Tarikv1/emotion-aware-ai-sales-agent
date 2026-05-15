#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.entrypoints.generate_runtime_voice_delivery import *  # noqa: F401,F403


if __name__ == "__main__":
    from runtime.entrypoints.generate_runtime_voice_delivery import main

    main()
