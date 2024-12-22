from VegansDeluxe.core import Item, FreeItem, AttachedAction, ActionTag
from VegansDeluxe.core import OwnOnly
from VegansDeluxe.core import RegisterItem
from VegansDeluxe.core.Translator.LocalizedString import ls

from DeluxeMod.States.Regeneration import Regeneration


@RegisterItem
class SweetCandy(Item):
    id = 'sweet_candy'
    name = ls("item.sweet_candy_name")


@AttachedAction(SweetCandy)
class SweetCandyAction(FreeItem):
    id = 'sweet_candy'
    name = ls("item.sweet_candy_name")
    target_type = OwnOnly()
    priority = -2

    def __init__(self, *args):
        super().__init__(*args)
        self.tags += [ActionTag.MEDICINE]

    async def func(self, source, target):
        # Retrieve the current state
        regeneration = target.get_state(Regeneration)

        if regeneration.active:
            regeneration.regeneration -= 1
        regeneration.active = True

        # Notify the session about the effect
        self.session.say(ls("item.sweet_candy.effect").format(source.name))
