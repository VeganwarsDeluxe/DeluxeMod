"""Headless Match: AndroidV2 vs a chosen opponent. Not listed in content.all_matches."""

from __future__ import annotations

# True  → mirrored FIXED_* / LOADOUT_PROFILES (fair profile tests)
# False → Android / AndroidV2 keep random __init__ gear (universality check)
USE_FIXED_LOADOUT = False

from VegansDeluxe import rebuild

import DeluxeMod.content
from DeluxeMod.Entities.Android import Android
from DeluxeMod.Entities.AndroidV2 import AndroidV2
from DeluxeMod.Entities.Beast import Beast
from DeluxeMod.Entities.Elemental import Elemental
from DeluxeMod.Entities.Slime import Slime
from DeluxeMod.Matches.BasicMatch import BasicMatch
from DeluxeMod.Skills.Dash import Dash


OPPONENT_TEAMS = {
    "android": "android",
    "beast": "beast",
    "slime": "slimes",
    "elemental": "elemental",
}

# Default kit (overridden per profile in multi-build sims).
FIXED_WEAPON = rebuild.Knife
FIXED_ITEMS = (rebuild.Adrenaline, rebuild.Grenade)
FIXED_SKILLS = (rebuild.Zombie, rebuild.Ninja)

# Named mirrored profiles for universality checks (weapon/items/skills by stats role).
LOADOUT_PROFILES = {
    "cheap_melee": (rebuild.Axe, (rebuild.Adrenaline, rebuild.Shield), (rebuild.Ninja, rebuild.Medic)),
    "expensive_melee": (rebuild.Molot, (rebuild.Adrenaline, rebuild.Shield), (rebuild.Sadist, rebuild.Medic)),
    "cheap_ranged": (rebuild.Pistol, (rebuild.Adrenaline, rebuild.Shield), (rebuild.Scope, rebuild.Ninja)),
    "expensive_ranged": (rebuild.Rifle, (rebuild.Adrenaline, rebuild.Shield), (rebuild.Scope, rebuild.Visor)),
    "defensive": (rebuild.Axe, (rebuild.Shield, rebuild.Stimulator), (rebuild.ShieldGen, rebuild.Ninja)),
    "aggressive": (rebuild.Pistol, (rebuild.Grenade, rebuild.Molotov), (rebuild.Scope, rebuild.Sadist)),
    "melee_dash": (rebuild.Knife, (rebuild.Adrenaline, rebuild.Shield), (Dash, rebuild.Ninja)),
    "heavy_ranged": (rebuild.Shotgun, (rebuild.Adrenaline, rebuild.Shield), (rebuild.Scope, rebuild.Medic)),
}


class AndroidSimulationMatch(BasicMatch):
    name = "AndroidV2 simulation"

    def __init__(self, match_id, engine, max_turns: int = 500):
        super().__init__(match_id, engine)
        self.max_turns = max_turns
        self.android_v2: AndroidV2 | None = None
        self.opponent = None
        self.opponent_kind: str = "android"
        self.loadout_weapon = FIXED_WEAPON
        self.loadout_items = FIXED_ITEMS
        self.loadout_skills = FIXED_SKILLS

    def set_loadout(self, weapon, items, skills) -> None:
        self.loadout_weapon = weapon
        self.loadout_items = items
        self.loadout_skills = skills

    def set_profile(self, profile: str) -> None:
        if profile not in LOADOUT_PROFILES:
            raise ValueError(f"Unknown loadout profile: {profile}")
        weapon, items, skills = LOADOUT_PROFILES[profile]
        self.set_loadout(weapon, items, skills)

    async def apply_fixed_loadout(self, npc) -> None:
        """Overwrite random __init__ loot with the current AI-test kit."""
        npc.weapon = self.loadout_weapon(npc.session_id, npc.id)
        npc.items.clear()
        npc.items.extend(item_cls() for item_cls in self.loadout_items)
        await self.engine.attach_states(npc, list(self.loadout_skills))

    async def setup_fighters(self, opponent: str = "android", profile: str | None = None):
        """Create AndroidV2 and one opponent NPC for this Match."""
        if USE_FIXED_LOADOUT and profile is not None:
            self.set_profile(profile)

        self.opponent_kind = opponent
        if opponent not in OPPONENT_TEAMS:
            raise ValueError(f"Unknown opponent: {opponent}")

        self.android_v2 = AndroidV2(self.id, name="AndroidV2")
        self.android_v2.team = "android_v2"

        if opponent == "android":
            self.opponent = Android(self.id, name="Android")
            self.opponent.team = "android"
        elif opponent == "beast":
            self.opponent = Beast(self.id, name="Beast")
            self.opponent.team = "beast"
        elif opponent == "slime":
            self.opponent = Slime(self.id, name="Slime")
            self.opponent.team = "slimes"
        elif opponent == "elemental":
            self.opponent = Elemental(self.id, name="Elemental")
            self.opponent.team = "elemental"

        for npc in (self.android_v2, self.opponent):
            self.session.attach_entity(npc)
            await self.engine.attach_states(npc, DeluxeMod.content.all_states)

        if USE_FIXED_LOADOUT:
            await self.apply_fixed_loadout(self.android_v2)
            if opponent == "android":
                await self.apply_fixed_loadout(self.opponent)
            elif opponent == "elemental":
                await self.engine.attach_states(self.opponent, self.opponent.skill_pool)
        elif opponent == "elemental":
            await self.engine.attach_states(self.opponent, self.opponent.skill_pool)

    async def check_game_status(self):
        if self.session.active and self.session.turn > self.max_turns:
            await self.session.stop()
        return await super().check_game_status()
