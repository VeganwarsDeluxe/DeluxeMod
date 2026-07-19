from VegansDeluxe.matchmakery.Matches.Match import Match

import DeluxeMod.content
from DeluxeMod.Entities.Beast import Beast
from VegansDeluxe.core import ls

from DeluxeMod.Matches.BasicMatch import BasicMatch


class BeastDungeon(BasicMatch):
    name = ls("matches.beast")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.beast_created = False

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)
        player.team = 'players'
        if not self.beast_created:
            self.beast_created = True
            beast = Beast(self.id)
            self.session.attach_entity(beast)
            await self.engine.attach_states(beast, DeluxeMod.content.all_states)
