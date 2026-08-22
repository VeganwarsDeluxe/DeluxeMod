import random

from VegansDeluxe.core import ActionTag, At, Attack, AttachedAction, Enemies, Entity, EventContext, \
    ExecuteActionEvent, HPLossGameEvent, MeleeAttack, PreDamagesGameEvent, PreMoveGameEvent, RegisterEvent, \
    RegisterWeapon, SelfOnly, Session, percentage_chance, per_cubes
from VegansDeluxe.core.Actions.Action import DecisiveAction, filter_targets
from VegansDeluxe.core.Translator.LocalizedList import LocalizedList
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon
from VegansDeluxe.rebuild import Armor, Bleeding, Knockdown, Stun

EGO_UNLOCK_DAMAGE = 25
EGO_DURATION = 4
EGO_ARMOR = 2


@RegisterWeapon
class Mimicry(MeleeWeapon):
    id = 'mimicry'
    name = ls("deluxe.weapon.mimicry.name")
    description = ls("deluxe.weapon.mimicry.description")

    cubes = 2
    accuracy_bonus = 2
    damage_bonus = 1
    energy_cost = 2

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.hit_count = 0
        self.total_damage_dealt = 0

        self.onrush_cooldown_turn = 0
        self.vertical_cooldown_turn = 0
        self.horizontal_cooldown_turn = 0

        self.ego_expires_turn = 0
        self.ego_armor = None

        @RegisterEvent(session_id, event=ExecuteActionEvent, priority=-1)
        async def reset_combo_on_reload(context: EventContext[ExecuteActionEvent]):
            action = context.event.action
            if action.source is None or action.source.id != entity_id:
                return
            if ActionTag.RELOAD in action.tags:
                self.hit_count = 0

        @RegisterEvent(session_id, event=PreMoveGameEvent)
        async def ego_upkeep(context: EventContext[PreMoveGameEvent]):
            if self.ego_expires_turn and context.session.turn >= self.ego_expires_turn:
                entity = context.session.get_entity(entity_id)
                if entity and self.ego_armor is not None:
                    entity.get_state(Armor).remove(self.ego_armor)
                self.ego_expires_turn = 0
                self.ego_armor = None
                if entity:
                    context.session.say(ls("deluxe.weapon.mimicry.ego_end").format(entity.name),
                                        source_id=entity_id, target_id=entity_id)

        @RegisterEvent(session_id, event=HPLossGameEvent)
        async def ego_reactive_armor(context: EventContext[HPLossGameEvent]):
            if not self.ego_expires_turn:
                return
            if context.event.source.id != entity_id:
                return

            entity = context.event.source
            armor_state = entity.get_state(Armor)
            if self.ego_armor is not None:
                armor_state.remove(self.ego_armor)
            value = (self.ego_armor[0] if self.ego_armor else EGO_ARMOR) + context.event.hp_loss
            self.ego_armor = (value, 100)
            armor_state.add(*self.ego_armor)
            self.ego_expires_turn += context.event.hp_loss

    def register_damage(self, damage: int):
        if damage:
            self.total_damage_dealt += damage

    def register_combo_hit(self, session: Session, source: Entity, target: Entity, damage: int):
        if not damage:
            return
        self.hit_count += 1
        if self.hit_count % 3 == 0:
            target.get_state(Knockdown).active = True
            session.say(ls("deluxe.weapon.mimicry.knockdown").format(source.name, target.name, self.hit_count),
                        source_id=source.id, target_id=target.id)
            if percentage_chance(25):
                target.get_state(Bleeding).active = True


@AttachedAction(Mimicry)
class MimicryAttack(MeleeAttack):
    def __init__(self, session: Session, source: Entity, weapon: Mimicry):
        super().__init__(session, source, weapon)
        self.weapon: Mimicry = weapon

    async def func(self, source, target):
        damage = (await self.attack(source, target)).dealt
        self.weapon.register_damage(damage)
        self.weapon.register_combo_hit(self.session, source, target, damage)
        return damage


def self_stun(session: Session, source: Entity, turns: int):
    @At(session.id, turn=session.turn + 1, event=PreMoveGameEvent)
    async def apply(context):
        source.get_state(Stun).stun += turns


@AttachedAction(Mimicry)
class Onrush(Attack):
    id = 'onrush'
    name = ls("deluxe.weapon.mimicry.onrush.name")
    target_type = Enemies()

    def __init__(self, session: Session, source: Entity, weapon: Mimicry):
        super().__init__(session, source, weapon)
        self.weapon: Mimicry = weapon

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.onrush_cooldown_turn

    @property
    def blocked(self) -> bool:
        return self.source.energy < 3

    def calculate_damage(self, source, target, energy=None):
        if energy is None:
            energy = source.energy
        if energy <= 0:
            return 0
        hits = per_cubes(3, 1, energy, target.inbound_accuracy_bonus + source.outbound_accuracy_bonus)
        return (hits + 2) if hits else 0

    def send_attack_message(self, source: Entity, target: Entity, damage: int):
        target_name = self.SELF_TARGET_NAME if source == target else target.name
        if damage:
            message = ls("deluxe.weapon.mimicry.onrush.hit").format(source.name, target_name, damage)
        else:
            message = ls("deluxe.weapon.mimicry.onrush.miss").format(source.name, target_name)
        self.session.say(message, source_id=source.id, target_id=target.id)

    async def func(self, source: Entity, target: Entity):
        self.weapon.onrush_cooldown_turn = self.session.turn + 5

        if target not in source.nearby_entities:
            source.nearby_entities = list(set(source.nearby_entities + [target]))
            target.nearby_entities = list(set(target.nearby_entities + [source]))

        damage = (await self.attack(source, target, energy_cost=3)).dealt
        self.weapon.register_damage(damage)

        if not damage:
            self_stun(self.session, source, 1)

        return damage


