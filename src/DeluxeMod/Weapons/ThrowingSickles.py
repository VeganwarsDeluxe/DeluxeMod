from VegansDeluxe.core import At
from VegansDeluxe.core import AttachedAction
from VegansDeluxe.core import Entity
from VegansDeluxe.core import EventContext
from VegansDeluxe.core import PreMoveGameEvent
from VegansDeluxe.core import RegisterEvent
from VegansDeluxe.core import RegisterWeapon
from VegansDeluxe.core import SelfOnly
from VegansDeluxe.core import percentage_chance
from VegansDeluxe.core.Actions.WeaponAction import DecisiveWeaponAction
from VegansDeluxe.core.Session import Session
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import RangedWeapon
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core import RangedAttack


@RegisterWeapon
class ThrowingSickles(RangedWeapon):
    id = 'throwing_sickles'
    name = ls("weapon.throwing_sickles.name")
    description = ls("weapon.throwing_sickles.description")

    ranged = False
    cubes = 3
    accuracy_bonus = 0
    energy_cost = 3
    damage_bonus = 0

    max_sickles = 2
    melee_accuracy_bonus = 1
    melee_energy_cost = 2
    double_melee_energy_cost = 3
    double_melee_chance = 20

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.held_sickles = self.max_sickles
        self.dropped_sickles = 0

        @RegisterEvent(self.session_id, event=PreMoveGameEvent)
        async def pre_move(context: EventContext[PreMoveGameEvent]):
            source = context.session.get_entity(self.entity_id)
            if not source:
                return
            source.notifications.append(
                ls("weapon.throwing_sickles.notification").format(self.held_sickles, self.dropped_sickles)
            )


@AttachedAction(ThrowingSickles)
class ThrowingSicklesMeleeAttack(MeleeAttack):
    name = ls("weapon.throwing_sickles.melee.name")

    async def func(self, source: Entity, target: Entity):
        original_cubes = self.weapon.cubes
        original_accuracy_bonus = self.weapon.accuracy_bonus
        original_energy_cost = self.weapon.energy_cost

        self.weapon.cubes = 3
        self.weapon.accuracy_bonus = self.weapon.melee_accuracy_bonus
        self.weapon.energy_cost = self.weapon.melee_energy_cost

        try:
            if (
                    self.weapon.held_sickles >= 2
                    and source.energy >= self.weapon.double_melee_energy_cost
                    and percentage_chance(self.weapon.double_melee_chance)
            ):
                throw_energy = source.energy
                self.weapon.energy_cost = self.weapon.double_melee_energy_cost
                first_damage = await self.attack(source, target)
                paid_energy = source.energy
                source.energy = throw_energy
                second_damage = await self.attack(source, target, pay_energy=False)
                source.energy = paid_energy
                self.session.say(ls("weapon.throwing_sickles.double_melee_text").format(source.name, target.name))
                return second_damage if second_damage.dealt else first_damage

            return await self.attack(source, target)
        finally:
            self.weapon.cubes = original_cubes
            self.weapon.accuracy_bonus = original_accuracy_bonus
            self.weapon.energy_cost = original_energy_cost


@AttachedAction(ThrowingSickles)
class ThrowSickle(RangedAttack):
    id = 'throw_sickle'
    name = ls("weapon.throwing_sickles.throw.name")

    @property
    def hidden(self) -> bool:
        return self.weapon.held_sickles <= 0

    async def func(self, source: Entity, target: Entity):
        original_cubes = self.weapon.cubes
        original_accuracy_bonus = self.weapon.accuracy_bonus
        original_energy_cost = self.weapon.energy_cost

        self.weapon.cubes = 3
        self.weapon.accuracy_bonus = 0
        self.weapon.energy_cost = 3

        self.weapon.held_sickles -= 1
        try:
            damage = await self.attack(source, target)
        finally:
            self.weapon.cubes = original_cubes
            self.weapon.accuracy_bonus = original_accuracy_bonus
            self.weapon.energy_cost = original_energy_cost

        if damage.calculated:
            self.weapon.dropped_sickles += 1
            self.session.say(ls("weapon.throwing_sickles.dropped_text").format(source.name))
            return damage

        @At(self.session.id, turn=self.session.turn + 1, event=PreMoveGameEvent)
        async def return_sickle(context: EventContext[PreMoveGameEvent]):
            owner = context.session.get_entity(self.weapon.entity_id)
            if not owner or not isinstance(owner.weapon, ThrowingSickles):
                return
            self.weapon.held_sickles = min(self.weapon.held_sickles + 1, self.weapon.max_sickles)
            context.session.say(ls("weapon.throwing_sickles.return_text").format(owner.name))

        return damage


@AttachedAction(ThrowingSickles)
class PickUpSickle(DecisiveWeaponAction):
    id = 'pick_up_sickle'
    name = ls("weapon.throwing_sickles.pickup.name")
    target_type = SelfOnly()

    @property
    def hidden(self) -> bool:
        return self.weapon.dropped_sickles <= 0 or self.weapon.held_sickles >= self.weapon.max_sickles

    async def func(self, source: Entity, target: Entity):
        self.weapon.dropped_sickles -= 1
        self.weapon.held_sickles = min(self.weapon.held_sickles + 1, self.weapon.max_sickles)
        self.session.say(ls("weapon.throwing_sickles.pickup.text").format(source.name))
