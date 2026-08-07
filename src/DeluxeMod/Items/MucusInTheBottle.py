from VegansDeluxe.core import Enemies, DecisiveItem
from VegansDeluxe.core import Entity
from VegansDeluxe.core import Item, AttachedAction, ActionTag
from VegansDeluxe.core import RegisterItem
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild.States.Armor import Armor

from DeluxeMod.Entities.Slime import Slime
from DeluxeMod.States.CorrosiveMucus import CorrosiveMucus


@RegisterItem
class MucusInTheBottle(Item):
    id = 'mucus_in_the_bottle'
    name = ls("deluxe.item.mucus_in_the_bottle.name")


@AttachedAction(MucusInTheBottle)
class MucusInTheBottleAction(DecisiveItem):
    id = 'mucus_in_the_bottle'
    name = ls("deluxe.item.mucus_in_the_bottle.name")
    target_type = Enemies()
    priority = 0

    tags = DecisiveItem.tags + [ActionTag.HARMFUL]

    async def func(self, source: Entity, target: Entity):
        # Check and deduct energy from the source
        if self.source.energy >= 2:
            source.energy -= 2
        else:
            self.session.say(ls("deluxe.item.mucus_in_the_bottle.energy_insufficient").format(source.name), source_id=source.id, target_id=target.id)
            return

        if isinstance(target, Slime):
            self.session.say(ls("deluxe.item.mucus_in_the_bottle.slime_immune").format(target.name), source_id=source.id, target_id=target.id)
            return

        removed_armor = target.get_state(Armor).remove_one()

        # Retrieve or initialize corrosive mucus state
        corrosive_mucus = target.get_state(CorrosiveMucus)
        if removed_armor:
            corrosive_mucus.removed_armor.append(removed_armor)

        # Apply corrosive mucus effect
        corrosive_mucus.corrosive_mucus -= 1
        corrosive_mucus.active = True

        # Notify about the action
        message = "deluxe.item.mucus_in_the_bottle.armor_loss" if removed_armor else "deluxe.item.mucus_in_the_bottle.text"
        self.session.say(ls(message).format(source.name, target.name), source_id=source.id, target_id=target.id)

    @property
    def blocked(self) -> bool:
        return self.source.energy < 2
