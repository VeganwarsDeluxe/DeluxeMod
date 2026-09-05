from VegansDeluxe import ContentModule, register_content_module

from MothVision.Items.Flare import Flare
from MothVision.Items.Needle import Needle
from MothVision.Skills.Barbeque import Barbeque
from MothVision.Skills.ClockODestiny import ClockODestiny
from MothVision.Skills.Embargo import Embargo
from MothVision.Skills.FightOrFlight import FightOrFlight
from MothVision.Skills.Lobotomy import Lobotomy
from MothVision.States.Cauterization import Cauterization
from MothVision.States.Combo import Combo
from MothVision.Weapons.ChainedDagger import ChainedDagger
from MothVision.Weapons.Guitar import Guitar
from MothVision.Weapons.HandBandage import HandBandage
from MothVision.Weapons.Mimicry import Mimicry
from MothVision.Weapons.Pen import Pen
from MothVision.Weapons.TurboGloves import TurboGloves
from MothVision.Weapons.WoodenLog import WoodenLog

all_states = [Cauterization, Combo]
all_items = [Needle, Flare]
all_weapons = [ChainedDagger, Guitar, HandBandage, Mimicry, Pen, TurboGloves, WoodenLog]
all_skills = [Lobotomy, ClockODestiny, Embargo, FightOrFlight, Barbeque]
all_matches = []
game_items_pool = [Flare]

mothvision_module = register_content_module(ContentModule(
    id="mothvision",
    version="0.1.0",
    requires=("rebuild",),
    weapons=tuple(all_weapons),
    states=tuple(all_states),
    skills=tuple(all_skills),
    items=tuple(all_items),
    extra={"game_items_pool": tuple(game_items_pool)},
))