@AttachedAction(Mimicry)
class GreatSplitVertical(MeleeAttack):
    id = 'great_split_vertical'
    name = ls("deluxe.weapon.mimicry.vertical.name")

    def __init__(self, session: Session, source: Entity, weapon: Mimicry):
        super().__init__(session, source, weapon)
        self.weapon: Mimicry = weapon

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.vertical_cooldown_turn

    @property
    def blocked(self) -> bool:
        return self.source.energy < 5

    def calculate_damage(self, source, target, energy=None):
        if energy is None:
            energy = source.energy
        if energy <= 0:
            return 0
        hits = per_cubes(3, 0, energy, target.inbound_accuracy_bonus + source.outbound_accuracy_bonus)
        return (hits + 4) if hits else 0

    async def func(self, source: Entity, target: Entity):
        self.weapon.vertical_cooldown_turn = self.session.turn + 5

        self.session.say(ls("deluxe.weapon.mimicry.vertical.charge").format(source.name, target.name),
                         source_id=source.id, target_id=target.id)
        self_stun(self.session, source, 1)

        @At(self.session.id, turn=self.session.turn + 1, event=PreDamagesGameEvent)
        async def resolve(context):
            if target.dead or source.dead:
                return

            damage = (await self.attack(source, target, energy_cost=5)).dealt
            self.weapon.register_damage(damage)

            if damage:
                self_stun(self.session, target, 1)
            else:
                self_stun(self.session, source, 2)


@AttachedAction(Mimicry)
class EGO(DecisiveAction):
    id = 'ego'
    name = ls("deluxe.weapon.mimicry.ego.name")
    target_type = SelfOnly()

    def __init__(self, session: Session, source: Entity, weapon: Mimicry):
        super().__init__(session, source)
        self.weapon: Mimicry = weapon

    @property
    def hidden(self) -> bool:
        if self.weapon.total_damage_dealt < EGO_UNLOCK_DAMAGE:
            return True
        return self.source.hp > self.source.max_hp // 2

    async def func(self, source: Entity, target: Entity):
        self.weapon.total_damage_dealt = 0

        armor_state = source.get_state(Armor)
        if self.weapon.ego_armor is not None:
            armor_state.remove(self.weapon.ego_armor)

        self.weapon.ego_armor = (EGO_ARMOR, 100)
        armor_state.add(*self.weapon.ego_armor)
        self.weapon.ego_expires_turn = self.session.turn + EGO_DURATION

        self.session.say(ls("deluxe.weapon.mimicry.ego.text").format(source.name),
                         source_id=source.id, target_id=source.id)


@AttachedAction(Mimicry)
class GreatSplitHorizontal(MeleeAttack):
    id = 'great_split_horizontal'
    name = ls("deluxe.weapon.mimicry.horizontal.name")

    def __init__(self, session: Session, source: Entity, weapon: Mimicry):
        super().__init__(session, source, weapon)
        self.weapon: Mimicry = weapon

    @property
    def hidden(self) -> bool:
        if self.session.turn < self.weapon.horizontal_cooldown_turn:
            return True
        return not (self.weapon.ego_expires_turn and self.session.turn < self.weapon.ego_expires_turn)

    @property
    def blocked(self) -> bool:
        return self.source.energy < 5

    def calculate_damage(self, source, target, energy=None):
        if energy is None:
            energy = source.energy
        if energy <= 0:
            return 0
        hits = per_cubes(3, 1, energy, target.inbound_accuracy_bonus + source.outbound_accuracy_bonus)
        return 18 if hits else 0

    async def func(self, source: Entity, target: Entity):
        self.weapon.horizontal_cooldown_turn = self.session.turn + 15

        pool = filter_targets(source, Enemies(), self.session.entities)
        if target in pool:
            pool.remove(target)
            targets = [target] + (random.sample(pool, 1) if pool else [])
        else:
            targets = random.sample(pool, min(2, len(pool))) if pool else []

        self.session.say(ls("deluxe.weapon.mimicry.horizontal.charge").format(source.name),
                         source_id=source.id, target_id=target.id)
        if targets:
            self.session.say(
                ls("deluxe.weapon.mimicry.horizontal.warning").format(LocalizedList([t.name for t in targets])),
                source_id=source.id, target_id=target.id)
        self_stun(self.session, source, 1)

        @At(self.session.id, turn=self.session.turn + 1, event=PreDamagesGameEvent)
        async def resolve(context):
            if source.dead:
                return

            payment = await self.publish_energy_payment_event(source, 5)
            source.energy = max(source.energy - payment.energy_payment, 0)

            misses = 0
            for enemy in targets:
                if enemy.dead:
                    continue
                damage = (await self.attack(source, enemy, pay_energy=False)).dealt
                self.weapon.register_damage(damage)
                if damage:
                    enemy.get_state(Bleeding).active = True
                else:
                    misses += 1

            if misses:
                self_stun(self.session, source, min(6, 2 * misses))
