from VegansDeluxe.core import AttachedAction, RegisterWeapon, percentage_chance
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

from DeluxeMod.States.Emptiness import Emptiness


@RegisterWeapon
class AbyssalBlade(MeleeWeapon):
    id = 'abyssal_blade'
    name = ls("weapon.abyssal.blade_name")
    description = ls("weapon.abyssal.blade_description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0


@AttachedAction(AbyssalBlade)
class AbyssalBladeAttack(MeleeAttack):
    async def func(self, source, target):
        damage = await super().attack(source, target)
        if not damage.dealt:
            return damage

        if percentage_chance(45):
            return damage

        emptiness = target.get_state(Emptiness)

        if emptiness.active:
            emptiness.emptiness += 1
            emptiness.triggered = True  # Добавляем новый атрибут для отслеживания изменения
            self.session.say(ls("weapon.abyssal.blade_increase"))
        else:
            emptiness.active = True
            emptiness.triggered = True  # Добавляем новый атрибут для отслеживания активации
            self.session.say(ls("weapon.abyssal.blade_effect").format(target.name))

        return damage
