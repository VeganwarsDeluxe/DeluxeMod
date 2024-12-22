import random

from VegansDeluxe.core import EventContext
from VegansDeluxe.core import RangedAttack, RegisterWeapon, Entity, Enemies, AttachedAction, At
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Events import PostDamageGameEvent, PreActionsGameEvent
from VegansDeluxe.core.Session import Session
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import RangedWeapon
from VegansDeluxe.rebuild import DroppedWeapon


@RegisterWeapon
class Boomerang(RangedWeapon):
    id = 'boomerang'
    name = ls("weapon.boomerang.name")
    description = ls("weapon.boomerang.description")

    cubes = 3
    accuracy_bonus = 3
    energy_cost = 3
    damage_bonus = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_turn = 0
        self.turns_until_return = 2
        self.is_thrown = False
        self.throw_energy = 0


@AttachedAction(Boomerang)
class BoomerangAttack(RangedAttack):

    def __init__(self, session: Session, source: Entity, weapon: Boomerang):
        super().__init__(session, source, weapon)

    async def func(self, source: Entity, target: Entity):
        if self.session.turn < self.weapon.return_turn + 1 or self.weapon.is_thrown:
            return

        await self.attack_boomerang(source, target)

    async def attack_boomerang(self, source: Entity, target: Entity):
        if source.energy < self.weapon.energy_cost:
            self.session.say(ls("weapon.boomerang.attack_text_miss").format(source.name, target.name))
            return

        self.weapon.throw_energy = source.energy

        total_damage = self.calculate_damage(source, target)
        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        post_damage = await self.publish_post_damage_event(source, target, total_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        if not total_damage:
            self.session.say(ls("weapon.boomerang.attack_text_miss").format(source.name, target.name))
        else:
            self.session.say(ls("weapon.boomerang.attack_text").format(source.name, target.name, total_damage))

        self.weapon.is_thrown = True
        self.weapon.return_turn = self.session.turn + self.weapon.turns_until_return
        state = source.get_state(DroppedWeapon)
        state.drop_weapon(source)

        @At(self.session.id, turn=self.weapon.return_turn, event=PreActionsGameEvent)
        async def handle_boomerang_return(context: EventContext[PreActionsGameEvent]):
            await self.return_boomerang(source)

    async def return_boomerang(self, source: Entity):
        target_pool = list(filter_targets(source, Enemies(), self.session.entities))
        if not target_pool:
            target_pool = [source]  # Fallback to self-target if no enemies found
        target = random.choice(target_pool)

        total_damage = self.calculate_damage(source, target, self.weapon.throw_energy)

        post_damage = await self.publish_post_damage_event(source, target, total_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        if not total_damage:
            self.session.say(ls("weapon.boomerang.return_text_miss").format(source.name, target.name))
        else:
            self.session.say(ls("weapon.boomerang.return_text").format(source.name, target.name, total_damage))

        self.weapon.is_thrown = False
        self.weapon.throw_energy = 0

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage
