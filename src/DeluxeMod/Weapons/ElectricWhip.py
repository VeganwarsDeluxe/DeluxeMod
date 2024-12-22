import math
import random

from VegansDeluxe.core import RegisterWeapon, Entity, Enemies, AttachedAction, MeleeAttack
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Events import PostDamageGameEvent
from VegansDeluxe.core.Session import Session
from VegansDeluxe.core.Translator.LocalizedList import LocalizedList
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon


@RegisterWeapon
class ElectricWhip(MeleeWeapon):
    id = 'electric_whip'
    name = ls("weapon.electric_whip.name")
    description = ls("weapon.electric_whip.description")

    cubes = 2
    accuracy_bonus = 0
    energy_cost = 2
    damage_bonus = 0


@AttachedAction(ElectricWhip)
class ElectricWhipAttack(MeleeAttack):
    def __init__(self, session: Session, source: Entity, weapon: ElectricWhip):
        super().__init__(session, source, weapon)
        self.targets_count = 3

    async def func(self, source, target):
        base_damage = self.calculate_damage(source, target)
        primary_damage = math.ceil(base_damage)
        secondary_damage = math.ceil(base_damage * 0.5)
        tertiary_damage = math.ceil(base_damage * 0.25)

        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        post_damage = await self.publish_post_damage_event(source, target, primary_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

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

        if primary_damage == 0 and secondary_damage == 0 and tertiary_damage == 0:
            self.session.say(
                ls("weapon.electric_whip.text_miss")
                .format(source.name, target.name)
            )
        else:
            if len(secondary_targets) == 0:
                self.session.say(
                    ls("weapon.electric_whip.single_target_text")
                    .format(source.name, target.name, primary_damage)
                )
            elif len(secondary_targets) == 1:
                secondary_target_name = secondary_targets[0].name
                self.session.say(
                    ls("weapon.electric_whip.multiple_targets_text")
                    .format(
                        source.name,
                        target.name,
                        primary_damage,
                        secondary_target_name,
                        secondary_damage
                    )
                )
            else:
                secondary_targets_name = LocalizedList([t.name for t in secondary_targets[:-1]])
                tertiary_target_name = secondary_targets[-1].name
                self.session.say(
                    ls("weapon.electric_whip.tertiary_targets_text")
                    .format(
                        source.name,
                        target.name,
                        primary_damage,
                        secondary_targets_name,
                        tertiary_target_name,
                        secondary_damage,
                        tertiary_damage
                    )
                )

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage
