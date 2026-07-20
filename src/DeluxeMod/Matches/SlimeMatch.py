from VegansDeluxe.core import ls
from VegansDeluxe.matchmakery.Matches.Match import Match

import DeluxeMod.content
from DeluxeMod.Entities.Slime import Slime
from DeluxeMod.Matches.BasicMatch import BasicMatch


class SlimeMatch(BasicMatch):
    name = ls("matches.slimes")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.slimes = 0

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)
        player.team = 'players'
        # if self.slimes == 1:
        #     return
        for _ in range(2):
            self.slimes += 1
            slime = Slime(self.id, name=ls("slime.number").format(self.slimes))
            self.session.attach_entity(slime)
            await self.engine.attach_states(slime, DeluxeMod.content.all_states)
