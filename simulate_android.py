"""
Headless Android vs AndroidV2 battle simulation via VegansDeluxe Match API.

Usage (from repo root, with DeluxeMod on PYTHONPATH / installed editable):

    python simulate_android.py
    python simulate_android.py --fights 1000
    python simulate_android.py --fights 10000 --progress 500
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
import uuid
from pathlib import Path

# Allow running without installing the package.
_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Register rebuild + DeluxeMod content (weapons, skills, states, actions) before Engine.
import DeluxeMod  # noqa: F401
import DeluxeMod.content  # noqa: F401
from DeluxeMod.Entities.Android import Android  # noqa: F401 — AttachedAction
from DeluxeMod.Entities.AndroidV2 import AndroidV2  # noqa: F401 — AttachedAction
from DeluxeMod.Matches.AndroidSimulationMatch import AndroidSimulationMatch
from VegansDeluxe.core import Engine


async def run_one_fight(engine: Engine, max_turns: int) -> tuple[str, int]:
    """
    Run a single Android vs AndroidV2 fight.

    Returns:
        (winner, turns) where winner is "android" | "android_v2" | "draw"
        and turns is the number of completed turns.
    """
    match = AndroidSimulationMatch(str(uuid.uuid4()), engine, max_turns=max_turns)
    await match.init_async()
    await match.setup_fighters()
    await match.start_game()

    # After the last move session.turn is already incremented.
    turns = max(match.session.turn - 1, 0)
    alive = list(match.session.alive_entities)

    if len(alive) == 1:
        winner_entity = alive[0]
        if isinstance(winner_entity, AndroidV2):
            return "android_v2", turns
        if isinstance(winner_entity, Android):
            return "android", turns
        if winner_entity.team == "android_v2":
            return "android_v2", turns
        if winner_entity.team == "android":
            return "android", turns
        return "draw", turns

    return "draw", turns


async def run_simulation(fights: int, max_turns: int, progress_every: int) -> None:
    engine = Engine()

    android_wins = 0
    android_v2_wins = 0
    draws = 0
    total_turns = 0

    started = time.perf_counter()

    for i in range(1, fights + 1):
        winner, turns = await run_one_fight(engine, max_turns=max_turns)
        total_turns += turns

        if winner == "android":
            android_wins += 1
        elif winner == "android_v2":
            android_v2_wins += 1
        else:
            draws += 1

        if progress_every > 0 and (i % progress_every == 0 or i == fights):
            elapsed = time.perf_counter() - started
            print(
                f"[{i}/{fights}] "
                f"Android={android_wins} AndroidV2={android_v2_wins} draws={draws} "
                f"avg_turns={total_turns / i:.2f} ({elapsed:.1f}s)",
                flush=True,
            )

    elapsed = time.perf_counter() - started

    def pct(n: int) -> float:
        return (100.0 * n / fights) if fights else 0.0

    print()
    print("=== Android vs AndroidV2 ===")
    print(f"Fights:              {fights}")
    print(f"Android wins:        {android_wins} ({pct(android_wins):.2f}%)")
    print(f"AndroidV2 wins:      {android_v2_wins} ({pct(android_v2_wins):.2f}%)")
    print(f"Draws:               {draws} ({pct(draws):.2f}%)")
    print(f"Average turns/fight: {total_turns / fights:.2f}" if fights else "Average turns/fight: n/a")
    print(f"Elapsed:             {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate Android vs AndroidV2 battles.")
    parser.add_argument("--fights", type=int, default=10_000, help="Number of fights (default: 10000)")
    parser.add_argument("--max-turns", type=int, default=500, help="Force draw after this many turns")
    parser.add_argument("--progress", type=int, default=500, help="Print progress every N fights (0=off)")
    args = parser.parse_args()

    if args.fights < 1:
        parser.error("--fights must be >= 1")

    asyncio.run(run_simulation(args.fights, args.max_turns, args.progress))


if __name__ == "__main__":
    main()
