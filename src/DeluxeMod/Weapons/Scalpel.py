from VegansDeluxe.core import AttachedAction, MeleeAttack, RegisterWeapon, per_cubes
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon
from VegansDeluxe.rebuild import Aflame, Bleeding, Injury, Knockdown, Stun, ZombieState

from DeluxeMod.States.Blindness import Blindness
from DeluxeMod.States.CorrosiveMucus import CorrosiveMucus
from DeluxeMod.States.CryoFreeze import CryoFreeze
from DeluxeMod.States.Dehydration import Dehydration
from DeluxeMod.States.Emptiness import Emptiness
from DeluxeMod.States.Hunger import Hunger
from DeluxeMod.States.Mutilation import Mutilation
from DeluxeMod.States.Regeneration import Regeneration
from DeluxeMod.States.Weakness import Weakness
from MothVision.States.Combo import Combo
from MothVision.States.Lobotomized import Lobotomized

EFFECT_CHECKS = [
    (Bleeding, lambda s: s.active),
    (Stun, lambda s: s.stun > 0),
    (Knockdown, lambda s: s.active),
    (Aflame, lambda s: bool(s.flames)),
    (CorrosiveMucus, lambda s: s.active),
    (Weakness, lambda s: s.turns > 0),
    (Dehydration, lambda s: s.active),
    (Mutilation, lambda s: s.active),
    (Emptiness, lambda s: s.active),
    (Hunger, lambda s: s.hunger > 0),
    (CryoFreeze, lambda s: s.freeze > 0),
    (Blindness, lambda s: bool(s.stacks)),
    (Injury, lambda s: s.injury > 0),
    (Lobotomized, lambda s: True),
    (ZombieState, lambda s: s.active),
    (Regeneration, lambda s: s.active),
    (Combo, lambda s: s.duration > 0),
]


def count_active_effects(target) -> int:
    count = 0
    for state_class, is_active in EFFECT_CHECKS:
        state = target.get_state(state_class)
        if state is not None and is_active(state):
            count += 1
    return count


@RegisterWeapon
class Scalpel(MeleeWeapon):
    id = 'scalpel'
    name = ls("deluxe.weapon.scalpel.name")
    description = ls("deluxe.weapon.scalpel.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0


@AttachedAction(Scalpel)
class ScalpelAttack(MeleeAttack):
    def calculate_damage(self, source, target, energy=None):
        if energy is None:
            energy = source.energy
        if energy <= 0:
            return 0
        hits = per_cubes(self.weapon.cubes, self.weapon.accuracy_bonus, energy,
                         target.inbound_accuracy_bonus + source.outbound_accuracy_bonus)
        if not hits:
            return 0
        return hits + count_active_effects(target)
