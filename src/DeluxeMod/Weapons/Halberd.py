from VegansDeluxe.core import MeleeAttack, Session
from VegansDeluxe.core import RegisterWeapon, Entity, AttachedAction, percentage_chance
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon


@RegisterWeapon
class Halberd(MeleeWeapon):
    id = 'halberd'
    name = ls("weapon.halberd.name")
    description = ls("weapon.halberd.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0


@AttachedAction(Halberd)
class HalberdAttack(MeleeAttack):
    def __init__(self, session: Session, source: Entity, weapon: Halberd):
        super().__init__(session, source, weapon)
        self.attack_count = 0

    async def func(self, source, target):
        self.attack_count += 1

        if self.attack_count % 3 == 0:
            if percentage_chance(99):
                self.weapon.damage *= 2
                self.session.say(ls("weapon.halberd.attack.critical").format(source.name, target.name,
                                                                             self.weapon.damage))

        await super().func(source, target)

        if self.attack_count % 3 == 0:
            self.attack_count = 0
