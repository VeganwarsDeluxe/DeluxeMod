from VegansDeluxe import ContentModule, register_content_module
from VegansDeluxe.rebuild.Matches.BasicMatch import BasicMatch
from VegansDeluxe.rebuild.Matches.TestGameMatch import TestGameMatch
from VegansDeluxe.rebuild.Skills.Stockpile import Stockpile
from VegansDeluxe.rebuild.Skills.Weaponsmith import Weaponsmith

from DeluxeMod.Items.CaffeineCandy import CaffeineCandy
from DeluxeMod.Items.CryoGrenade import CryoGrenade
from DeluxeMod.Items.DeathGrenade import DeathGrenade
from DeluxeMod.Items.EnergyGrenade import EnergyGrenade
from DeluxeMod.Items.MucusInTheBottle import MucusInTheBottle
from DeluxeMod.Items.SourCandy import SourCandy
from DeluxeMod.Items.SweetCandy import SweetCandy
from DeluxeMod.Matches.AkurukaMatch import AkurukaMatch
from DeluxeMod.Matches.AndroidMatch import AndroidMatch
from DeluxeMod.Matches.BeastDungeon import BeastDungeon
from DeluxeMod.Matches.BotDungeon import BotDungeon
from DeluxeMod.Matches.ElementalMatch import ElementalMatch
from DeluxeMod.Matches.GuardianDungeon import GuardianDungeon
from DeluxeMod.Matches.Room57 import Room57
from DeluxeMod.Matches.SlimeMatch import SlimeMatch
from DeluxeMod.Matches.TournierMatch import TournierMatch
from DeluxeMod.Skills.ClassicSheath import ClassicSheath
from DeluxeMod.Skills.Dash import Dash
from DeluxeMod.Skills.Echo import Echo
from DeluxeMod.Skills.ExplosionMagic import ExplosionMagic
from DeluxeMod.Skills.FinalBlow import FinalBlow
from DeluxeMod.Skills.Heroism import Heroism
from DeluxeMod.Skills.SweetTooth import SweetTooth
from DeluxeMod.Skills.Tactician import Tactician
from DeluxeMod.Skills.Toad import Toad
from DeluxeMod.States.Blindness import Blindness
from DeluxeMod.States.CorrosiveMucus import CorrosiveMucus
from DeluxeMod.States.CryoFreeze import CryoFreeze
from DeluxeMod.States.Dehydration import Dehydration
from DeluxeMod.States.Emptiness import Emptiness
from DeluxeMod.States.Hunger import Hunger
from DeluxeMod.States.Mutilation import Mutilation
from DeluxeMod.States.Regeneration import Regeneration
from DeluxeMod.States.Weakness import Weakness
from DeluxeMod.Weapons.AbyssalBlade import AbyssalBlade
from DeluxeMod.Weapons.AluminiumBat import AluminiumBat
from DeluxeMod.Weapons.Boomerang import Boomerang
from DeluxeMod.Weapons.Briefcase import Briefcase
from DeluxeMod.Weapons.ButterflyKnife import ButterflyKnife
from DeluxeMod.Weapons.Chainsaw import Chainsaw
from DeluxeMod.Weapons.CursedSword import CursedSword
from DeluxeMod.Weapons.Dagger import Dagger
from DeluxeMod.Weapons.ElectricWhip import ElectricWhip
from DeluxeMod.Weapons.Emitter import Emitter
from DeluxeMod.Weapons.FryingPan import FryingPan
from DeluxeMod.Weapons.GrenadeLauncher import GrenadeLauncher
from DeluxeMod.Weapons.Gunbai import Gunbai
from DeluxeMod.Weapons.HellBow import HellBow
from DeluxeMod.Weapons.Hook import Hook
from DeluxeMod.Weapons.Horn import Horn
from DeluxeMod.Weapons.MagicMirror import MagicMirror
from DeluxeMod.Weapons.NeedleFan import NeedleFan
from DeluxeMod.Weapons.Scalpel import Scalpel
from DeluxeMod.Weapons.Shurikens import Shurikens
from DeluxeMod.Weapons.StarBow import StarBow
from DeluxeMod.Weapons.ThrowingSickles import ThrowingSickles
from DeluxeMod.Weapons.Tomahawk import Tomahawk
from DeluxeMod.Weapons.VampiricWhip import VampiricWhip

all_states = [Emptiness, Weakness, Hunger, Dehydration, Mutilation, Blindness, CorrosiveMucus, CryoFreeze, Regeneration]
all_items = [CryoGrenade, CaffeineCandy, SourCandy, SweetCandy, DeathGrenade, EnergyGrenade, MucusInTheBottle]
all_weapons = [AbyssalBlade, Hook, HellBow, ElectricWhip, Tomahawk, CursedSword, GrenadeLauncher,
               Boomerang, Shurikens, NeedleFan, Emitter, Chainsaw, VampiricWhip, Dagger, StarBow,
               MagicMirror, ButterflyKnife, ThrowingSickles, Gunbai,
               AluminiumBat, Horn, FryingPan, Briefcase, Scalpel]
all_skills = [ExplosionMagic, SweetTooth, Echo, Tactician, Dash, Heroism, FinalBlow, Toad, Weaponsmith,
              ClassicSheath]

game_items_pool = [MucusInTheBottle]

all_matches = [AndroidMatch, BasicMatch, BeastDungeon, BotDungeon, ElementalMatch, GuardianDungeon,
               Room57, SlimeMatch, TestGameMatch, TournierMatch, AkurukaMatch]

# Death Grenade stays registered (still directly usable) but is kept out of the
# random Stockpile/Flare grant pool -- see DeluxeMod.Items.DeathGrenade for why.
Stockpile.item_pool = Stockpile.item_pool + [CryoGrenade, EnergyGrenade]
MagicMirror.form_pool = [weapon for weapon in all_weapons if weapon is not MagicMirror]

deluxe_module = register_content_module(ContentModule(
    id="deluxemod",
    version="0.1.2",
    requires=("rebuild", "mothvision"),
    weapons=tuple(all_weapons),
    states=tuple(all_states),
    skills=tuple(all_skills),
    items=tuple(all_items),
    matches=tuple(all_matches),
    extra={"game_items_pool": tuple(game_items_pool)},
))

# Specialized matches use DeluxeMod entities directly. Their dependencies are
# expressed by the module itself rather than duplicated as string literals.
for match in all_matches:
    if match is not BasicMatch:
        match.required_content_modules = frozenset(
            {deluxe_module.id, *deluxe_module.requires}
        )
