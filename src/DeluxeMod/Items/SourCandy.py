from VegansDeluxe.core import Item, FreeItem, AttachedAction, ActionTag
from VegansDeluxe.core import OwnOnly, EventContext, PostDamagesGameEvent
from VegansDeluxe.core import RegisterItem, At
from VegansDeluxe.core.Translator.LocalizedString import ls


@RegisterItem
class SourCandy(Item):
    id = 'sour_candy'
    name = ls("item.sour_candy.name")


@AttachedAction(SourCandy)
class SourCandyAction(FreeItem):
    id = 'sour_candy'
    name = ls("item.sour_candy.name")
    target_type = OwnOnly()
    priority = -2

    def __init__(self, *args):
        super().__init__(*args)
        self.tags += [ActionTag.MEDICINE]

    async def func(self, source, target):
        target.max_energy += 1
        self.session.say(ls("item.sour_candy.effect").format(target.name, target.max_energy))

        @At(self.session.id, turn=self.session.turn + 2, event=PostDamagesGameEvent)
        async def handle_at(context: EventContext[PostDamagesGameEvent]):
            target.max_energy = max(target.max_energy - 1, 0)
            self.session.say(ls("item.sour_candy.wear_off").format(target.name, target.max_energy))

        self.session.say(ls("item.sour_candy.use").format(source.name, target.name))
