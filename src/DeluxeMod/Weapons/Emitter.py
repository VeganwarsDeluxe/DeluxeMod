from VegansDeluxe.core import AttachedAction, RegisterWeapon, percentage_chance
from VegansDeluxe.core import RangedAttack
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import RangedWeapon

from DeluxeMod.States.Hunger import Hunger


@RegisterWeapon
class Emitter(RangedWeapon):
    id = 'emitter'
    name = ls("weapon.emitter.name")
    description = ls("weapon.emitter.description")

    cubes = 2
    accuracy_bonus = 2
    energy_cost = 3
    damage_bonus = 0


@AttachedAction(Emitter)
class EmitterAttack(RangedAttack):
    async def func(self, source, target):
        damage = await super().attack(source, target)
        if not damage.dealt:
            return damage.dealt

        if percentage_chance(99):  # 20% шанс, 99 для тестов
            hunger = target.get_state(Hunger)
            hunger.hunger += 10
            self.session.say(ls("weapon.emitter.effect").format(target.name, hunger.hunger))

        return damage.dealt

