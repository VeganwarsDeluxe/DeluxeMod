from VegansDeluxe.core import ls
from VegansDeluxe.matchmakery.Matches.Match import Match

import DeluxeMod.content
from DeluxeMod.Entities.Elemental import Elemental
from DeluxeMod.Matches.BasicMatch import BasicMatch


class ElementalMatch(BasicMatch):
    name = ls("matches.elemental")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.elemental: Elemental = None

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)
        player.team = 'players'

        if self.elemental:
            return

        elemental = Elemental(self.id)
        self.elemental = elemental
        self.session.attach_entity(elemental)
        await self.engine.attach_states(elemental, DeluxeMod.content.all_states)
        await self.engine.attach_states(elemental, elemental.skill_pool)

    async def start_game(self):
        self.elemental.hp = 4 + 4*(len(self.session.entities)-1)
        self.elemental.max_hp = self.elemental.hp
        await super().start_game()
