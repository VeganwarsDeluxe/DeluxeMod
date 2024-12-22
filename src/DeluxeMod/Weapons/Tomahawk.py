from VegansDeluxe.core import AttachedAction, RegisterWeapon
from VegansDeluxe.core import Enemies
from VegansDeluxe.core import Entity
from VegansDeluxe.core import MeleeAttack, RangedAttack
from VegansDeluxe.core import PostDamageGameEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

from VegansDeluxe.rebuild import DroppedWeapon


@RegisterWeapon
class Tomahawk(MeleeWeapon):
    id = 'tomahawk'
    name = ls("weapon.tomahawk.name")
    description = ls("weapon.tomahawk.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cooldown_turn = 0


@AttachedAction(Tomahawk)
class TomahawkAttack(MeleeAttack):
    pass


@AttachedAction(Tomahawk)
class TomahawkThrow(RangedAttack):
    id = 'tomahawk_throw'
    name = ls("weapon.tomahawk.throw_name")
    target_type = Enemies()

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.cooldown_turn

    def __init__(self, session: Session, source: Entity, weapon: Tomahawk):
        super().__init__(session, source, weapon)

    async def func(self, source: Entity, target: Entity):
        self.weapon.damage_bonus = 2
        total_damage = self.calculate_damage(source, target)
        self.weapon.cooldown_turn = self.session.turn + 5

        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        post_damage = await self.publish_post_damage_event(source, target, total_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        if not total_damage:
            self.session.say(
                ls("weapon.tomahawk.throw_text_miss")
                .format(source.name, target.name)
            )
        else:
            self.session.say(
                ls("weapon.tomahawk.throw_text").format(source.name, target.name, total_damage)
            )

        state = source.get_state(DroppedWeapon)
        state.drop_weapon(source)

        self.weapon.damage_bonus = 0

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage
