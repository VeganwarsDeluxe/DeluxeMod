from VegansDeluxe.core import AttachedAction, RegisterWeapon, At, percentage_chance, RegisterEvent, PreMoveGameEvent, \
    DecisiveWeaponAction
from VegansDeluxe.core import MeleeAttack, PostTickGameEvent, Entity, PostDamageGameEvent
from VegansDeluxe.core import OwnOnly, EventContext
from VegansDeluxe.core.Session import Session
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon


@RegisterWeapon
class Chainsaw(MeleeWeapon):
    id = 'chainsaw'
    name = ls("weapon.chainsaw.name")
    description = ls("weapon.chainsaw.description")

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.wound_up = False
        self.cooldown_turn = 0

        @RegisterEvent(self.session_id, event=PreMoveGameEvent)
        async def pre_move(context: EventContext[PreMoveGameEvent]):
            if not self.wound_up:
                return
            source = context.session.get_entity(self.entity_id)
            source.notifications.append(
                ls("weapon.chainsaw.active").format(self.cooldown_turn - context.session.turn)
            )

    def reset_stats(self):
        self.cubes = 2
        self.energy_cost = 2
        self.accuracy_bonus = 2
        self.damage_bonus = 0


@AttachedAction(Chainsaw)
class ChainsawAttack(MeleeAttack):

    def __init__(self, session: Session, source: Entity, weapon: Chainsaw):
        super().__init__(session, source, weapon)

    async def func(self, source: Entity, target: Entity):
        if percentage_chance(5):
            self.session.say(ls("weapon.chainsaw.jammed").format(source.name))
            self.weapon.wound_up = False
            self.weapon.reset_stats()
            return

        if not self.weapon.wound_up:
            self.weapon.reset_stats()
        else:
            self.weapon.cubes = 3
            self.weapon.damage_bonus = 1
            self.weapon.accuracy_bonus = 2
            self.weapon.energy_cost = 2

        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        total_damage = self.calculate_damage(source, target)

        post_damage = await self.publish_post_damage_event(source, target, total_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        if not total_damage:
            self.session.say(
                self.MISS_MESSAGE.format(source_name=source.name, attack_text=self.ATTACK_TEXT, target_name=target.name,
                                         weapon_name=self.weapon.name)
            )
        else:
            self.session.say(
                self.ATTACK_MESSAGE.format(attack_emoji=self.ATTACK_EMOJI, source_name=source.name,
                                           attack_text=self.ATTACK_TEXT,
                                           target_name=target.name, weapon_name=self.weapon.name, damage=total_damage)
            )

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage


@AttachedAction(Chainsaw)
class WoundUpChainsaw(DecisiveWeaponAction):
    id = 'wound_up_chainsaw'
    target_type = OwnOnly()
    priority = -10

    @property
    def hidden(self) -> bool:
        return self.weapon.wound_up

    @property
    def name(self):
        return ls("weapon.chainsaw.enable_name")

    async def func(self, source, target):
        self.weapon.wound_up = True
        self.weapon.cooldown_turn = self.session.turn + 4

        self.session.say(ls("weapon.chainsaw.switch_text").format(source.name))

        @At(self.session.id, turn=self.weapon.cooldown_turn, event=PostTickGameEvent)
        async def disable_chainsaw(context: EventContext[PostTickGameEvent]):
            self.weapon.wound_up = False
            self.weapon.reset_stats()
            context.session.say(ls("weapon.chainsaw.disable_text").format(source.name))
