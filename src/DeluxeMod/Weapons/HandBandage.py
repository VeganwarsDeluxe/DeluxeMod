from VegansDeluxe.core import AttachedAction, RegisterWeapon
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

from DeluxeMod.States.Combo import Combo


@RegisterWeapon
class HandBandage(MeleeWeapon):
    id = 'hand_bandage'
    name = ls("deluxe.weapon.hand_bandage.name")
    description = ls("deluxe.weapon.hand_bandage.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2


@AttachedAction(HandBandage)
class HandBandageAttack(MeleeAttack):
    async def func(self, source, target):
        damage = await self.attack(source, target)
        if not damage.dealt:
            return damage

        source.get_state(Combo).trigger(self.session, source)

        return damage
