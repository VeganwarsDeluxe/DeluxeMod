from VegansDeluxe.core import AttachedAction, RegisterWeapon, percentage_chance
from VegansDeluxe.core import RangedAttack
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import RangedWeapon
from VegansDeluxe.rebuild import Visor

from DeluxeMod.States.Blindness import Blindness


@RegisterWeapon
class StarBow(RangedWeapon):
    id = 'star_bow'
    name = ls("weapon.star_bow.name")
    description = ls("weapon.star_bow.description")

    cubes = 3
    accuracy_bonus = 1
    energy_cost = 3
    damage_bonus = 0


@AttachedAction(StarBow)
class StarBowAttack(RangedAttack):
    async def func(self, source, target):
        damage = await super().attack(source, target)
        if not damage.dealt:
            return damage

        if percentage_chance(75):
            if target.get_state(Visor):
                self.session.say(ls("weapon.star_bow.visor_fail").format(target.name))
                return damage

            blindness = target.get_state(Blindness)
            blindness.blind(self.session)
            self.session.say(ls("weapon.star_bow.effect").format(target.name))

        return damage
