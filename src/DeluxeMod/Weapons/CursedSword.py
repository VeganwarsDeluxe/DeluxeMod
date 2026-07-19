from VegansDeluxe.core import AttachedAction, RegisterWeapon, percentage_chance
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

from DeluxeMod.States.Weakness import Weakness


@RegisterWeapon
class CursedSword(MeleeWeapon):
    id = 'cursed_sword'
    name = ls("weapon.cursed_sword.name")
    description = ls("weapon.cursed_sword.description")

    accuracy_bonus = 2
    cubes = 3


@AttachedAction(CursedSword)
class CursedSwordAttack(MeleeAttack):
    async def func(self, source, target):
        attack = await super().attack(source, target)
        damage = attack.dealt
        if not damage:
            return damage

        if percentage_chance(40):
            weakness = target.get_state(Weakness)

            message_key = "weapon.cursed_sword.increase" if weakness.turns else "weapon.cursed_sword.effect"
            weakness.apply(self.session)
            self.session.say(ls(message_key).format(target.name, weakness.turns))

        return damage
