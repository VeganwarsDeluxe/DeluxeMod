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
from VegansDeluxe.rebuild import Stun


@RegisterItem
class CryoGrenade(Item):
    id = 'cryo_grenade'
    name = ls("item.cryo.grenade_name")


@AttachedAction(CryoGrenade)
class CryoGrenadeAction(DecisiveItem):
    id = 'cryo_grenade'
    name = ls("item.cryo.grenade_name")
    target_type = Enemies()

    def __init__(self, session: Session, source: Entity, item: Item):
        super().__init__(session, source, item)
        self.tags += [ActionTag.HARMFUL]
        self.range = 2

    async def func(self, source, target):
        targets = []
        for _ in range(self.range):
            target_pool = list(filter(lambda t: t not in targets,
                                      filter_targets(source, Enemies(), self.session.entities)
                                      ))
            if not target_pool:
                continue
            target = random.choice(target_pool)
            stun_state = target.get_state(Stun)
            stun_state.stun += 2
            targets.append(target)

        source.energy = max(source.energy - 2, 0)
        self.session.say(
            ls("item.cryo.grenade_text")
            .format(source.name, LocalizedList([t.name for t in targets]))
        )

    @property
    def blocked(self):
        return self.source.energy < 2
