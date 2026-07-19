from VegansDeluxe.matchmakery.Matches.Match import Match

import DeluxeMod.content
from DeluxeMod.Matches.BasicMatch import BasicMatch
from DeluxeMod.Skills.Dash import Dash
from DeluxeMod.Skills.Echo import Echo
from DeluxeMod.Skills.ExplosionMagic import ExplosionMagic
from DeluxeMod.Skills.Heroism import Heroism
from DeluxeMod.Skills.Tactician import Tactician
from DeluxeMod.Weapons.Emitter import Emitter
from DeluxeMod.Weapons.Tomahawk import Tomahawk
from VegansDeluxe.core import ls
from VegansDeluxe.rebuild import Necromancer, Visor

class TournierMatch(BasicMatch):
    name = ls("matches.tournier")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)

        self.skill_pool = DeluxeMod.content.all_skills.copy()
        self.skill_pool.remove(ExplosionMagic)
        self.skill_pool.remove(Heroism)
        self.skill_pool.remove(Necromancer)

        self.weapon_pool = DeluxeMod.content.all_weapons.copy()
