from VegansDeluxe.matchmakery.Matches.Match import Match

import DeluxeMod.content
from DeluxeMod.Entities.Guardian import Guardian
from VegansDeluxe.core import ls

from DeluxeMod.Matches.BasicMatch import BasicMatch


class GuardianDungeon(BasicMatch):
    name = ls("matches.guardian")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.guardian_created = False

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)
        player.team = 'players'
        if not self.guardian_created:
            self.guardian_created = True
            guardian = Guardian(self.id)
            self.session.attach_entity(guardian)
            await self.engine.attach_states(guardian, DeluxeMod.content.all_states)
