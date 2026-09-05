from VegansDeluxe.core import ls
from VegansDeluxe.rebuild.Matches.BasicMatch import BasicMatch

import DeluxeMod.content
from DeluxeMod.Entities.Beast import Beast
from DeluxeMod.Entities.Elemental import Elemental
from DeluxeMod.Entities.Guardian import Guardian
from DeluxeMod.Entities.Slime import Slime


class BotDungeon(BasicMatch):
    name = ls("deluxe.matches.bots")
    description = ls("deluxe.matches.bots.description")

    async def init_async(self):
        await super().init_async()

        elemental = Elemental(self.id)
        self.session.attach_entity(elemental)
        await self.engine.attach_states(elemental, DeluxeMod.content.deluxe_module.states)

        glitched_elemental = Elemental(self.id, name="❓|010100101101010")
        glitched_elemental.anger = True
        glitched_elemental.team = None
        glitched_elemental.glitched = True
        self.session.attach_entity(glitched_elemental)
        await self.engine.attach_states(glitched_elemental, DeluxeMod.content.deluxe_module.states)

        beast = Beast(self.id)
        self.session.attach_entity(beast)
        await self.engine.attach_states(beast, DeluxeMod.content.deluxe_module.states)

        slime = Slime(self.id)
        self.session.attach_entity(slime)
        await self.engine.attach_states(slime, DeluxeMod.content.deluxe_module.states)

        guardian = Guardian(self.id)
        self.session.attach_entity(guardian)
        await self.engine.attach_states(guardian, DeluxeMod.content.deluxe_module.states)

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)
        player.team = 'players'
        return player
