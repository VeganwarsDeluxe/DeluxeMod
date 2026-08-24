import random

from VegansDeluxe.core import At, Enemies, Entity, EventContext, ExecuteActionEvent, MeleeAttack, \
    PostDamageGameEvent, PostTickGameEvent, PostUpdateActionsGameEvent, RegisterEvent, RegisterWeapon, SelfOnly, \
    Session, AttachedAction
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon
from VegansDeluxe.rebuild.States.Aflame import Aflame
from VegansDeluxe.rebuild.States.Armor import Armor

from DeluxeMod.Entities.Slime import Slime
from DeluxeMod.States.CorrosiveMucus import CorrosiveMucus

BLOCK_ENERGY_COST = 2
BLOCKED_GRENADE_IDS = {'grenade', 'mucus_in_the_bottle'}
SELF_CAST_GRENADE_IDS = {'grenade', 'molotov', 'mucus_in_the_bottle', 'cryo_grenade', 'energy_grenade',
                         'death_grenade'}
SELF_CAST_ENERGY_REFUND = 1

MOLOTOV_BUFF_DURATION = 2
MOLOTOV_BUFF_DAMAGE = 1
MOLOTOV_BURN_STACKS = 1

_self_cast_variant_cache = {}


def get_self_cast_variant(action_type):
    """
    Builds (and caches) a self-targetable, instant duplicate of a grenade item's action class.

    Instant actions (cost == -1) execute immediately on selection and never publish
    ExecuteActionEvent, so AluminiumBat's block+redirect watcher can't see them coming --
    this variant registers the block itself, right before running the item's real func().
    """
    variant = _self_cast_variant_cache.get(action_type)
    if variant is None:
        blockable = action_type.id in BLOCKED_GRENADE_IDS

        class SelfCastVariant(action_type):
            id = 'self_' + action_type.id
            target_type = SelfOnly()

            @property
            def cost(self):
                return -1

            async def func(self, source, target):
                weapon = source.weapon
                if blockable and isinstance(weapon, AluminiumBat):
                    weapon.register_block(self.session, source, source, action_type.id)
                result = await super().func(source, target)
                source.energy = min(source.energy + SELF_CAST_ENERGY_REFUND, source.max_energy)
                return result

        variant = SelfCastVariant
        _self_cast_variant_cache[action_type] = variant
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
        async def watch_grenades(context: EventContext[ExecuteActionEvent]):
            entity = context.session.get_entity(entity_id)
            if not entity or entity.weapon is not self:
                return

            action = context.event.action
            item = getattr(action, 'item', None)
            if item is None:
                return

            # NOTE: Molotov's own func() re-rolls random targets from the thrower's enemy
            # pool, same as Grenade, so gating on action.target here is only an
            # approximation of "did this actually hit me" -- Molotov doesn't publish any
            # per-hit event to react to properly. Flagged separately, not fixed yet.
            if item.id == 'molotov':
                if action.target != entity:
                    return
                self.molotov_buff_expires_turn = context.session.turn + MOLOTOV_BUFF_DURATION
                if not self.molotov_buff_active:
                    self.molotov_buff_active = True
                    self.damage_bonus += MOLOTOV_BUFF_DAMAGE
                context.session.say(ls("deluxe.weapon.aluminium_bat.molotov_buff").format(entity.name),
                                    source_id=entity_id, target_id=entity_id)
                return

            if item.id not in BLOCKED_GRENADE_IDS:
                return

            self.register_block(context.session, action.source, entity, item.id)

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
        async def add_self_cast_actions(context: EventContext[PostUpdateActionsGameEvent]):
            if context.event.entity_id != entity_id:
                return
            entity = context.session.get_entity(entity_id)
            if not entity or entity.weapon is not self:
                return
            entity_actions = context.action_manager.actions.get((context.session, entity))
            if entity_actions is None:
                return
            for item in entity.items:
                if item.id not in SELF_CAST_GRENADE_IDS:
                    continue
                resolved = context.action_manager.get_action_from_all_actions(item.id)
                if not resolved:
                    continue
                _, action_type = resolved
                variant = get_self_cast_variant(action_type)
                entity_actions.append(variant(context.session, entity, item))

    def register_block(self, session: Session, thrower: Entity, wielder: Entity, item_id: str):
        """
        Reactively intercepts the next PostDamageGameEvent from `thrower` landing on
        `wielder` this turn, zeroing it and applying the same effect to a random enemy
        of the wielder instead. Used for both enemy throws and self-casts (where
        thrower is wielder).
        """
        already_blocked = False

        @At(session.id, turn=session.turn, event=PostDamageGameEvent,
            filters=[lambda event: event.source == thrower and event.target == wielder])
        async def block_hit(context: EventContext[PostDamageGameEvent]):
            nonlocal already_blocked
            if already_blocked or not context.event.damage:
                return
            already_blocked = True

            blocked_amount = context.event.damage
            context.event.damage = 0

            enemies = filter_targets(wielder, Enemies(), context.session.entities)
            if not enemies:
                return

            wielder.energy = max(wielder.energy - BLOCK_ENERGY_COST, 0)
            redirect_target = random.choice(enemies)

            if item_id == 'mucus_in_the_bottle':
                if not isinstance(redirect_target, Slime):
                    removed_armor = redirect_target.get_state(Armor).remove_one()
                    corrosive_mucus = redirect_target.get_state(CorrosiveMucus)
                    if removed_armor:
                        corrosive_mucus.removed_armor.append(removed_armor)
                    corrosive_mucus.corrosive_mucus -= 1
                    corrosive_mucus.active = True
            else:
                redirect_target.inbound_dmg.add(wielder, blocked_amount, context.session.turn)

            context.session.say(
                ls("deluxe.weapon.aluminium_bat.block_redirect").format(wielder.name, redirect_target.name),
                source_id=wielder.id, target_id=redirect_target.id)


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
