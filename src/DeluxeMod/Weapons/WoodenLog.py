from VegansDeluxe.core import AttachedAction, RegisterWeapon, percentage_chance
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon
from VegansDeluxe.rebuild import Knockdown

KNOCK_TARGET_CHANCE = 35
KNOCK_SELF_ON_MISS_CHANCE = 50


@RegisterWeapon
class WoodenLog(MeleeWeapon):
    id = 'wooden_log'
    name = ls("deluxe.weapon.wooden_log.name")
    description = ls("deluxe.weapon.wooden_log.description")

    cubes = 4
    accuracy_bonus = 0
    damage_bonus = 1
    energy_cost = 3


@AttachedAction(WoodenLog)
class WoodenLogAttack(MeleeAttack):
    async def func(self, source, target):
        damage = (await self.attack(source, target)).dealt

        if damage:
            if percentage_chance(KNOCK_TARGET_CHANCE):
                target.get_state(Knockdown).active = True
                self.session.say(ls("deluxe.weapon.wooden_log.knockdown").format(source.name, target.name),
                                 source_id=source.id, target_id=target.id)
        else:
            if percentage_chance(KNOCK_SELF_ON_MISS_CHANCE):
                source.get_state(Knockdown).active = True
                self.session.say(ls("deluxe.weapon.wooden_log.stumble").format(source.name),
                                 source_id=source.id, target_id=source.id)

        return damage
