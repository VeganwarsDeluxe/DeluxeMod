import random

from VegansDeluxe.core import AttachedAction, RegisterWeapon, MeleeWeapon, ls
from VegansDeluxe.core import FreeItem
from VegansDeluxe.core import Item
from VegansDeluxe.core import OwnOnly
from VegansDeluxe.core.Actions.Action import DecisiveAction
from VegansDeluxe.core.Actions.EntityActions import ApproachAction

from VegansDeluxe.core.Entities.NPC import NPC


class Cow(NPC):
    def __init__(self, session_id: str):
        super().__init__(session_id, name=ls("cow.name"))

        self.weapon = CowWeapon(self.session_id, self.id)

        self.hp = 30
        self.max_hp = 1
        self.max_energy = 5

        self.team = 'cows'

    async def choose_act(self, session, action_manager):
        await super().choose_act(session, action_manager)

        while True:
            action = action_manager.get_action(session, self, "cow_silence")
            if not action:
                continue
            if not action.targets:
                continue
            action.target = random.choice(action.targets)
            action_manager.queue_action(session, self, action.id)
            break


@AttachedAction(Cow)
class CowApproach(ApproachAction):
    id = 'cow_approach'
    target_type = OwnOnly()

    async def func(self, source, target):
        source.nearby_entities = list(filter(lambda t: t != source, self.session.entities))
        for entity in source.nearby_entities:
            entity.nearby_entities.append(source) if source not in entity.nearby_entities else None
        self.session.say(ls("cow.approach.text").format(source.name))


@AttachedAction(Cow)
class Silence(DecisiveAction):
    id = 'cow_silence'
    name = ls("cow.silence.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        source.items.append(MilkItem())


@AttachedAction(Cow)
class Run(DecisiveAction):
    id = 'cow_dodge'
    name = ls("cow.dodge.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        self.source.inbound_accuracy_bonus = -5
        self.session.say(ls("cow.dodge.text").format(source.name))


@AttachedAction(Cow)
class WalkAway(DecisiveAction):
    id = 'cow_walk_away'
    name = ls("cow.walk_away.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        for entity in source.nearby_entities:
            entity.nearby_entities.remove(source) if source in entity.nearby_entities else None
        source.nearby_entities = []
        self.session.say(ls("cow.walk_away.text").format(source.name))


@AttachedAction(Cow)
class EatGrassReload(DecisiveAction):
    id = 'eat_grass'
    name = ls("cow.eat_grass.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        source.energy = source.max_energy
        self.session.say(ls("cow.eat_grass.text").format(source.name, source.max_energy))


@RegisterWeapon
class CowWeapon(MeleeWeapon):
    id = 'cow_weapon'
    name = ls("cow.weapon.name")

    cubes = 0
    damage_bonus = 0
    energy_cost = 0
    accuracy_bonus = 0


class MilkItem(Item):
    id = 'milk'
    name = ls("cow.item.milk")


@AttachedAction(MilkItem)
class Milk(FreeItem):
    id = 'milk'
    name = ls("cow.item.milk")
    target_type = OwnOnly()

    async def use(self):
        self.target.energy = self.target.max_energy
        self.session.say(ls("cow.item.milk.text").format(self.source.name))
