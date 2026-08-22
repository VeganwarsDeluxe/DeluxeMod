import atexit
import os
import random
from collections import Counter
from dataclasses import dataclass

from VegansDeluxe import rebuild
from VegansDeluxe.core import AttachedAction, Session, ls, percentage_chance, Action, Enemies, Distance, ActionTag
from VegansDeluxe.core import RegisterEvent, EventContext, PreDeathGameEvent
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Entities import Entity
from VegansDeluxe.matchmakery.Entities.NPC import NPC
from VegansDeluxe.rebuild import Bleeding, ZombieState, Stun, DroppedWeapon, ThrowingKnife, Berserk, \
    Knockdown, Grenade, Molotov, Aflame, Ninja, Chitin, FlashGrenade, GasMask, Stimulator, Armor, \
    Jet
from VegansDeluxe.rebuild.Items.Adrenaline import AdrenalineAction, Adrenaline
from VegansDeluxe.rebuild.Items.FlashGrenade import FlashGrenadeAction
from VegansDeluxe.rebuild.Items.Grenade import GrenadeAction
from VegansDeluxe.rebuild.Items.Jet import JetAction
from VegansDeluxe.rebuild.Items.Molotov import MolotovAction
from VegansDeluxe.rebuild.Items.RageSerum import RageSerumAction
from VegansDeluxe.rebuild.Items.Shield import ShieldAction
from VegansDeluxe.rebuild.Items.Stimulator import StimulatorAction
from VegansDeluxe.rebuild.Items.ThrowingKnife import ThrowingKnifeAction
from VegansDeluxe.rebuild.Skills.Inquisitor import Pray
from VegansDeluxe.rebuild.Skills.ShieldGen import ShieldGenAction
from VegansDeluxe.rebuild.Skills.Weaponsmith import Weaponsmith
from VegansDeluxe.rebuild.States.Dodge import DodgeAction
from VegansDeluxe.rebuild.States.DroppedWeapon import PickUp
from VegansDeluxe.rebuild.States.KnockDown import StandUp
from VegansDeluxe.rebuild.Weapons.Bow import FireArrow
from VegansDeluxe.rebuild.Weapons.Chain import KnockWeapon
from VegansDeluxe.rebuild.Weapons.Molot import TrueStrike
from VegansDeluxe.rebuild.Weapons.Shaft import KnockDown
from VegansDeluxe.rebuild.Weapons.Sledgehammer import SledgehammerCrush
from VegansDeluxe.rebuild.Weapons.Spear import CounterAttack

from VegansDeluxe.core.Actions.EntityActions import ReloadAction, SkipTurnAction, ApproachAction
from ..Skills.Dash import DashAction
from ..Skills.ExplosionMagic import Explosion

# Temporary fight diagnostics (AndroidV2 only). Enable: ANDROID_V2_DIAG=1
DIAG = Counter()
DIAG_ENABLED = os.environ.get("ANDROID_V2_DIAG", "0") == "1"

_DEFENSE_IDS = {
    DodgeAction.id, ShieldAction.id, ShieldGenAction.id,
    FlashGrenadeAction.id, Pray.id, CounterAttack.id,
}
_UTILITY_ABILITY_IDS = {
    KnockWeapon.id, FireArrow.id, KnockDown.id, TrueStrike.id, SledgehammerCrush.id,
}


