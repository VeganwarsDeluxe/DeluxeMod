from VegansDeluxe.core import Enemies, DecisiveItem
from VegansDeluxe.core import Entity
from VegansDeluxe.core import Item, AttachedAction, ActionTag
from VegansDeluxe.core import RegisterItem
from VegansDeluxe.core import Session
from VegansDeluxe.core.Translator.LocalizedString import ls

from DeluxeMod.States.CorrosiveMucus import CorrosiveMucus


@RegisterItem
class MucusInTheBottle(Item):
    id = 'mucus_in_the_bottle'
    name = ls("item.mucus_in_the_bottle.name")


@AttachedAction(MucusInTheBottle)
class MucusInTheBottleAction(DecisiveItem):
    id = 'mucus_in_the_bottle'
    name = ls("item.mucus_in_the_bottle.name")
    target_type = Enemies()
    priority = 0

    def __init__(self, session: Session, source: Entity, item: Item):
        super().__init__(session, source, item)
        self.tags += [ActionTag.HARMFUL]

    async def func(self, source: Entity, target: Entity):
        # Check and deduct energy from the source
        if self.source.energy >= 2:
            source.energy -= 2
        else:
            self.session.say(ls("item.mucus_in_the_bottle.energy_insufficient").format(source.name))
            return

        # Retrieve or initialize corrosive mucus state
        corrosive_mucus = target.get_state(CorrosiveMucus)

        # Apply corrosive mucus effect
        corrosive_mucus.corrosive_mucus -= 1
        corrosive_mucus.active = True

        # Notify about the action
        self.session.say(ls("item.mucus_in_the_bottle.text").format(source.name, target.name))

    @property
    def blocked(self) -> bool:
        return self.source.energy < 2
