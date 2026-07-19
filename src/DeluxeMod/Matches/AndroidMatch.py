from VegansDeluxe.matchmakery.Matches.Match import Match
import DeluxeMod.content
from DeluxeMod.Entities.Android import Android
from VegansDeluxe.core import ls

from DeluxeMod.Matches.BasicMatch import BasicMatch


class AndroidMatch(BasicMatch):
    name = ls("matches.android")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.rats = 0

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)
        player.team = 'players'

        self.rats += 1
        android = Android(self.id, name="🤖|Android {0}".format(self.rats))
        self.session.attach_entity(android)
        await self.engine.attach_states(android, DeluxeMod.content.all_states)
        await self.engine.attach_states(android, android.choose_skills())
