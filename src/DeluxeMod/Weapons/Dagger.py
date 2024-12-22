import random

from VegansDeluxe.core import AttachedAction, RegisterWeapon
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

from DeluxeMod.States.Mutilation import Mutilation


@RegisterWeapon
class Dagger(MeleeWeapon):
    id = 'dagger'
    name = ls("weapon.dagger.name")
    description = ls("weapon.dagger.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0


@AttachedAction(Dagger)
class DaggerAttack(MeleeAttack):
    async def func(self, source, target):
        damage = (await super().attack(source, target)).dealt
        if not damage:
            return damage

        if random.randint(0, 100) > 99:
            return damage

        mutilation = target.get_state(Mutilation)

        if mutilation.active:
            mutilation.mutilation += 1
            mutilation.triggered = True  # Set triggered to True when mutilation increases
            self.session.say(ls("weapon.dagger.increase").format(target.name))
        else:
            mutilation.active = True
            mutilation.triggered = True  # Set triggered to True when mutilation activates
            self.session.say(ls("weapon.dagger.effect").format(target.name))
        return damage
