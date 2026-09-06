from VegansDeluxe.core import At, AttachedAction, Enemies, Entity, EventContext, MeleeAttack, PreMoveGameEvent, \
    RegisterWeapon, Session, per_cubes, percentage_chance
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon
from VegansDeluxe.rebuild import Armor, Knockdown, Stun

CHARGE_ENERGY = 1
CHARGE_COOLDOWN = 5
CHARGE_DAMAGE_BONUS = 1
STUN_CHANCE = 50
KNOCKDOWN_CHANCE = 50
STUN_DURATION = 1
ARMOR_CHANCE = 50
ARMOR_VALUE = 2


def delayed_stun(session: Session, entity: Entity, turns: int):
    @At(session.id, turn=session.turn + 1, event=PreMoveGameEvent)
    async def apply(context):
        entity.get_state(Stun).stun += turns


def maybe_grant_armor(session: Session, source: Entity):
    if not percentage_chance(ARMOR_CHANCE):
        return
    source.get_state(Armor).add(ARMOR_VALUE, 100)
    session.say(ls("deluxe.weapon.horn.armor").format(source.name), source_id=source.id, target_id=source.id)


def calculate_horn_damage(weapon, session, source, target, energy, extra_bonus=0):
    if energy is None:
        energy = source.energy
    if energy <= 0:
        return 0
    enemy_count = len([e for e in session.entities if not source.is_ally(e) and not e.dead])
    damage = per_cubes(weapon.cubes, weapon.accuracy_bonus, energy,
                       target.inbound_accuracy_bonus + source.outbound_accuracy_bonus)
    if not damage:
        return 0
    damage += enemy_count + extra_bonus
    if target.get_state(Stun).stun > 0:
        damage *= 2
    return damage


@RegisterWeapon
class Horn(MeleeWeapon):
    id = 'horn'
    name = ls("deluxe.weapon.horn.name")
    description = ls("deluxe.weapon.horn.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 1
    damage_bonus = 0

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.charge_cooldown_turn = 0


@AttachedAction(Horn)
class HornAttack(MeleeAttack):
    def __init__(self, session: Session, source: Entity, weapon: Horn):
        super().__init__(session, source, weapon)
        self.weapon: Horn = weapon

    def calculate_damage(self, source, target, energy=None):
        return calculate_horn_damage(self.weapon, self.session, source, target, energy)

    async def func(self, source, target):
        damage = (await self.attack(source, target)).dealt
        if damage:
            maybe_grant_armor(self.session, source)
        return damage


@AttachedAction(Horn)
class Charge(MeleeAttack):
    id = 'charge'
    name = ls("deluxe.weapon.horn.charge.name")
    target_type = Enemies()

    def __init__(self, session: Session, source: Entity, weapon: Horn):
        super().__init__(session, source, weapon)
        self.weapon: Horn = weapon

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.charge_cooldown_turn

    @property
    def blocked(self) -> bool:
        return self.source.energy < CHARGE_ENERGY

    def calculate_damage(self, source, target, energy=None):
        return calculate_horn_damage(self.weapon, self.session, source, target, energy,
                                     extra_bonus=CHARGE_DAMAGE_BONUS)

    async def func(self, source: Entity, target: Entity):
        self.weapon.charge_cooldown_turn = self.session.turn + CHARGE_COOLDOWN

        source.nearby_entities = list(filter(lambda e: e != source, self.session.entities))
        for entity in source.nearby_entities:
            if source not in entity.nearby_entities:
                entity.nearby_entities.append(source)

        damage = (await self.attack(source, target, energy_cost=CHARGE_ENERGY)).dealt
        if damage:
            maybe_grant_armor(self.session, source)
            if percentage_chance(STUN_CHANCE):
                delayed_stun(self.session, target, STUN_DURATION)
                self.session.say(ls("deluxe.weapon.horn.charge.stun").format(source.name, target.name),
                                 source_id=source.id, target_id=target.id)
            if percentage_chance(KNOCKDOWN_CHANCE):
                target.get_state(Knockdown).active = True
                self.session.say(ls("deluxe.weapon.horn.charge.knockdown").format(source.name, target.name),
                                 source_id=source.id, target_id=target.id)

        return damage
