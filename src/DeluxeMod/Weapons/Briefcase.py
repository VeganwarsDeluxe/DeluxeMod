import math

from VegansDeluxe.core import AttachedAction, MeleeAttack, RegisterWeapon, per_cubes
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

BASE_CUBES = 2
BASE_ACCURACY = 2
BASE_ENERGY = 1
ITEMS_PER_CUBE = 2
ITEMS_PER_ENERGY = 3
ITEMS_PER_ACCURACY_DROP = 3


def item_bonus(source):
    item_count = len(source.items)
    cube_bonus = math.ceil(item_count / ITEMS_PER_CUBE)
    energy_bonus = math.ceil(item_count / ITEMS_PER_ENERGY)
    accuracy_drop = item_count // ITEMS_PER_ACCURACY_DROP
    return cube_bonus, energy_bonus, accuracy_drop


@RegisterWeapon
class Briefcase(MeleeWeapon):
    id = 'briefcase'
    name = ls("deluxe.weapon.briefcase.name")
    description = ls("deluxe.weapon.briefcase.description")

    cubes = BASE_CUBES
    accuracy_bonus = BASE_ACCURACY
    energy_cost = BASE_ENERGY
    damage_bonus = 0


@AttachedAction(Briefcase)
class BriefcaseAttack(MeleeAttack):
    def calculate_damage(self, source, target, energy=None):
        if energy is None:
            energy = source.energy
        if energy <= 0:
            return 0
        cube_bonus, _, accuracy_drop = item_bonus(source)
        cubes = BASE_CUBES + cube_bonus
        accuracy = max(BASE_ACCURACY - accuracy_drop, 0)
        hits = per_cubes(cubes, accuracy, energy, target.inbound_accuracy_bonus + source.outbound_accuracy_bonus)
        return hits if hits else 0

    async def func(self, source, target):
        _, energy_bonus, _ = item_bonus(source)
        energy_cost = BASE_ENERGY + energy_bonus
        damage = (await self.attack(source, target, energy_cost=energy_cost)).dealt
        return damage
