from VegansDeluxe.core import AttachedAction, RegisterItem, ActionTag
from VegansDeluxe.core import DecisiveItem
from VegansDeluxe.core import Enemies
from VegansDeluxe.core import Item
from VegansDeluxe.core.Translator.LocalizedString import ls


@RegisterItem
class DeathGrenade(Item):
    id = 'death_grenade'
    name = ls("item.death_grenade_name")


@AttachedAction(DeathGrenade)
class DeathGrenadeAction(DecisiveItem):
    id = 'death_grenade'
    name = ls("item.death_grenade_name")
    target_type = Enemies()

    priority = -1

    def __init__(self, *args):
        super().__init__(*args)
        self.tags += [ActionTag.HARMFUL]

    async def func(self, source, target):
        source.energy = max(source.energy - 2, 0)
        target.hp = max(target.hp - 1, 0)
        self.session.say(ls("item.death_grenade_text").format(source.name, target.name, target.hp))

    @property
    def blocked(self):
        # The action is blocked if the source has less than 2 energy
        return self.source.energy < 2

