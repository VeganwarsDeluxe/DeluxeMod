"""
Ablation study for AndroidV2 heuristics.

Obsolete: AndroidV2 no longer exposes per-heuristic toggles. The AI keeps only
opponent-agnostic architectural fixes (threat detection, deterministic Explosion,
weapon_rank, skill_prefer, grenade_suppress, force_finish, reload_override).

Use simulate_android_v2_suite.py for multi-opponent evaluation instead.
"""

from __future__ import annotations

import sys


def main() -> None:
    print(
        "ablate_android_v2.py is obsolete: AndroidV2 no longer has heuristic toggles.\n"
        "Run: python simulate_android_v2_suite.py --fights 1000",
        file=sys.stderr,
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