def _dump_diag() -> None:
    if not DIAG_ENABLED or not DIAG:
        return
    print("\n=== AndroidV2 DIAG ===", flush=True)
    for key, value in sorted(DIAG.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {key}: {value}", flush=True)


atexit.register(_dump_diag)


def _weapon_cost(entity: Entity) -> int:
    return max(int(getattr(getattr(entity, "weapon", None), "energy_cost", 2) or 2), 1)


def swings_with_cost(energy: int, energy_cost: int) -> int:
    """How many attacks fit in remaining energy at this weapon's cost."""
    cost = max(int(energy_cost), 1)
    return max(int(energy), 0) // cost


# Weapon two-turn prep (e.g. aim_rifle). Discover by action id, not weapon class.
_WEAPON_PREP_ACTION_IDS = ("aim_rifle",)


def parse_weapon_aim_state(weapon) -> tuple[Entity | None, int]:
    """Read weapon.main_target = (entity|None, level). Missing attr → no aim mech."""
    raw = getattr(weapon, "main_target", None)
    if not raw:
        return None, 0
    try:
        target, level = raw
    except (TypeError, ValueError):
        return None, 0
    if target is None:
        return None, 0
    try:
        return target, int(level or 0)
    except (TypeError, ValueError):
        return target, 0


@dataclass
class BuildProfile:
    """Snapshot of current build/situation. Aggregates are convenience only, not weapon classes."""

    is_ranged: bool
    energy_cost: int
    cubes: int
    accuracy_bonus: int
    damage_bonus: int
    hit_chance_now: int
    swings_left: int
    can_afford_attack: bool
    # Convenience aggregates over stats (not hard weapon types).
    cost_style: str  # cheap | medium | expensive
    payload_heavy: bool
    accuracy_high: bool
    # Distance / reach
    can_hit_any: bool
    threatened: bool
    has_gap_closer: bool
    needs_approach: bool
    range_style: str  # ranged | melee_gap | melee_walk
    # Kit capacities (available options, not item names as logic keys)
    defense_capacity: int
    offense_capacity: int
    tempo_capacity: int
    sustain_capacity: int
    kit_stance: str  # defensive | balanced | aggressive
    # Two-turn weapon prep (aim / charge): action available + main_target state
    has_weapon_prep: bool
    prep_action_id: str | None
    aim_target: Entity | None
    aim_level: int
    aim_ready: bool
    # Tempo vs threats
    my_swings: int
    enemy_swings: int
    tempo_ahead: bool
    tempo_behind: bool
    hp_ahead: bool
    hp_behind: bool
    fragile: bool
    finishable: bool
    helpless: bool
    min_enemy_hp: int


class AndroidV2(NPC):
    """Android AI that adapts to current weapon/item/action options via BuildProfile."""

    weapon_pool = rebuild.all_weapons
    item_pool = rebuild.game_items_pool
    skill_pool = rebuild.all_skills

    def __init__(self, session_id: str, name=ls("🤖|Android V2")):
        # TODO: Localization
        super().__init__(session_id, name)

        self.weapon = self.choose_weapon()
        self.items.extend(self.choose_items())

        self.hp = 4
        self.max_hp = 4
        self.energy = 5
        self.max_energy = 5

        self.team = 'android_v2'
        self._last_decision: dict = {}
        self._profile: BuildProfile | None = None

        @RegisterEvent(self.session_id, event=PreDeathGameEvent)
        async def on_pre_death(context: EventContext[PreDeathGameEvent]):
            if not DIAG_ENABLED:
                return
            if context.event.entity is not self:
                return
            DIAG["deaths"] += 1
            if self.energy > 0:
                DIAG["died_with_energy"] += 1
            else:
                DIAG["died_energy_empty"] += 1
            d = self._last_decision
            if d.get("finishable") and d.get("chose_defense"):
                DIAG["death_after_defense_instead_of_kill"] += 1
            if d.get("finishable") and d.get("chose_reload"):
                DIAG["death_after_reload_instead_of_kill"] += 1
            if d.get("finishable") and d.get("chose_utility_ability"):
                DIAG["death_after_utility_instead_of_kill"] += 1
            if d.get("chose_dash") or d.get("chose_approach"):
                DIAG["death_after_dash_or_approach"] += 1
            if d.get("bad_focus"):
                DIAG["death_after_bad_focus"] += 1

    def choose_weapon(self):
        ranked = sorted(
            self.weapon_pool,
            key=lambda w: (
                getattr(w, "accuracy_bonus", 0) + getattr(w, "cubes", 0),
                getattr(w, "damage_bonus", 0),
            ),
            reverse=True,
        )
        top = ranked[: max(len(ranked) // 2, 3)]
        return random.choice(top)(self.session_id, self.id)

    def choose_skills(self):
        preferred = []
        for skill in (
                rebuild.ShieldGen, rebuild.Ninja, rebuild.Sadist, rebuild.Biceps,
                rebuild.DoubleVein, rebuild.ToughSkull, rebuild.Scope, rebuild.Visor,
                rebuild.GasMask, rebuild.Medic,
        ):
            if skill in self.skill_pool and skill not in preferred:
                preferred.append(skill)
        pool = [s for s in self.skill_pool if s is not Weaponsmith and s not in preferred]
        random.shuffle(pool)
        random.shuffle(preferred)
        return (preferred + pool)[:2]

    def choose_items(self):
        pool = self.item_pool.copy()
        random.shuffle(pool)
        return pool[0](), pool[1]()

    def can_entity_attack_me(self, target: Entity, session, action_manager) -> bool:
        # Empty-energy enemies cannot swing this turn (simultaneous resolve still
        # lets us punish a reload). Reach itself matches Android: basic attack.
        if target.energy <= 0:
            return False
        attack = action_manager.get_action(session, target, "attack")
        if not attack:
            return False
        return self in attack.targets

    def can_i_attack_entity(self, target: Entity, session, action_manager) -> bool:
        if self.energy <= 0:
            return False
        attack = action_manager.get_action(session, self, "attack")
        if not attack:
            return False
        return target in attack.targets

    def targeted_action(self, action_manager, action_id: str, session: Session[Entity],
                        target: Entity | None = None):
        action = action_manager.get_action(session, self, action_id)
        if not action:
            return
        if not action.targets:
            action.target = action.source
        elif not target:
            action.target = random.choice(action.targets)
        else:
            action.target = target
        return action

    def threat_score(self, entity: Entity) -> float:
        if entity.dead or entity.energy <= 0:
            return 0.0
        if entity.get_state(Stun).stun > 0 or entity.get_state(Knockdown).active:
            return 0.0
        score = float(entity.energy) * 10.0 + float(getattr(entity, "hit_chance", 0))
        if entity.hp <= 2:
            score += 5.0
        if entity.get_state(DroppedWeapon).weapon:
            score *= 0.25
        return score

    @staticmethod
    def swings_for(entity: Entity, energy: int | None = None) -> int:
        een = entity.energy if energy is None else energy
        return swings_with_cost(een, _weapon_cost(entity))

    @staticmethod
    def pick_defense(defense_pool: list) -> Action:
        """Prefer reliable block over dodge/utility when we force a defensive override."""
        shields = [
            a for a in defense_pool
            if a and a.id in (ShieldAction.id, ShieldGenAction.id)
        ]
        if shields:
            return random.choice(shields)
        return random.choice(defense_pool)

    def find_weapon_prep_action_id(self, session, action_manager) -> str | None:
        """Discover a two-turn weapon prep action (aim_*) via ActionManager, not weapon class."""
        for aid in _WEAPON_PREP_ACTION_IDS:
            if action_manager.is_action_available(session, self, aid):
                return aid
        for action in action_manager.get_available_actions(session, self):
            aid = getattr(action, "id", "") or ""
            if aid.startswith("aim_"):
                return aid
        return None

    def queued_weapon_prep(self, action_manager, session, target: Entity | None = None):
        """Build a targeted prep action; prefer existing aim target, else focus pick."""
        prep_id = self.find_weapon_prep_action_id(session, action_manager)
        if not prep_id:
            return None
        aim_target, _ = parse_weapon_aim_state(self.weapon)
        if aim_target is not None and not getattr(aim_target, "dead", True):
            target = aim_target
        return self.targeted_action(action_manager, prep_id, session, target)

    def build_profile(
            self,
            session,
            action_manager,
            enemies,
            enemies_close,
            enemies_can_attack_me,
            enemies_i_can_attack,
            enemies_zombie,
    ) -> BuildProfile:
        w = self.weapon
        cost = max(int(getattr(w, "energy_cost", 2) or 2), 1)
        cubes = int(getattr(w, "cubes", 2) or 2)
        acc = int(getattr(w, "accuracy_bonus", 0) or 0)
        dmg = int(getattr(w, "damage_bonus", 0) or 0)
        hit = int(self.hit_chance)
        swings = swings_with_cost(self.energy, cost)
        can_afford = self.energy >= cost

        if cost <= 2:
            cost_style = "cheap"
        elif cost >= 4:
            cost_style = "expensive"
        else:
            cost_style = "medium"

        payload_heavy = dmg >= 3 or cubes >= 5
        accuracy_high = hit >= 70 or (acc >= 2 and cubes >= 3)

        can_hit_any = bool(enemies_i_can_attack)
        threatened = bool(enemies_can_attack_me)
        has_gap = action_manager.is_action_available(session, self, DashAction.id)
        out_of_melee = (not w.ranged) and bool(enemies) and len(enemies) != len(enemies_close)
        needs_approach = out_of_melee and not can_hit_any and not has_gap

        if w.ranged:
            range_style = "ranged"
        elif has_gap:
            range_style = "melee_gap"
        else:
            range_style = "melee_walk"

        defense_capacity = 0
        for act_id in (ShieldGenAction.id, ShieldAction.id, DodgeAction.id, CounterAttack.id, Pray.id):
            if action_manager.is_action_available(session, self, act_id):
                defense_capacity += 1
        if self.get_item(Chitin.id):
            defense_capacity += 1

        offense_capacity = 0
        for item_id, act_id in (
                (Grenade.id, GrenadeAction.id),
                (Molotov.id, MolotovAction.id),
                (ThrowingKnife.id, ThrowingKnifeAction.id),
                (FlashGrenade.id, FlashGrenadeAction.id),
        ):
            if self.get_item(item_id) and action_manager.is_action_available(session, self, act_id):
                offense_capacity += 1

        tempo_capacity = 0
        if self.get_item(Adrenaline.id):
            tempo_capacity += 1
        if self.get_item(Jet.id):
            tempo_capacity += 1

        sustain_capacity = 1 if self.get_item(Stimulator.id) else 0

        if defense_capacity > offense_capacity and defense_capacity >= 1:
            kit_stance = "defensive"
        elif offense_capacity > 0 and defense_capacity == 0:
            kit_stance = "aggressive"
        else:
            kit_stance = "balanced"

        prep_action_id = self.find_weapon_prep_action_id(session, action_manager)
        has_weapon_prep = prep_action_id is not None
        aim_target, aim_level = parse_weapon_aim_state(w)
        if aim_target is not None and getattr(aim_target, "dead", False):
            aim_target, aim_level = None, 0
        aim_ready = aim_target is not None and aim_level >= 1

        # Effective hit chance after invested aim (Rifle notification: +60/+90).
        if aim_ready:
            hit = hit + (60 if aim_level == 1 else 90 if aim_level >= 2 else 0)

        my_swings = swings
        enemy_swings = max(
            (self.swings_for(e) for e in enemies_can_attack_me),
            default=0,
        )
        min_enemy_hp = min((e.hp for e in enemies_i_can_attack), default=99)
        hp_ahead = self.hp > min_enemy_hp
        hp_behind = self.hp < min_enemy_hp
        finishable = any(e.hp == 1 and e not in enemies_zombie for e in enemies_i_can_attack)
        helpless = any(
            (e.energy <= 0 or e.get_state(Stun).stun > 0 or e.get_state(Knockdown).active)
            and e not in enemies_zombie for e in enemies_i_can_attack
        )
        fragile = self.hp <= 2 or (hp_behind and threatened)

        return BuildProfile(
            is_ranged=bool(w.ranged),
            energy_cost=cost,
            cubes=cubes,
            accuracy_bonus=acc,
            damage_bonus=dmg,
            hit_chance_now=hit,
            swings_left=swings,
            can_afford_attack=can_afford,
            cost_style=cost_style,
            payload_heavy=payload_heavy,
            accuracy_high=accuracy_high,
            can_hit_any=can_hit_any,
            threatened=threatened,
            has_gap_closer=has_gap,
            needs_approach=needs_approach,
            range_style=range_style,
            defense_capacity=defense_capacity,
            offense_capacity=offense_capacity,
            tempo_capacity=tempo_capacity,
            sustain_capacity=sustain_capacity,
            kit_stance=kit_stance,
            has_weapon_prep=has_weapon_prep,
            prep_action_id=prep_action_id,
            aim_target=aim_target,
            aim_level=aim_level,
            aim_ready=aim_ready,
            my_swings=my_swings,
            enemy_swings=enemy_swings,
            tempo_ahead=my_swings > enemy_swings,
            tempo_behind=my_swings < enemy_swings,
            hp_ahead=hp_ahead,
            hp_behind=hp_behind,
            fragile=fragile,
            finishable=finishable,
            helpless=helpless,
            min_enemy_hp=min_enemy_hp,
        )

    def choose_weapon_ability(self, action_manager, session, target: Entity) -> Action:
        """Weapon ability chain. Prefer real attack when finishing or when payload is scarce."""
        if self.get_state(Knockdown).active:
            return self.targeted_action(action_manager, StandUp.id, session)

        charge = action_manager.is_action_available(session, self, DashAction.id)
        act = self.targeted_action(action_manager, "attack", session, target)
        profile = self._profile
        scarce_swing = bool(profile and (profile.payload_heavy or profile.cost_style == "expensive")
                            and profile.swings_left <= 1)

        # True finish or scarce heavy swing: never trade the hit for utility.
        if target.hp <= 1 or scarce_swing:
            if DIAG_ENABLED and target.hp <= 1:
                DIAG["ability_forced_lethal"] += 1
            if charge:
                return self.targeted_action(action_manager, DashAction.id, session, target)
            return act

        if (action_manager.is_action_available(session, self, KnockWeapon.id)
                and percentage_chance(70) and target.energy < target.max_energy):
            act = self.targeted_action(action_manager, KnockWeapon.id, session, target)
        if action_manager.is_action_available(session, self, FireArrow.id) and percentage_chance(40):
            act = self.targeted_action(action_manager, FireArrow.id, session, target)
        if action_manager.is_action_available(session, self, KnockDown.id) and percentage_chance(40):
            act = self.targeted_action(action_manager, KnockDown.id, session, target)
        if (action_manager.is_action_available(session, self, TrueStrike.id)
                and self.energy >= 4 and percentage_chance(50)):
            act = self.targeted_action(action_manager, TrueStrike.id, session, target)
        if (action_manager.is_action_available(session, self, SledgehammerCrush.id)
                and self.energy >= 4 and target.energy > 1 and percentage_chance(50)):
            act = self.targeted_action(action_manager, SledgehammerCrush.id, session, target)
        if charge:
            act = self.targeted_action(action_manager, DashAction.id, session, target)
        return act

    def pick_focus_target(self, candidates: list) -> Entity | None:
        if not candidates:
            return None
        ones = [e for e in candidates if e.hp == 1]
        pool = ones if ones else candidates
        min_hp = min(e.hp for e in pool)
        lowest = [e for e in pool if e.hp == min_hp]
        min_energy = min(e.energy for e in lowest)
        weakest = [e for e in lowest if e.energy == min_energy]
        return random.choice(weakest)

    async def choose_act(self, session, action_manager):
        await super().choose_act(session, action_manager)

        hit_chance = self.hit_chance
        base_hit_chance = hit_chance

        acts = []
        dopitems = []
        flash_candidates = []
        enemies = filter_targets(self, Enemies(), session.entities)
        enemies_close = filter_targets(self, Enemies(Distance.NEARBY_ONLY), session.entities)
        enemies_can_attack_me = []
        enemies_i_can_attack = []
        enemies_zombie = []
        enemies_stunned = []
        enemies_lostweapon = []

        lowest_health = 100

        near_death = self.hp == 1 or (self.hp == 2 and self.get_state(Bleeding).bleeding == 1)
        next_turn_death = self.hp == 1 and self.get_state(Bleeding).bleeding == 1

        debuff = 0

        can_regen = not (debuff >= self.max_energy - self.energy)

        for entity in session.entities:
            target = entity
            if not self.is_ally(target) and not target.dead:
                lowest_health = min(lowest_health, target.hp)

                if self.can_entity_attack_me(target, session, action_manager):
                    enemies_can_attack_me.append(target)
                if self.can_i_attack_entity(target, session, action_manager):
                    enemies_i_can_attack.append(target)

                if target.get_state(ZombieState).active > 0:
                    enemies_zombie.append(target)
                if target.get_state(Stun).stun > 0:
                    enemies_stunned.append(target)
                if target.get_state(DroppedWeapon).weapon:
                    enemies_lostweapon.append(target)

        if len(enemies) == 0:
            action_manager.queue_action(session, self, SkipTurnAction.id)
            return

        profile = self.build_profile(
            session, action_manager, enemies, enemies_close,
            enemies_can_attack_me, enemies_i_can_attack, enemies_zombie,
        )
        self._profile = profile

        if len(enemies_can_attack_me) == 0 and len(enemies_i_can_attack) == 0:
            if self.get_item(ThrowingKnife.id):
                acts.append(self.targeted_action(action_manager, ThrowingKnifeAction.id, session))

        if self.get_item(ThrowingKnife.id) and percentage_chance(50) and session.turn == 1:
            acts.append(self.targeted_action(action_manager, ThrowingKnifeAction.id, session))

        can_attack = profile.can_hit_any

        enemies_armored = []
        for entity in session.entities:
            if entity.get_state(Armor).armor_sum > 0 and entity in enemies_i_can_attack:
                enemies_armored.append(entity)

        low = False
        for entity in enemies_i_can_attack:
            if entity.energy <= self.energy or self.energy == self.max_energy or entity not in enemies_can_attack_me:
                low = True
        if self.get_state(Berserk) and self.hp == 1:
            low = True
        if self.get_item(ThrowingKnife.id) and percentage_chance(50) and (
                self.energy >= 4 or self.energy == self.max_energy):
            acts.append(self.targeted_action(action_manager, ThrowingKnifeAction.id, session))
        if not low:
            hit_chance -= 40
        if len(enemies_armored) == len(enemies_i_can_attack):
            hit_chance -= 50
        if base_hit_chance < 70:
            hit_chance -= 20
        if base_hit_chance < 60:
            hit_chance -= 20
        if len(enemies_i_can_attack) == len(enemies_zombie):
            hit_chance -= 100
        if self.get_state(DroppedWeapon).weapon:
            hit_chance -= 100
            acts.append(self.targeted_action(action_manager, PickUp.id, session))
        if self.get_state(Knockdown).active:
            hit_chance -= 100
        # npcact: weapons with aim-prep get a free attack-pool gate so the
        # two-turn cycle (prep → shot) can start; unaimed shot is converted below.
        if profile.has_weapon_prep and self.energy > 0:
            hit_chance += 100
        # Same attack gate as Android: hitchance roll + can reach. Cost gates reload/adrenaline only.
        if percentage_chance(hit_chance) and can_attack:
            acts.append(self.targeted_action(action_manager, "attack", session))
        else:
            if self.energy >= 2:
                if self.get_item(Grenade.id) and percentage_chance(50) and not self.get_state(Knockdown).active:
                    acts.append(self.targeted_action(action_manager, GrenadeAction.id, session))
                if self.get_item(Molotov.id):
                    molotov = True
                    for entity in enemies:
                        if entity.get_state(Aflame).timer > 1:
                            molotov = False
                    if molotov and percentage_chance(50) and not self.get_state(Knockdown).active:
                        acts.append(self.targeted_action(action_manager, MolotovAction.id, session))
                if self.get_item(ThrowingKnife.id) and self.energy >= 4:
                    if (len(enemies) != len(enemies_zombie)
                            and percentage_chance(50) and not self.get_state(Knockdown).active):
                        acts.append(self.targeted_action(action_manager, ThrowingKnifeAction.id, session))
            # Classic Android bank: reload at <=3. Raising this to energy_cost
            # makes expensive weapons (cost 4-5) reload on every failed hitchance
            # roll and never keep a partial bar — Android wins those fights.
            if self.energy <= 3 and self.energy < self.max_energy and can_regen:
                acts.append(self.targeted_action(action_manager, ReloadAction.id, session))
        if self.energy == 0:
            reload_action = self.targeted_action(action_manager, ReloadAction.id, session)
            if reload_action not in acts and can_regen:
                acts.append(self.targeted_action(action_manager, ReloadAction.id, session))
            if self.get_item(Adrenaline.id) and profile.tempo_capacity > 0:
                if (len(enemies_i_can_attack) != len(enemies_zombie)
                        and debuff <= 1 and not self.get_state(Knockdown).active):
                    after = swings_with_cost(self.energy + 3, profile.energy_cost)
                    if (profile.finishable or after > profile.enemy_swings
                            or percentage_chance(50)):
                        dopitems.append(self.targeted_action(action_manager, AdrenalineAction.id, session, self))

        # Two-turn weapon prep (aim): only when no charge yet — npcact "need_pricel".
        # Stacking a second aim level is optional when raw hitchance is still poor.
        if (profile.has_weapon_prep and profile.prep_action_id and self.energy > 0
                and not self.get_state(Knockdown).active):
            need_prep = not profile.aim_ready
            deepen_aim = (
                profile.aim_ready and profile.aim_level < 2
                and base_hit_chance < 50 and not near_death and not profile.finishable
            )
            if need_prep or deepen_aim:
                prep_target = profile.aim_target
                if prep_target is None or getattr(prep_target, "dead", True):
                    prep_target = self.pick_focus_target(
                        [e for e in enemies if e not in enemies_zombie]
                    ) or (enemies[0] if enemies else None)
                if prep_target is not None:
                    acts.append(self.targeted_action(
                        action_manager, profile.prep_action_id, session, prep_target
                    ))

        for entity in enemies:
            target = entity
            target_hit_chance = target.hit_chance
            aimed_at, aim_lvl = parse_weapon_aim_state(getattr(target, "weapon", None))
            if aimed_at is not None and aim_lvl > 0 and target.energy > 0:
                # Aimed shot is a real threat — inflate for defense decisions.
                target_hit_chance += 60 if aim_lvl == 1 else 90
            if target.get_state(Stun).stun > 0 or target.get_state(Knockdown).active:
                target_hit_chance = 0

            base_chance = target_hit_chance - 30
            dodge_chance = shield_chance = flash_chance = base_chance
            counterattack_chance = target_hit_chance
            pray_chance = target_hit_chance if near_death else 0

            knockdown_active = self.get_state(Knockdown).active
            ninja_active = self.get_state(Ninja)
            aflame_state = target.get_state(Aflame)
            armor_state = self.get_state(Armor)
            zombie_state = self.get_state(ZombieState).active

            if knockdown_active and near_death and target_hit_chance > 50:
                shield_chance += 40
                flash_chance += 40

            if target_hit_chance > 98 and not ninja_active:
                dodge_chance = 0

            if target_hit_chance < 70 and (not near_death or target_hit_chance < 50):
                dodge_chance = shield_chance = flash_chance = counterattack_chance = 0

            if (aflame_state.timer > 1 and aflame_state.flame > 1) or armor_state.armor_sum > 0 \
                    or not enemies_can_attack_me or zombie_state:
                dodge_chance = shield_chance = flash_chance = counterattack_chance = pray_chance = 0

            if target.energy < 4:
                flash_chance = 0

            if len(enemies_can_attack_me) in [len(enemies_lostweapon), len(enemies_stunned)]:
                dodge_chance = shield_chance = flash_chance = pray_chance = 0

            if target in enemies_zombie and target.energy > 1:
                dodge_chance = shield_chance = flash_chance = counterattack_chance = 100
                if near_death:
                    pray_chance = 100

            if knockdown_active:
                dodge_chance = counterattack_chance = 0

            if percentage_chance(dodge_chance):
                if action_manager.is_action_available(session, self, DodgeAction.id):
                    acts.append(self.targeted_action(action_manager, DodgeAction.id, session, self))
            if percentage_chance(shield_chance):
                if action_manager.is_action_available(session, self, ShieldGenAction.id):
                    acts.append(self.targeted_action(action_manager, ShieldGenAction.id, session, self))
                elif action_manager.is_action_available(session, self, ShieldAction.id):
                    acts.append(self.targeted_action(action_manager, ShieldAction.id, session, self))
                elif (self.get_item(Chitin.id) and self.targeted_action(action_manager, DodgeAction.id, session) not in acts
                      and percentage_chance(60)):
                    dopitems.append(self.targeted_action(action_manager, Chitin.id, session, self))
            if percentage_chance(counterattack_chance):
                if action_manager.is_action_available(session, self, CounterAttack.id):
                    if base_hit_chance >= 70 and percentage_chance(base_hit_chance):
                        acts.append(self.targeted_action(action_manager, CounterAttack.id, session))
            if percentage_chance(pray_chance) and action_manager.is_action_available(session, self, Pray.id):
                acts.append(self.targeted_action(action_manager, Pray.id, session, self))
            if percentage_chance(flash_chance):
                if self.get_item(FlashGrenade.id):
                    if target in enemies_can_attack_me:
                        if not target.get_state(GasMask):
                            flash_candidates.append(target)
            if target.hp == 1:
                # Match Android bank window (<=3); also when a swing is unaffordable.
                if self.get_item(Adrenaline.id) and (
                        self.energy <= 3 or self.energy < profile.energy_cost):
                    if debuff <= 1:
                        dopitems.append(self.targeted_action(action_manager, AdrenalineAction.id, session, self))

        if flash_candidates:
            flash_target = max(flash_candidates, key=self.threat_score)
            acts.append(self.targeted_action(action_manager, FlashGrenadeAction.id, session, flash_target))

        # Melee distance: match npcact/Android economy —
        # if nobody can hit anyone yet, bank energy (reload) instead of walking in empty.
        # Approach only when energy is full or we already have a reason to close.
        if (not profile.is_ranged and bool(enemies)
                and len(enemies) != len(enemies_close)):
            if (not profile.can_hit_any and not profile.threatened
                    and self.energy < self.max_energy and can_regen):
                acts.append(self.targeted_action(action_manager, ReloadAction.id, session))
            elif not profile.can_hit_any and not profile.has_gap_closer:
                acts.append(self.targeted_action(action_manager, ApproachAction.id, session))

        if profile.sustain_capacity > 0 and (self.max_hp - self.hp) >= 2 and percentage_chance(80):
            if len(enemies_stunned) != len(enemies):
                acts.append(self.targeted_action(action_manager, StimulatorAction.id, session, self))

        if (
                self.get_state(Aflame).timer > 1 > self.get_state(Armor).armor_sum
                and (not self.get_state(ZombieState).active and self.targeted_action(action_manager, Chitin.id, session, self)
                     not in dopitems)
        ):
            acts.append(self.targeted_action(action_manager, SkipTurnAction.id, session))
            dodge = self.targeted_action(action_manager, DodgeAction.id, session)
            if dodge in acts:
                acts.remove(dodge)
            flash_grenade_act = self.targeted_action(action_manager, FlashGrenadeAction.id, session)
            if flash_grenade_act in acts:
                acts.remove(flash_grenade_act)

        if not acts:
            if self.energy <= 2 and self.energy < self.max_energy and can_regen:
                acts.append(self.targeted_action(action_manager, ReloadAction.id, session))
            elif not profile.can_hit_any and not profile.is_ranged and not profile.has_gap_closer:
                acts.append(self.targeted_action(action_manager, ApproachAction.id, session))
            elif self.energy > 0 and profile.can_hit_any:
                acts.append(self.targeted_action(action_manager, "attack", session))
            else:
                acts.append(self.targeted_action(action_manager, SkipTurnAction.id, session))

        if (self.get_state(Aflame).timer > 1 > self.get_state(Armor).armor_sum
                and self.targeted_action(action_manager, Chitin.id, session, self) not in dopitems
                and not self.get_state(ZombieState).active):
            acts = [self.targeted_action(action_manager, SkipTurnAction.id, session)]

        # --- Choice + BuildProfile-aware overrides ---
        finishable = profile.finishable
        helpless = profile.helpless

        acts = [act for act in acts if act]
        pool_before = list(acts)

        # Sustain kits: when chipped, overweight heal in the roll.
        choice_pool = acts
        if (profile.sustain_capacity > 0 and (self.max_hp - self.hp) >= 2
                and not finishable):
            stims = [a for a in acts if a and a.id == StimulatorAction.id]
            if stims:
                choice_pool = list(acts) + stims

        act: Action = random.choice(choice_pool) if choice_pool else self.targeted_action(
            action_manager, SkipTurnAction.id, session
        )

        # Soft defense -> attack: only probabilistic dodge.
        # Never convert Shield/ShieldGen. Press when we can refill or already lead.
        soft_ok = (
            not near_death and low and can_attack
            and self.energy >= profile.energy_cost
            and profile.sustain_capacity == 0
            and (
                profile.tempo_capacity > 0
                or profile.hp_ahead
                or (profile.tempo_ahead and self.hp >= 3)
            )
        )
        if (act and act.id == DodgeAction.id and soft_ok and percentage_chance(55)):
            if DIAG_ENABLED:
                DIAG["soft_defense_to_attack"] += 1
            act = self.targeted_action(action_manager, "attack", session)

        # Attrition: when behind on HP, energy-disadvantaged, and threatened,
        # do not take the trade — use a reliable block if the roll offered one.
        if (act and act.id == "attack" and profile.sustain_capacity > 0
                and profile.hp_behind and profile.threatened and not low
                and not finishable and not near_death
                and not self.get_state(Knockdown).active):
            defense_pool = [
                a for a in pool_before
                if a and a.id in (ShieldAction.id, ShieldGenAction.id, DodgeAction.id)
            ]
            if defense_pool:
                act = self.pick_defense(defense_pool)

        if (can_attack and self.energy > 0 and not self.get_state(Knockdown).active
                and (finishable or helpless)
                and act and act.id in (
                    ReloadAction.id, ApproachAction.id, SkipTurnAction.id,
                    GrenadeAction.id, MolotovAction.id, StimulatorAction.id)):
            if DIAG_ENABLED:
                DIAG["kill_override"] += 1
            act = self.targeted_action(action_manager, "attack", session)
        elif (finishable and can_attack and self.energy > 0 and not near_death
                and not self.get_state(Knockdown).active
                and act and act.id in (
                    DodgeAction.id, ShieldAction.id, ShieldGenAction.id,
                    FlashGrenadeAction.id, Pray.id)):
            # At near_death keep the rolled defense — forcing the finish into a
            # live threat loses the race vs Android's willingness to block at 1hp.
            if DIAG_ENABLED:
                DIAG["kill_override"] += 1
            act = self.targeted_action(action_manager, "attack", session)

        # Don't reload with a ready multi-swing bar when we hold tempo and accuracy.
        # Pressing a last scrap swing (1 swing left) after a failed hitchance roll
        # is how V2 loses attrition vs Android's bank-to-full pattern.
        if (act and act.id == ReloadAction.id and low and can_attack
                and self.energy >= profile.energy_cost and not near_death
                and profile.swings_left >= 2
                and base_hit_chance >= 70):
            act = self.targeted_action(action_manager, "attack", session)

        # Don't approach when we already have a real attack opportunity.
        if act and act.id == ApproachAction.id and can_attack and self.energy > 0:
            act = self.targeted_action(action_manager, "attack", session)

        # --- Weapon prep cycle (aim → shot), npcact "pricel" idea ---
        # 1) Never fire cold when a prep action exists and we have no charge.
        if (act and act.id == "attack" and profile.has_weapon_prep
                and not profile.aim_ready and self.energy > 0
                and not self.get_state(Knockdown).active):
            prep = self.queued_weapon_prep(action_manager, session)
            if prep:
                if DIAG_ENABLED:
                    DIAG["weapon_prep_instead_of_cold_shot"] += 1
                act = prep
        # 2) After aiming, finish the combo: don't reload/utility away the setup.
        elif (profile.aim_ready and can_attack and self.energy > 0
                and not self.get_state(Knockdown).active
                and act and act.id in (
                    ReloadAction.id, ApproachAction.id, SkipTurnAction.id,
                    GrenadeAction.id, MolotovAction.id, StimulatorAction.id)):
            if DIAG_ENABLED:
                DIAG["weapon_prep_complete_shot"] += 1
            act = self.targeted_action(action_manager, "attack", session)
        # 3) Soft defense while aimed and able to shoot: prefer the charged shot.
        elif (profile.aim_ready and can_attack and self.energy >= profile.energy_cost
                and not near_death and not self.get_state(Knockdown).active
                and act and act.id == DodgeAction.id and percentage_chance(60)):
            if DIAG_ENABLED:
                DIAG["weapon_prep_complete_shot"] += 1
            act = self.targeted_action(action_manager, "attack", session)

        if not self.get_state(ZombieState).active:
            if next_turn_death and self.get_item(Stimulator.id):
                act = self.targeted_action(action_manager, StimulatorAction.id, session, self)
        if self.get_state(ZombieState).active:
            if self.get_item(Chitin.id) and self.targeted_action(action_manager, Chitin.id, session, self) not in dopitems:
                dopitems.append(self.targeted_action(action_manager, Chitin.id, session, self))
            if self.get_state(ZombieState).timer >= 1:
                if self.energy > 0:
                    if len(enemies_i_can_attack) > 0:
                        act = self.targeted_action(action_manager, "attack", session)
                if self.get_item(Adrenaline.id) and debuff <= 1:
                    if len(enemies_i_can_attack) > 0:
                        dopitems.append(self.targeted_action(action_manager, AdrenalineAction.id, session, self))
                elif self.get_item(ThrowingKnife.id):
                    act = self.targeted_action(action_manager, ThrowingKnifeAction.id, session)
                if action_manager.is_action_available(session, self, GrenadeAction.id):
                    act = self.targeted_action(action_manager, GrenadeAction.id, session)
            else:
                if base_hit_chance < 50:
                    if self.energy < self.max_energy and can_regen:
                        act = self.targeted_action(action_manager, ReloadAction.id, session, self)
                    else:
                        if len(enemies_i_can_attack) > 0:
                            act = self.targeted_action(action_manager, "attack", session)
                if 65 >= base_hit_chance >= 50:
                    if percentage_chance(base_hit_chance):
                        if len(enemies_i_can_attack) > 0:
                            act = self.targeted_action(action_manager, "attack", session)
                    else:
                        if self.energy < self.max_energy and can_regen:
                            act = self.targeted_action(action_manager, ReloadAction.id, session, self)
                        else:
                            if len(enemies_i_can_attack) > 0:
                                act = self.targeted_action(action_manager, "attack", session)
                if base_hit_chance > 65:
                    if len(enemies_i_can_attack) > 0:
                        act = self.targeted_action(action_manager, "attack", session)
                # On heavy fire without armor, skip rather than dump remaining energy.
                if (self.get_state(Aflame).timer > 1 and self.get_state(Aflame).flame > 2
                        and self.get_state(Armor).armor_sum < 1):
                    if self.energy > profile.energy_cost:
                        act = self.targeted_action(action_manager, SkipTurnAction.id, session)
                    elif can_regen:
                        act = self.targeted_action(action_manager, ReloadAction.id, session, self)

        focus_target = None
        if act and act.id == "attack":
            # Burst items: match Android's 40% attack->grenade swap.
            # Do NOT gate on hitchance — accurate kits (Scope) still benefit from
            # burst when offense_capacity is the kit's main tool.
            # Only suppress when finishing, burning the last expensive swing,
            # or abandoning an invested weapon-prep charge.
            if (self.hp >= 1 and self.get_item(Grenade.id) and self.energy >= 2
                    and not finishable
                    and not profile.aim_ready
                    and not (profile.payload_heavy and profile.swings_left <= 1)
                    and percentage_chance(40)):
                act = self.targeted_action(action_manager, GrenadeAction.id, session)
            else:
                targets = []
                if len(enemies_zombie) == len(enemies_i_can_attack):
                    for entity in enemies_i_can_attack:
                        targets.append(entity)
                        if entity.hp == lowest_health:
                            targets.append(entity)
                elif len(enemies_armored) == len(enemies_i_can_attack):
                    for entity in enemies_i_can_attack:
                        if entity not in enemies_zombie:
                            targets.append(entity)
                            if entity.hp == lowest_health:
                                targets.append(entity)
                else:
                    for entity in enemies_i_can_attack:
                        if entity.get_state(Armor).armor_sum < 1 and entity not in enemies_zombie:
                            targets.append(entity)
                            if entity.hp == lowest_health:
                                targets.append(entity)
                # Charged aim locks focus onto main_target (npcact).
                if (profile.aim_ready and profile.aim_target is not None
                        and not getattr(profile.aim_target, "dead", True)):
                    targets = [profile.aim_target]
                if not targets:
                    if self.energy < self.max_energy:
                        act = self.targeted_action(action_manager, ReloadAction.id, session)
                    else:
                        act = self.targeted_action(action_manager, SkipTurnAction.id, session)
                else:
                    focus_target = self.pick_focus_target(targets)
                    act = self.choose_weapon_ability(action_manager, session, focus_target)

        elif act and profile.prep_action_id and act.id == profile.prep_action_id:
            # Keep / pick prep target (npcact pricel target selection).
            prep_target = profile.aim_target
            if prep_target is None or getattr(prep_target, "dead", True):
                candidates = [e for e in enemies if e not in enemies_zombie] or list(enemies)
                prep_target = self.pick_focus_target(candidates)
            if prep_target is not None:
                act = self.targeted_action(
                    action_manager, profile.prep_action_id, session, prep_target
                )
        elif act and act.id == ReloadAction.id:
            if self.get_state(Knockdown).active:
                act = self.targeted_action(action_manager, StandUp.id, session)
            else:
                if self.get_item(Jet.id) and percentage_chance(50):
                    dopitems.append(self.targeted_action(action_manager, JetAction.id, session, self))
                elif (action_manager.is_action_available(session, self, RageSerumAction.id) and
                      percentage_chance(30)):
                    dopitems.append(self.targeted_action(action_manager, RageSerumAction.id, session, self))
        elif act and act.id in [GrenadeAction.id, MolotovAction.id] and self.get_state(Knockdown).active:
            act = self.targeted_action(action_manager, StandUp.id, session)
        elif act and act.id == DodgeAction.id:
            if self.get_state(Knockdown).active:
                if action_manager.is_action_available(session, self, ShieldGenAction.id):
                    act = self.targeted_action(action_manager, ShieldGenAction.id, session, self)
                elif action_manager.is_action_available(session, self, ShieldAction.id):
                    act = self.targeted_action(action_manager, ShieldAction.id, session, self)
                else:
                    act = self.targeted_action(action_manager, StandUp.id, session)
        if next_turn_death:
            if action_manager.is_action_available(session, self, Pray.id):
                act = self.targeted_action(action_manager, Pray.id, session, self)
                dopitems = []

        for entity in enemies:
            target = entity
            if action_manager.is_action_available(session, target, Explosion.id):
                if action_manager.is_action_available(session, self, ShieldGenAction.id):
                    act = self.targeted_action(action_manager, ShieldGenAction.id, session, self)
                elif action_manager.is_action_available(session, self, ShieldAction.id):
                    act = self.targeted_action(action_manager, ShieldAction.id, session, self)
                elif (action_manager.is_action_available(session, self, SledgehammerCrush.id)
                      and self.energy >= 4 and not self.get_state(Knockdown).active):
                    act = self.targeted_action(action_manager, SledgehammerCrush.id, session, target)
                else:
                    act = self.targeted_action(action_manager, SkipTurnAction.id, session)
        if not act:
            session.say("🐭| 😭🍵.")
            act = self.targeted_action(action_manager, SkipTurnAction.id, session)

        # --- Diagnostics ---
        if DIAG_ENABLED and act:
            DIAG["turns"] += 1
            DIAG[f"act_{act.id}"] += 1
            attack_in_pool = any(a and a.id == "attack" for a in pool_before)
            defense_in_pool = any(a and a.id in _DEFENSE_IDS for a in pool_before)
            reload_in_pool = any(a and a.id == ReloadAction.id for a in pool_before)
            chose_defense = act.id in _DEFENSE_IDS
            chose_reload = act.id == ReloadAction.id
            chose_utility = act.id in _UTILITY_ABILITY_IDS
            if finishable and attack_in_pool and chose_defense:
                DIAG["defense_over_kill"] += 1
            if finishable and attack_in_pool and chose_reload:
                DIAG["reload_over_kill"] += 1
            if finishable and chose_utility:
                DIAG["utility_over_kill"] += 1
            if defense_in_pool and attack_in_pool and chose_defense and not near_death:
                DIAG["defense_over_attack_tempo"] += 1
            if reload_in_pool and attack_in_pool and chose_reload and low and self.energy >= 2:
                DIAG["reload_over_attack_tempo"] += 1
            self._last_decision = {
                "finishable": finishable,
                "chose_defense": chose_defense,
                "chose_reload": chose_reload,
                "chose_utility_ability": chose_utility,
                "chose_dash": act.id == DashAction.id,
                "chose_approach": act.id == ApproachAction.id,
                "bad_focus": self._last_decision.get("bad_focus", False),
            }

        for item in dopitems:
            if item.item not in self.items:
                continue
            action_manager.queue_action_instance(item)
            if ActionTag.ITEM in item.tags:
                self.items.remove(item.item)
        action_manager.queue_action_instance(act)
        if ActionTag.ITEM in act.tags and act.item in self.items:
            self.items.remove(act.item)


@AttachedAction(AndroidV2)
class ApproachAction(ApproachAction):
    pass


@AttachedAction(AndroidV2)
class ReloadAction(ReloadAction):
    pass


@AttachedAction(AndroidV2)
class SkipTurnAction(SkipTurnAction):
    pass
