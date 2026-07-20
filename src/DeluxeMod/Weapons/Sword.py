from VegansDeluxe.core import AttachedAction, MeleeAttack, RegisterWeapon
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon


@RegisterWeapon
class Sword(MeleeWeapon):
    id = "deluxe_sword"
    name = ls("weapon.sword.name")
    description = ls("weapon.sword.description")

    cubes = 3
    energy_cost = 2
    accuracy_bonus = 2


@AttachedAction(Sword)
class SwordAttack(MeleeAttack):
    pass
