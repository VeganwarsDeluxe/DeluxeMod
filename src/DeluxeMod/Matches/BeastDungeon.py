from VegansDeluxe.core import ls
from VegansDeluxe.rebuild.Matches.BasicMatch import BasicMatch

import DeluxeMod.content
from DeluxeMod.Entities.Beast import Beast


class BeastDungeon(BasicMatch):
    name = ls("deluxe.matches.beast")
    description = ls("deluxe.matches.beast.description")

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
            await self.engine.attach_states(beast, DeluxeMod.content.deluxe_module.states)
        return player
