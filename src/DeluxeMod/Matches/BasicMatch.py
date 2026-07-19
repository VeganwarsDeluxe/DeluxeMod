from VegansDeluxe.matchmakery.Matches.Match import Match
from VegansDeluxe.rebuild import Fist

import DeluxeMod.content
from VegansDeluxe.core import ls

class BasicMatch(Match):
    name = ls("matches.match")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.weapon_pool = DeluxeMod.content.all_weapons.copy()
        self.weapon_pool.remove(Fist)

        self.item_pool = DeluxeMod.content.game_items_pool
        self.skill_pool = DeluxeMod.content.all_skills
        self.state_pool = DeluxeMod.content.all_states
