from VegansDeluxe.core import ActionTag, Allies, At, AttachedAction, DecisiveWeaponAction, Entity, EventContext, \
    MeleeAttack, PostAttackGameEvent, PostDamageGameEvent, PostDamagesGameEvent, PostTickGameEvent, \
    PreActionsGameEvent, PreDamagesGameEvent, PreMoveGameEvent, RegisterEvent, RegisterWeapon, Session, \
    per_cubes, percentage_chance
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon
from VegansDeluxe.rebuild import Stun

BASE_CUBES = 3
COMBO_DURATION = 3
RELOAD_ENERGY_DRAIN = 3
SPECIAL_COOLDOWN = 6
UPPERCUT_ENERGY = 1
BARRAGE_ENERGY = 1
STUN_CHANCE_PER_STACK = 10
BLOCK_ENERGY_REWARD = 2


def delayed_stun(session: Session, entity: Entity, turns: int):
    @At(session.id, turn=session.turn + 1, event=PreMoveGameEvent)
    async def apply(context):
        entity.get_state(Stun).stun += turns


@RegisterWeapon
class TurboGloves(MeleeWeapon):
    id = 'turbo_gloves'
    name = ls("deluxe.weapon.turbo_gloves.name")
    description = ls("deluxe.weapon.turbo_gloves.description")

    cubes = BASE_CUBES
    accuracy_bonus = 2
    energy_cost = 2

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.combo_stacks = 0
        self.combo_duration = 0
        self.applied_bonus = 0
        self.boosted_weapon = None
        self.last_target = None

        self.uppercut_cooldown_turn = 0
        self.barrage_cooldown_turn = 0

        @RegisterEvent(session_id, event=PreActionsGameEvent)
        async def apply_combo_bonus(context: EventContext[PreActionsGameEvent]):
            entity = context.session.get_entity(entity_id)
            if not entity:
                return

            if self.boosted_weapon is not None and self.boosted_weapon is not entity.weapon:
                self.boosted_weapon.cubes -= self.applied_bonus
                self.applied_bonus = 0
                self.boosted_weapon = None

            desired = (1 + self.combo_stacks // 2) if self.combo_duration > 0 else 0
            if desired != self.applied_bonus:
                entity.weapon.cubes += desired - self.applied_bonus
                self.applied_bonus = desired
                self.boosted_weapon = entity.weapon if desired else None

        @RegisterEvent(session_id, event=PostTickGameEvent)
        async def tick(context: EventContext[PostTickGameEvent]):
            entity = context.session.get_entity(entity_id)
            if not entity or self.combo_duration <= 0:
                return

            entity.energy = min(entity.energy + 1, entity.max_energy)
            self.combo_duration -= 1
            if self.combo_duration <= 0:
                if self.boosted_weapon is not None:
                    self.boosted_weapon.cubes -= self.applied_bonus
                    self.applied_bonus = 0
                    self.boosted_weapon = None
                context.session.say(
                    ls("deluxe.weapon.turbo_gloves.combo_end").format(entity.name, self.combo_stacks),
                    source_id=entity_id, target_id=entity_id)
                self.combo_stacks = 0

        @RegisterEvent(session_id, event=PostAttackGameEvent)
        async def assist_combo(context: EventContext[PostAttackGameEvent]):
            if self.last_target is None or context.event.target != self.last_target:
                return
            if context.event.source.id == entity_id:
                return
            if not context.event.damage:
                return

            entity = context.session.get_entity(entity_id)
            if entity and not entity.dead:
                self.trigger_combo(context.session, entity)

    def trigger_combo(self, session: Session, source: Entity):
        was_active = self.combo_duration > 0
        self.combo_stacks += 1
        self.combo_duration = COMBO_DURATION

        if was_active:
            session.say(ls("deluxe.weapon.turbo_gloves.combo_continue").format(source.name, self.combo_stacks),
                        source_id=source.id, target_id=source.id)
        else:
            session.say(ls("deluxe.weapon.turbo_gloves.combo_start").format(source.name),
                        source_id=source.id, target_id=source.id)


@AttachedAction(TurboGloves)
class TurboGlovesAttack(MeleeAttack):
    priority = -1

    def __init__(self, session: Session, source: Entity, weapon: TurboGloves):
        super().__init__(session, source, weapon)
        self.weapon: TurboGloves = weapon

    async def func(self, source, target):
        self.weapon.last_target = target
        damage = (await self.attack(source, target)).dealt

        if damage:
            self.weapon.trigger_combo(self.session, source)

            @At(self.session.id, turn=self.session.turn, event=PreDamagesGameEvent)
            async def check_reload(context: EventContext[PreDamagesGameEvent]):
                for action in context.action_manager.get_queued_entity_actions(self.session, target):
                    if ActionTag.RELOAD in action.tags:
                        self.session.say(ls("deluxe.weapon.turbo_gloves.reload_punish").format(target.name),
                                         source_id=source.id, target_id=target.id)
                        target.energy = max(target.energy - RELOAD_ENERGY_DRAIN, 0)
                        break

        return damage


@AttachedAction(TurboGloves)
class Uppercut(MeleeAttack):
    id = 'uppercut'
    name = ls("deluxe.weapon.turbo_gloves.uppercut.name")

    def __init__(self, session: Session, source: Entity, weapon: TurboGloves):
        super().__init__(session, source, weapon)
        self.weapon: TurboGloves = weapon

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.uppercut_cooldown_turn

    @property
    def blocked(self) -> bool:
        return self.source.energy < UPPERCUT_ENERGY

    def calculate_damage(self, source, target, energy=None):
        if energy is None:
            energy = source.energy
        if energy <= 0:
            return 0
        cubes = BASE_CUBES + self.weapon.combo_stacks
        hits = per_cubes(cubes, self.weapon.accuracy_bonus, energy,
                         target.inbound_accuracy_bonus + source.outbound_accuracy_bonus)
        return hits if hits else 0

    async def func(self, source: Entity, target: Entity):
        self.weapon.uppercut_cooldown_turn = self.session.turn + SPECIAL_COOLDOWN
        self.weapon.last_target = target
        stacks = self.weapon.combo_stacks

        damage = (await self.attack(source, target, energy_cost=UPPERCUT_ENERGY)).dealt
        if damage and stacks and percentage_chance(min(100, STUN_CHANCE_PER_STACK * stacks)):
            delayed_stun(self.session, target, 1)
            self.session.say(ls("deluxe.weapon.turbo_gloves.uppercut.stun").format(source.name, target.name),
                             source_id=source.id, target_id=target.id)

        return damage


@AttachedAction(TurboGloves)
class PunchBarrage(MeleeAttack):
    id = 'punch_barrage'
    name = ls("deluxe.weapon.turbo_gloves.barrage.name")

    def __init__(self, session: Session, source: Entity, weapon: TurboGloves):
        super().__init__(session, source, weapon)
        self.weapon: TurboGloves = weapon

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.barrage_cooldown_turn

    @property
    def blocked(self) -> bool:
        return self.source.energy < BARRAGE_ENERGY

    def calculate_damage(self, source, target, energy=None):
        if energy is None:
            energy = source.energy
        if energy <= 0:
            return 0
        hits = per_cubes(2, self.weapon.accuracy_bonus, energy,
                         target.inbound_accuracy_bonus + source.outbound_accuracy_bonus)
        return hits if hits else 0

    async def func(self, source: Entity, target: Entity):
        self.weapon.barrage_cooldown_turn = self.session.turn + SPECIAL_COOLDOWN
        self.weapon.last_target = target
        punches = self.weapon.combo_stacks

        payment = await self.publish_energy_payment_event(source, BARRAGE_ENERGY)
        source.energy = max(source.energy - payment.energy_payment, 0)

        self.session.say(ls("deluxe.weapon.turbo_gloves.barrage.text").format(source.name, target.name, punches),
                         source_id=source.id, target_id=target.id)

        total = 0
        for _ in range(punches):
            if target.dead:
                break
            dealt = (await self.attack(source, target, pay_energy=False)).dealt
            total += dealt

        return total


@AttachedAction(TurboGloves)
class Block(DecisiveWeaponAction):
    id = 'block'
    name = ls("deluxe.weapon.turbo_gloves.block.name")
    target_type = Allies()
    priority = -4

    def __init__(self, session: Session, source: Entity, weapon: TurboGloves):
        super().__init__(session, source, weapon)
        self.weapon: TurboGloves = weapon

    @property
    def hidden(self) -> bool:
        return self.weapon.combo_stacks <= 0

    async def func(self, source, target):
        if target == source:
            self.session.say(ls("deluxe.weapon.turbo_gloves.block.text").format(source.name),
                             source_id=source.id, target_id=target.id)
        else:
            self.session.say(ls("deluxe.weapon.turbo_gloves.block.text_targeted").format(source.name, target.name),
                             source_id=source.id, target_id=target.id)

        blocked = False

        @At(self.session.id, turn=self.session.turn, event=PostDamageGameEvent,
            filters=[lambda event: event.target == target])
        async def block_hit(context: EventContext[PostDamageGameEvent]):
            nonlocal blocked
            if blocked or not context.event.damage:
                return
            blocked = True
            context.event.damage = 0
            self.session.say(ls("deluxe.weapon.turbo_gloves.block.effect").format(target.name),
                             source_id=source.id, target_id=target.id)
            self.weapon.trigger_combo(self.session, source)
            target.energy = min(target.energy + BLOCK_ENERGY_REWARD, target.max_energy)

        @At(self.session.id, turn=self.session.turn, event=PostDamagesGameEvent)
        async def check_vain(context: EventContext[PostDamagesGameEvent]):
            if blocked:
                return
            self.weapon.combo_stacks = 0
            self.weapon.combo_duration = 0
            self.session.say(ls("deluxe.weapon.turbo_gloves.block.vain").format(source.name),
                             source_id=source.id, target_id=target.id)
