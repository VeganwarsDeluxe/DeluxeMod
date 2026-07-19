from VegansDeluxe.matchmakery.Matches.Match import Match

import DeluxeMod.content
from DeluxeMod.Entities.Beast import Beast
from DeluxeMod.Entities.Elemental import Elemental
from DeluxeMod.Entities.Guardian import Guardian
from DeluxeMod.Entities.Slime import Slime
from VegansDeluxe.core import ls

from DeluxeMod.Matches.BasicMatch import BasicMatch


class BotDungeon(BasicMatch):
    name = ls("matches.bots")

    async def init_async(self):
        await super().init_async()

        elemental = Elemental(self.id)
        self.session.attach_entity(elemental)
        await self.engine.attach_states(elemental, DeluxeMod.content.all_states)

        glitched_elemental = Elemental(self.id, name="❓|010100101101010")
        glitched_elemental.anger = True
        glitched_elemental.team = None
        glitched_elemental.glitched = True
        self.session.attach_entity(glitched_elemental)
        await self.engine.attach_states(glitched_elemental, DeluxeMod.content.all_states)

        beast = Beast(self.id)
        self.session.attach_entity(beast)
        await self.engine.attach_states(beast, DeluxeMod.content.all_states)

        slime = Slime(self.id)
        self.session.attach_entity(slime)
        await self.engine.attach_states(slime, DeluxeMod.content.all_states)

        guardian = Guardian(self.id)
        self.session.attach_entity(guardian)
        await self.engine.attach_states(guardian, DeluxeMod.content.all_states)

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)
        player.team = 'players'

