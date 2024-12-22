from VegansDeluxe.core import Item, FreeItem, AttachedAction, ActionTag, After
from VegansDeluxe.core import OwnOnly, EventContext, PostDamagesGameEvent
from VegansDeluxe.core import RegisterItem
from VegansDeluxe.core.Translator.LocalizedString import ls


@RegisterItem
class CaffeineCandy(Item):
    id = 'caffeine_candy'
    name = ls("item.caffeine.candy_name")


@AttachedAction(CaffeineCandy)
class CaffeineCandyAction(FreeItem):
    id = 'caffeine_candy'
    name = ls("item.caffeine.candy_name")
    target_type = OwnOnly()
    priority = -2

    def __init__(self, *args):
        super().__init__(*args)
        self.tags += [ActionTag.MEDICINE]

    async def func(self, source, target):
        @After(self.session.id, 0, event=PostDamagesGameEvent, repeats=3)
        async def handle_at(context: EventContext[PostDamagesGameEvent]):
            energy_recovered = min(1, source.max_energy - source.energy)
            source.energy += energy_recovered
            self.session.say(ls("item.caffeine.candy_effect").format(target.name, target.energy))

        self.session.say(ls("item.caffeine.candy_use").format(source.name, target.name))
