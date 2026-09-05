from VegansDeluxe.core import ls
from VegansDeluxe.rebuild.Matches.BasicMatch import BasicMatch

import DeluxeMod.content
from DeluxeMod.Entities.Slime import Slime


class SlimeMatch(BasicMatch):
    name = ls("deluxe.matches.slimes")
    description = ls("deluxe.matches.slimes.description")

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
            slime = Slime(self.id, name=ls("deluxe.slime.number").format(self.slimes))
            self.session.attach_entity(slime)
            await self.engine.attach_states(slime, DeluxeMod.content.deluxe_module.states)
        return player
