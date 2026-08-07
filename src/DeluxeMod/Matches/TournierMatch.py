from VegansDeluxe.core import ls
from VegansDeluxe.rebuild import Necromancer

import DeluxeMod.content
from DeluxeMod.Matches.BasicMatch import BasicMatch
from DeluxeMod.Skills.ExplosionMagic import ExplosionMagic
from DeluxeMod.Skills.Heroism import Heroism


class TournierMatch(BasicMatch):
    name = ls("deluxe.matches.tournier")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.skill_pool = DeluxeMod.content.all_skills.copy()
        self.skill_pool.remove(ExplosionMagic)
        self.skill_pool.remove(Heroism)
        self.skill_pool.remove(Necromancer)

        self.weapon_choice_window = 4
