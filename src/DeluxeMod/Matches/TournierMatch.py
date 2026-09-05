from VegansDeluxe.core import ls
from VegansDeluxe.rebuild import Necromancer
from VegansDeluxe.rebuild.Matches.BasicMatch import BasicMatch

import DeluxeMod.content
from DeluxeMod.Skills.ExplosionMagic import ExplosionMagic
from DeluxeMod.Skills.Heroism import Heroism


class TournierMatch(BasicMatch):
    name = ls("deluxe.matches.tournier")
    description = ls("deluxe.matches.tournier.description")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.skill_pool = list(DeluxeMod.content.deluxe_module.skills)
        self.skill_pool.remove(ExplosionMagic)
        self.skill_pool.remove(Heroism)
        self.skill_pool.remove(Necromancer)

        self.weapon_choice_window = 4
