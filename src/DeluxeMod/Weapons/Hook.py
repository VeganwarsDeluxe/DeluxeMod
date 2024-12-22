from VegansDeluxe.core import Enemies
from VegansDeluxe.core import MeleeAttack, Session
from VegansDeluxe.core import RangedAttack, RegisterWeapon, Entity, AttachedAction, PostDamageGameEvent
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon


@RegisterWeapon
class Hook(MeleeWeapon):
    id = 'hook'
    name = ls("weapon.hook.name")
    description = ls("weapon.hook.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cooldown_turn = 0


@AttachedAction(Hook)
class HookAttack(MeleeAttack):
    pass


@AttachedAction(Hook)
class HookAttract(RangedAttack):
    id = 'hook_attract'
    name = ls("weapon.hook.attract.name")
    target_type = Enemies()

    def __init__(self, session: Session, source: Entity, weapon: Hook):
        super().__init__(session, source, weapon)

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.cooldown_turn

    async def func(self, source: Entity, target: Entity):

        self.weapon.damage_bonus = 1
        total_damage = self.calculate_damage(source, target)

        # Уменьшение энергии
        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        self.weapon.cooldown_turn = self.session.turn + 3

        # Притягиваем цель к себе
        if source not in target.nearby_entities:
            target.nearby_entities.append(source)

        if target not in source.nearby_entities:
            source.nearby_entities.append(target)

        # Притянутые цели видят друг друга
        for entity in source.nearby_entities:
            if entity != target and target not in entity.nearby_entities:
                entity.nearby_entities.append(target)
            if entity != target and entity not in target.nearby_entities:
                target.nearby_entities.append(entity)

        post_damage = await self.publish_post_damage_event(source, target, total_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        if not total_damage:
            self.session.say(
                ls("weapon.hook.attract.miss")
                .format(source.name, target.name)
            )
        else:
            self.session.say(
                ls("weapon.hook.attract.text").format(source.name, target.name, total_damage)
            )

        self.weapon.damage_bonus = 0

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage
