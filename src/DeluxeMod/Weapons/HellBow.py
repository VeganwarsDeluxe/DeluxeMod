import math
import random

from VegansDeluxe.core import RangedAttack, RegisterWeapon, Entity, Enemies, AttachedAction
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Events import PostDamageGameEvent
from VegansDeluxe.core.Session import Session
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import RangedWeapon


@RegisterWeapon
class HellBow(RangedWeapon):
    id = 'hell_bow'
    name = ls("weapon.hell.bow_name")
    description = ls("weapon.hell.bow_description")

    cubes = 3
    accuracy_bonus = 1
    energy_cost = 3
    damage_bonus = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cooldown_turn = 0


@AttachedAction(HellBow)
class HellBowAttack(RangedAttack):
    pass


@AttachedAction(HellBow)
class ExplosionArrow(RangedAttack):
    id = 'explosion_arrow'
    name = ls("weapon.hell.bow_explosion_arrow_name")
    target_type = Enemies()

    def __init__(self, session: Session, source: Entity, weapon: HellBow):
        super().__init__(session, source, weapon)
        self.targets_count = 10

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.cooldown_turn

    async def func(self, source: Entity, target: Entity):
        if self.hidden:
            return

        # Уменьшение энергии
        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        self.weapon.cooldown_turn = self.session.turn + 13

        self.weapon.damage_bonus = 1
        primary_damage = self.calculate_damage(source, target)
        secondary_damage = math.ceil(primary_damage * 0.5)

        post_damage = await self.publish_post_damage_event(source, target, primary_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        # Выбор второстепенных целей
        targets = [target]
        secondary_targets = []
        while len(targets) < self.targets_count:
            target_pool = list(filter(lambda t: t not in targets,
                                      filter_targets(source, Enemies(), self.session.entities)
                                      ))
            if not target_pool:
                break
            selected_target = random.choice(target_pool)
            post_damage = await self.publish_post_damage_event(source, selected_target, secondary_damage)
            selected_target.inbound_dmg.add(source, post_damage, self.session.turn)
            source.outbound_dmg.add(selected_target, post_damage, self.session.turn)
            secondary_targets.append(selected_target)
            targets.append(selected_target)

        if primary_damage == 0 and secondary_damage == 0:
            self.session.say(
                ls("weapon.hell.bow_explosion_arrow_text_miss")
                .format(source.name, target.name)
            )
        else:
            if len(secondary_targets) == 0:
                self.session.say(
                    ls("weapon.hell.bow_explosion_arrow_single_target_text")
                    .format(source.name, target.name, primary_damage)
                )
            else:
                secondary_targets_names = ', '.join([t.name for t in secondary_targets])
                self.session.say(
                    ls("weapon.hell.bow_explosion_arrow_multiple_targets_text")
                    .format(
                        source.name,
                        target.name,
                        primary_damage,
                        secondary_targets_names,
                        secondary_damage
                    )
                )

        self.weapon.damage_bonus = 0

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage
