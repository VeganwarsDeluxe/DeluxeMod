from VegansDeluxe.core import AttachedAction, RegisterWeapon, percentage_chance
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

from DeluxeMod.States.Emptiness import Emptiness


@RegisterWeapon
class AbyssalBlade(MeleeWeapon):
    id = 'abyssal_blade'
    name = ls("deluxe.weapon.abyssal.blade_name")
    description = ls("deluxe.weapon.abyssal.blade_description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0


@AttachedAction(AbyssalBlade)
class AbyssalBladeAttack(MeleeAttack):
    async def func(self, source, target):
        damage = await super().attack(source, target)
        if not damage.calculated:
            return damage

        if percentage_chance(45):
            return damage

        emptiness = target.get_state(Emptiness)

        if emptiness.active:
            emptiness.emptiness += 1
            emptiness.triggered = True  # Добавляем новый атрибут для отслеживания изменения
            self.session.say(ls("deluxe.weapon.abyssal.blade_increase"), source_id=source.id, target_id=target.id)
        else:
            emptiness.active = True
            emptiness.triggered = True  # Добавляем новый атрибут для отслеживания активации
            self.session.say(ls("deluxe.weapon.abyssal.blade_effect").format(target.name), source_id=source.id, target_id=target.id)

        return damage
