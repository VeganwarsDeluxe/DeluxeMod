"""
Mirror Android vs AndroidV2 across several loadout profiles.

Usage:
    python simulate_android_profiles.py
    python simulate_android_profiles.py --fights 2000
    python simulate_android_profiles.py --profiles cheap_melee,expensive_ranged
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
import uuid
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import DeluxeMod  # noqa: F401
import DeluxeMod.content  # noqa: F401
from DeluxeMod.Entities.Android import Android  # noqa: F401
from DeluxeMod.Entities.AndroidV2 import AndroidV2  # noqa: F401
from DeluxeMod.Matches.AndroidSimulationMatch import AndroidSimulationMatch, LOADOUT_PROFILES
from VegansDeluxe.core import Engine


async def run_one(engine: Engine, profile: str, max_turns: int) -> tuple[str, int]:
    match = AndroidSimulationMatch(str(uuid.uuid4()), engine, max_turns=max_turns)
    await match.init_async()
    await match.setup_fighters(opponent="android", profile=profile)
    try:
        await match.start_game()
    except Exception:
        turns = max(getattr(match.session, "turn", 1) - 1, 0)
        return "error", turns

    turns = max(match.session.turn - 1, 0)
    alive = list(match.session.alive_entities)
    if len(alive) == 1:
        e = alive[0]
        if isinstance(e, AndroidV2) or e.team == "android_v2":
            return "android_v2", turns
        if isinstance(e, Android) or e.team == "android":
            return "android", turns
    return "draw", turns


async def run_profile(engine: Engine, profile: str, fights: int, max_turns: int, progress: int) -> dict:
    a = v2 = draws = errors = 0
    total_turns = 0
    started = time.perf_counter()
    for i in range(1, fights + 1):
        winner, turns = await run_one(engine, profile, max_turns)
        total_turns += turns
        if winner == "android":
            a += 1
        elif winner == "android_v2":
            v2 += 1
        elif winner == "error":
            errors += 1
        else:
            draws += 1
        if progress and i % progress == 0:
            print(
                f"  [{profile}] {i}/{fights} "
                f"A={a} V2={v2} D={draws} E={errors} "
                f"({time.perf_counter() - started:.1f}s)",
                flush=True,
            )
    return {
        "profile": profile,
        "fights": fights,
        "android": a,
        "android_v2": v2,
        "draws": draws,
        "errors": errors,
        "avg_turns": total_turns / fights if fights else 0.0,
        "seconds": time.perf_counter() - started,
    }


def pct(n: int, total: int) -> float:
    return 100.0 * n / total if total else 0.0


async def main_async(fights: int, max_turns: int, progress: int, profiles: list[str]) -> None:
    engine = Engine()
    print(f"Multi-profile mirror: {fights} fights each")
    print(f"profiles={', '.join(profiles)} max_turns={max_turns}\n")

    results = []
    for profile in profiles:
        print(f"=== {profile} ===")
        r = await run_profile(engine, profile, fights, max_turns, progress)
        results.append(r)
        print(
            f"  V2 {r['android_v2']} ({pct(r['android_v2'], fights):.1f}%) | "
            f"A {r['android']} ({pct(r['android'], fights):.1f}%) | "
            f"D {r['draws']} ({pct(r['draws'], fights):.1f}%) | "
            f"avg turns {r['avg_turns']:.1f} | {r['seconds']:.1f}s\n"
        )

    print("=== SUMMARY (V2 win% / Android win% / Draw%) ===")
    for r in results:
        f = r["fights"]
        print(
            f"{r['profile']:<18} "
            f"V2={pct(r['android_v2'], f):5.1f}%  "
            f"A={pct(r['android'], f):5.1f}%  "
            f"D={pct(r['draws'], f):5.1f}%  "
            f"avg_turns={r['avg_turns']:.1f}"
        )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Android vs AndroidV2 multi-loadout profiles")
    p.add_argument("--fights", type=int, default=2000)
    p.add_argument("--max-turns", type=int, default=200)
    p.add_argument("--progress", type=int, default=500)
    p.add_argument(
        "--profiles",
        type=str,
        default=",".join(LOADOUT_PROFILES.keys()),
        help=f"Comma-separated. Available: {','.join(LOADOUT_PROFILES)}",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    profiles = [x.strip() for x in args.profiles.split(",") if x.strip()]
    unknown = [p for p in profiles if p not in LOADOUT_PROFILES]
    if unknown:
        raise SystemExit(f"Unknown profiles: {unknown}")
    asyncio.run(main_async(args.fights, args.max_turns, args.progress, profiles))


if __name__ == "__main__":
    main()
