from VegansDeluxe.core import EventContext, DamageData, RegisterEvent, PreMoveGameEvent
from VegansDeluxe.core import PostActionsGameEvent
from VegansDeluxe.core import PostDamageGameEvent
from VegansDeluxe.core import RangedAttack, RegisterWeapon, Entity, AttachedAction
from VegansDeluxe.core.Session import Session
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import RangedWeapon


@RegisterWeapon
class NeedleFan(RangedWeapon):
    id = 'needle_fan'
    name = ls("weapon.needle_fan.name")
    description = ls("weapon.needle_fan.description")

    cubes = 2
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_needles = 1
        self.max_needles = 4

        @RegisterEvent(self.session_id, event=PostActionsGameEvent)
        async def handle_needle_recovery(context: EventContext[PostActionsGameEvent]):
            if self.current_needles < self.max_needles:
                self.current_needles += 1

        @RegisterEvent(self.session_id, event=PreMoveGameEvent)
        async def pre_move(context: EventContext[PreMoveGameEvent]):
            source = context.session.get_entity(self.entity_id)
            source.notifications.append(
                ls("weapon.needle_fan.notification").format(self.current_needles)
            )


@AttachedAction(NeedleFan)
class NeedleFanAttack(RangedAttack):
    def __init__(self, session: Session, source: Entity, weapon: NeedleFan):
        super().__init__(session, source, weapon)

    async def attack(self, source: Entity, target, pay_energy=True) -> DamageData:
        """
        Actually performs attack on target, dealing damage.
        """
        calculated_damage = self.calculate_damage(source, target)
        if pay_energy:
            source.energy = max(source.energy - self.weapon.energy_cost, 0)

        if self.weapon.current_needles > 0:
            used_needles = self.weapon.current_needles
            calculated_damage = calculated_damage * used_needles
            self.weapon.current_needles = 0
        else:
            target = target if target in source.nearby_entities else source

        displayed_damage = await self.publish_attack_event(source, target, calculated_damage)
        self.send_attack_message(source, target, displayed_damage)
        dealt_damage = await self.publish_post_attack_event(source, target, displayed_damage)

        target.inbound_dmg.add(source, dealt_damage, self.session.turn)
        source.outbound_dmg.add(target, dealt_damage, self.session.turn)
        return DamageData(calculated_damage, displayed_damage, dealt_damage)

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage
