from VegansDeluxe.core import Allies
from VegansDeluxe.core import AttachedAction, RegisterItem
from VegansDeluxe.core import Item
from VegansDeluxe.core.Actions.ItemAction import DecisiveItem
from VegansDeluxe.core.Translator.LocalizedString import ls

from DeluxeMod.States.Lobotomized import Lobotomized


@RegisterItem
class Needle(Item):
    id = 'needle'
    name = ls("deluxe.item.needle.name")


@AttachedAction(Needle)
class NeedleAction(DecisiveItem):
    id = 'needle'
    name = ls("deluxe.item.needle.name")
    target_type = Allies()

    async def func(self, source, target):
        target.weapon.energy_cost = max(target.weapon.energy_cost - 1, 0)
        await target.attach_state(Lobotomized(), self.event_manager)

        self.session.say(ls("deluxe.item.needle.text").format(target.name),
                         source_id=source.id, target_id=target.id)
