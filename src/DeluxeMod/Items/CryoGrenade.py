import random

from VegansDeluxe.core import AttachedAction, RegisterItem, ActionTag
from VegansDeluxe.core import DecisiveItem
from VegansDeluxe.core import Enemies
from VegansDeluxe.core import Entity
from VegansDeluxe.core import Item
from VegansDeluxe.core import Session
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Translator.LocalizedList import LocalizedList
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild import Aflame

from DeluxeMod.States.CryoFreeze import CryoFreeze


@RegisterItem
class CryoGrenade(Item):
    id = 'cryo_grenade'
    name = ls("item.cryo.grenade_name")


@AttachedAction(CryoGrenade)
class CryoGrenadeAction(DecisiveItem):
    id = 'cryo_grenade'
    name = ls("item.cryo.grenade_name")
    target_type = Enemies()

    tags = DecisiveItem.tags + [ActionTag.HARMFUL]

    def __init__(self, session: Session, source: Entity, item: Item):
        super().__init__(session, source, item)
        self.range = 2

    async def func(self, source, target):
        targets = []
        frozen_targets = []
        extinguished_targets = []
        for _ in range(self.range):
            target_pool = list(filter(lambda t: t not in targets,
                                      filter_targets(source, Enemies(), self.session.entities)
                                      ))
            if not target_pool:
                continue
            target = random.choice(target_pool)
            targets.append(target)

            aflame = target.get_state(Aflame)
            if aflame and aflame.flame:
                aflame.flame = 0
                aflame.timer = 0
                aflame.extinguished = False
                extinguished_targets.append(target)
                continue

            cryo_freeze = target.get_state(CryoFreeze)
            cryo_freeze.apply(self.session)
            frozen_targets.append(target)

        source.energy = max(source.energy - 2, 0)
        if frozen_targets:
            self.session.say(
                ls("item.cryo.grenade_text")
                .format(source.name, LocalizedList([t.name for t in frozen_targets]))
            )
        if extinguished_targets:
            self.session.say(
                ls("item.cryo.grenade_extinguish_text")
                .format(LocalizedList([t.name for t in extinguished_targets]))
            )

    @property
    def blocked(self):
        return self.source.energy < 2
