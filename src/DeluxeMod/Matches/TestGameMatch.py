from VegansDeluxe.matchmakery.Events.MatchEvents import DisplayItemChoiceEvent
from VegansDeluxe.matchmakery.Matches.Match import Match

import DeluxeMod.content
from DeluxeMod.Entities.Cow import Cow
from VegansDeluxe.core import ls, Entity

from DeluxeMod.Matches.BasicMatch import BasicMatch


class TestGameMatch(BasicMatch):
    name = ls("matches.test_game")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.weapon_pool = DeluxeMod.content.all_weapons

        self.skill_choice_window = len(DeluxeMod.content.all_skills)
        self.weapon_choice_window = len(DeluxeMod.content.all_weapons)

    async def init_async(self):
        await super().init_async()
        cow = Cow(self.id)
        self.session.attach_entity(cow)
        await self.engine.attach_states(cow, DeluxeMod.content.all_states)

    def player_skill_pool(self, player: Entity):
        return self.skill_pool

    async def distribute_starting_items(self):
        for player in self.session.entities:
            for item_type in DeluxeMod.content.all_items:
                item = item_type()
                for _ in range(100):
                    player.items.append(item)

            display_item_choice_event = DisplayItemChoiceEvent(self.session.id, self.session.turn, player.id)
            await self.engine.event_manager.publish(display_item_choice_event)
