"""
Headless AndroidV2 multi-opponent suite via VegansDeluxe Match API.

Usage (from repo root):

    python simulate_android_v2_suite.py
    python simulate_android_v2_suite.py --fights 1000
    python simulate_android_v2_suite.py --fights 500 --opponents android,beast,slime,elemental
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
from DeluxeMod.Entities.Beast import Beast  # noqa: F401
from DeluxeMod.Entities.Elemental import Elemental  # noqa: F401
from DeluxeMod.Entities.Slime import Slime  # noqa: F401
from DeluxeMod.Matches.AndroidSimulationMatch import AndroidSimulationMatch, OPPONENT_TEAMS
from VegansDeluxe.core import Engine


async def run_one_fight(engine: Engine, opponent: str, max_turns: int) -> tuple[str, int]:
    """
    Returns:
        (winner, turns) where winner is "android_v2" | "opponent" | "draw" | "error"
    """
    match = AndroidSimulationMatch(str(uuid.uuid4()), engine, max_turns=max_turns)
    await match.init_async()
    await match.setup_fighters(opponent=opponent)
    try:
        await match.start_game()
    except Exception:
        turns = max(getattr(match.session, "turn", 1) - 1, 0)
        return "error", turns

    turns = max(match.session.turn - 1, 0)
    alive = list(match.session.alive_entities)
    opponent_team = OPPONENT_TEAMS[opponent]

    if not alive:
        return "draw", turns

    alive_teams = {e.team for e in alive}
    if alive_teams == {"android_v2"}:
        return "android_v2", turns
    if alive_teams == {opponent_team}:
        return "opponent", turns
    return "draw", turns


async def run_series(engine: Engine, opponent: str, fights: int, max_turns: int, progress_every: int) -> dict:
    v2_wins = 0
    opp_wins = 0
    draws = 0
    errors = 0
    total_turns = 0
    started = time.perf_counter()

    for i in range(1, fights + 1):
        winner, turns = await run_one_fight(engine, opponent, max_turns=max_turns)
        total_turns += turns
        if winner == "android_v2":
            v2_wins += 1
        elif winner == "opponent":
            opp_wins += 1
        elif winner == "error":
            errors += 1
        else:
            draws += 1

        if progress_every and i % progress_every == 0:
            elapsed = time.perf_counter() - started
            print(
                f"  [{opponent}] {i}/{fights} "
                f"V2={v2_wins} Opp={opp_wins} Draw={draws} Err={errors} "
                f"({elapsed:.1f}s)"
            )

    return {
        "opponent": opponent,
        "fights": fights,
        "v2_wins": v2_wins,
        "opp_wins": opp_wins,
        "draws": draws,
        "errors": errors,
        "avg_turns": total_turns / fights if fights else 0.0,
        "seconds": time.perf_counter() - started,
    }


def pct(n: int, total: int) -> float:
    return 100.0 * n / total if total else 0.0


async def main_async(fights: int, max_turns: int, progress_every: int, opponents: list[str]) -> None:
    engine = Engine()
    results = []

    print(f"AndroidV2 suite: {fights} fights each vs {', '.join(opponents)}")
    print(f"max_turns={max_turns}\n")

    for opponent in opponents:
        print(f"=== vs {opponent} ===")
        result = await run_series(engine, opponent, fights, max_turns, progress_every)
        results.append(result)
        print(
            f"  V2 {result['v2_wins']} ({pct(result['v2_wins'], fights):.1f}%) | "
            f"Opp {result['opp_wins']} ({pct(result['opp_wins'], fights):.1f}%) | "
            f"Draw {result['draws']} ({pct(result['draws'], fights):.1f}%) | "
            f"Err {result['errors']} ({pct(result['errors'], fights):.1f}%) | "
            f"avg turns {result['avg_turns']:.1f} | {result['seconds']:.1f}s\n"
        )

    print("=== SUMMARY ===")
    for r in results:
        print(
            f"V2 vs {r['opponent']:<10} "
            f"V2={pct(r['v2_wins'], r['fights']):5.1f}%  "
            f"Opp={pct(r['opp_wins'], r['fights']):5.1f}%  "
            f"Draw={pct(r['draws'], r['fights']):5.1f}%  "
            f"Err={pct(r['errors'], r['fights']):5.1f}%  "
            f"avg_turns={r['avg_turns']:.1f}"
        )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AndroidV2 multi-opponent simulation suite")
    p.add_argument("--fights", type=int, default=1000, help="Fights per opponent")
    p.add_argument("--max-turns", type=int, default=500)
    p.add_argument("--progress", type=int, default=200)
    p.add_argument(
        "--opponents",
        type=str,
        default="android,beast,slime,elemental",
        help="Comma-separated: android,beast,slime,elemental",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    opponents = [o.strip().lower() for o in args.opponents.split(",") if o.strip()]
    unknown = [o for o in opponents if o not in OPPONENT_TEAMS]
    if unknown:
        raise SystemExit(f"Unknown opponents: {unknown}. Allowed: {list(OPPONENT_TEAMS)}")
    asyncio.run(main_async(args.fights, args.max_turns, args.progress, opponents))


if __name__ == "__main__":
    main()
