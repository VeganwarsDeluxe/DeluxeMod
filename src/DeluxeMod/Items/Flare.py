import random

from VegansDeluxe.core import At, AttachedAction, Entity, Everyone, ExecuteActionEvent, Item, Next, \
    PostTickGameEvent, RegisterItem, Session
from VegansDeluxe.core.Actions.ItemAction import DecisiveItem
from VegansDeluxe.core.Translator.LocalizedList import LocalizedList
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild import Aflame
from VegansDeluxe.rebuild.Skills.Stockpile import Stockpile

GRANT_DELAY = 2
ENEMY_ENERGY_PENALTY = 2


@RegisterItem
class Flare(Item):
    id = 'flare'
    name = ls("deluxe.item.flare.name")


@AttachedAction(Flare)
class FlareAction(DecisiveItem):
    id = 'flare'
    name = ls("deluxe.item.flare.name")
    target_type = Everyone()

    @property
    def blocked(self) -> bool:
        return self.source.energy < 1

    async def func(self, source: Entity, target: Entity):
        source.energy = max(source.energy - 1, 0)

        if source.is_ally(target):
            self.session.say(ls("deluxe.item.flare.text_ally").format(source.name, target.name, GRANT_DELAY),
                             source_id=source.id, target_id=target.id)

            @At(self.session.id, turn=self.session.turn + GRANT_DELAY, event=PostTickGameEvent)
            async def grant_items(context):
                if target.dead:
                    return

                pool = Stockpile.item_pool
                given = []
                granted = []
                for _ in range(2):
                    candidates = [item_cls for item_cls in pool if item_cls.id not in given]
                    if not candidates:
                        candidates = pool
                    item_cls = random.choice(candidates)
                    given.append(item_cls.id)
                    item = item_cls()
                    target.items.append(item)
                    granted.append(item.name)

                self.session.say(ls("deluxe.item.flare.granted").format(target.name, LocalizedList(granted)),
                                 source_id=target.id, target_id=target.id)
        else:
            aflame = target.get_state(Aflame)
            aflame.add_flame(self.session, target, source, 1)
            aflame.timer = 1
            self.session.say(ls("deluxe.item.flare.text_enemy").format(source.name, target.name),
                             source_id=source.id, target_id=target.id)

            @Next(self.session.id, event=ExecuteActionEvent, priority=-1,
                  filters=[lambda e, t=target: e.action.source == t and e.action.id == 'attack'])
            async def drain_energy(context):
                target.energy = max(target.energy - ENEMY_ENERGY_PENALTY, 0)
