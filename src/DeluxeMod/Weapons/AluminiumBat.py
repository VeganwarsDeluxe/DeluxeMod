import random

from VegansDeluxe.core import Enemies, Entity, EventContext, ExecuteActionEvent, MeleeAttack, PostTickGameEvent, \
    PostUpdateActionsGameEvent, RegisterEvent, RegisterWeapon, SelfOnly, Session, AttachedAction
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon
from VegansDeluxe.rebuild.States.Aflame import Aflame

STEAL_ENERGY_COST = 2
BLOCKED_GRENADE_IDS = {'grenade', 'mucus_in_the_bottle'}
QUICK_THROW_GRENADE_IDS = {'grenade', 'molotov', 'mucus_in_the_bottle', 'cryo_grenade', 'energy_grenade',
                           'death_grenade'}
QUICK_THROW_ENERGY_COST = 3

MOLOTOV_BUFF_DURATION = 2
MOLOTOV_BUFF_DAMAGE = 1
MOLOTOV_BURN_STACKS = 1

_quick_throw_variant_cache = {}


def get_quick_throw_variant(action_type):
    """
    Builds (and caches) a self-targetable, instant duplicate of a grenade item's action
    class -- pressing it either lobs the item at a random enemy for a flat energy cost,
    or (Molotov specifically) consumes it to directly charge up the bat's own buff.
    """
    variant = _quick_throw_variant_cache.get(action_type)
    if variant is None:
        is_molotov = action_type.id == 'molotov'

        class QuickThrowVariant(action_type):
            id = 'quick_throw_' + action_type.id
            target_type = SelfOnly()

            @property
            def cost(self):
                return -1

            async def func(self, source, target):
                weapon = source.weapon
                if is_molotov:
                    if isinstance(weapon, AluminiumBat):
                        weapon.apply_molotov_buff(self.session, source)
                    return None

                enemies = filter_targets(source, Enemies(), self.session.entities)
                if not enemies:
                    return None
                random_target = random.choice(enemies)

                energy_before = source.energy
                result = await super().func(source, random_target)
                source.energy = min(max(energy_before - QUICK_THROW_ENERGY_COST, 0), source.max_energy)
                return result

        variant = QuickThrowVariant
        _quick_throw_variant_cache[action_type] = variant
    return variant


@RegisterWeapon
class AluminiumBat(MeleeWeapon):
    id = 'aluminium_bat'
    name = ls("deluxe.weapon.aluminium_bat.name")
    description = ls("deluxe.weapon.aluminium_bat.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.molotov_buff_active = False
        self.molotov_buff_expires_turn = 0

        @RegisterEvent(session_id, event=ExecuteActionEvent, priority=-10)
        async def steal_grenades(context: EventContext[ExecuteActionEvent]):
            entity = context.session.get_entity(entity_id)
            if not entity or entity.dead or entity.weapon is not self:
                return

            action = context.event.action
            item = getattr(action, 'item', None)
            if item is None:
                return

            thrower = action.source
            if thrower == entity:
                return

            # NOTE: Molotov's own func() re-rolls random targets from the thrower's enemy
            # pool, same as Grenade, so gating on action.target here is only an
            # approximation of "did this actually hit me" -- Molotov doesn't publish any
            # per-hit event to react to properly. Flagged separately, not fixed yet.
            if item.id == 'molotov':
                if action.target != entity:
                    return
                self.apply_molotov_buff(context.session, entity)
                return

            if item.id not in BLOCKED_GRENADE_IDS or entity.is_ally(thrower):
                return

            # Steal it outright, before it resolves: no original text, no damage to anyone.
            action.canceled = True
            energy_before = entity.energy
            entity.energy = max(entity.energy - STEAL_ENERGY_COST, 0)
            context.session.say(
                ls("deluxe.weapon.aluminium_bat.steal").format(entity.name, thrower.name),
                source_id=entity_id, target_id=thrower.id)

            resolved = context.action_manager.get_action_from_all_actions(item.id)
            if not resolved:
                return
            _, action_type = resolved
            retaliation = action_type(context.session, entity, item)
            retaliation.target = thrower
            await retaliation.execute()
            # Whatever the retaliation charged internally is folded back in -- the only
            # net cost for the whole steal+retaliate is the flat STEAL_ENERGY_COST above.
            entity.energy = min(max(energy_before - STEAL_ENERGY_COST, 0), entity.max_energy)

        @RegisterEvent(session_id, event=PostTickGameEvent)
        async def molotov_buff_tick(context: EventContext[PostTickGameEvent]):
            if not self.molotov_buff_active or context.session.turn < self.molotov_buff_expires_turn:
                return
            self.molotov_buff_active = False
            self.damage_bonus -= MOLOTOV_BUFF_DAMAGE
            entity = context.session.get_entity(entity_id)
            if entity:
                context.session.say(ls("deluxe.weapon.aluminium_bat.molotov_buff_end").format(entity.name),
                                    source_id=entity_id, target_id=entity_id)

        @RegisterEvent(session_id, event=PostUpdateActionsGameEvent)
        async def add_quick_throw_actions(context: EventContext[PostUpdateActionsGameEvent]):
            if context.event.entity_id != entity_id:
                return
            entity = context.session.get_entity(entity_id)
            if not entity or entity.weapon is not self:
                return
            entity_actions = context.action_manager.actions.get((context.session, entity))
            if entity_actions is None:
                return
            for item in entity.items:
                if item.id not in QUICK_THROW_GRENADE_IDS:
                    continue
                resolved = context.action_manager.get_action_from_all_actions(item.id)
                if not resolved:
                    continue
                _, action_type = resolved
                variant = get_quick_throw_variant(action_type)
                entity_actions.append(variant(context.session, entity, item))

    def apply_molotov_buff(self, session: Session, entity: Entity):
        self.molotov_buff_expires_turn = session.turn + MOLOTOV_BUFF_DURATION
        if not self.molotov_buff_active:
            self.molotov_buff_active = True
            self.damage_bonus += MOLOTOV_BUFF_DAMAGE
        session.say(ls("deluxe.weapon.aluminium_bat.molotov_buff").format(entity.name),
                    source_id=entity.id, target_id=entity.id)


@AttachedAction(AluminiumBat)
class AluminiumBatAttack(MeleeAttack):
    def __init__(self, session: Session, source: Entity, weapon: AluminiumBat):
        super().__init__(session, source, weapon)
        self.weapon: AluminiumBat = weapon

    async def func(self, source, target):
        damage = (await self.attack(source, target)).dealt
        if damage and self.weapon.molotov_buff_active:
            target.get_state(Aflame).add_flame(self.session, target, source, MOLOTOV_BURN_STACKS)
        return damage
