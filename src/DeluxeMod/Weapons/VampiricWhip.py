import random

from VegansDeluxe.core import AttachedAction, RegisterWeapon
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

from DeluxeMod.States.Dehydration import Dehydration


@RegisterWeapon
class VampiricWhip(MeleeWeapon):
    id = 'vampiric_whip'
    name = ls("weapon.vampiric_whip_name")
    description = ls("weapon.vampiric_whip_description")

    accuracy_bonus = 2
    cubes = 3


@AttachedAction(VampiricWhip)
class VampiricWhipAttack(MeleeAttack):

    async def func(self, source, target):
        damage = await super().attack(source, target)
        if not damage.displayed:
            return

        # Определяем шанс наложения состояния
        if random.randint(0, 100) > 99:
            return

        dehydration = source.get_state(Dehydration)

        if dehydration.active:
            dehydration.dehydration += 1
            dehydration.triggered = True  # Отслеживание изменения
            self.session.say(ls("weapon.vampiric_whip_increase"))
        else:
            dehydration.active = True
            dehydration.triggered = True  # Отслеживание активации
            dehydration.target = target  # Сохраняем цель в состоянии
            self.session.say(ls("weapon.vampiric_whip_effect").format(target.name))
