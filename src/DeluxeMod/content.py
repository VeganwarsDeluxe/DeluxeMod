import VegansDeluxe.deluxe as deluxe
import VegansDeluxe.rebuild as rebuild
from VegansDeluxe.rebuild.Skills.Stockpile import Stockpile
from VegansDeluxe.rebuild.Skills.Weaponsmith import Weaponsmith

from DeluxeMod.Items.CaffeineCandy import CaffeineCandy
from DeluxeMod.Items.CryoGrenade import CryoGrenade
from DeluxeMod.Items.DeathGrenade import DeathGrenade
from DeluxeMod.Items.EnergyGrenade import EnergyGrenade
from DeluxeMod.Items.MucusInTheBottle import MucusInTheBottle
from DeluxeMod.Items.SourCandy import SourCandy
from DeluxeMod.Items.SweetCandy import SweetCandy
from DeluxeMod.Matches.AndroidMatch import AndroidMatch
from DeluxeMod.Matches.BasicMatch import BasicMatch
from DeluxeMod.Matches.BeastDungeon import BeastDungeon
from DeluxeMod.Matches.BotDungeon import BotDungeon
from DeluxeMod.Matches.ElementalDungeon import ElementalDungeon
from DeluxeMod.Matches.GuardianDungeon import GuardianDungeon
from DeluxeMod.Matches.SlimeDungeon import SlimeDungeon
from DeluxeMod.Matches.TestGameMatch import TestGameMatch
from DeluxeMod.Matches.TournierMatch import TournierMatch
from DeluxeMod.Skills.Dash import Dash
from DeluxeMod.Skills.Echo import Echo
from DeluxeMod.Skills.ExplosionMagic import ExplosionMagic
from DeluxeMod.Skills.FinalBlow import FinalBlow
from DeluxeMod.Skills.Heroism import Heroism
from DeluxeMod.Skills.SweetTooth import SweetTooth
from DeluxeMod.Skills.Tactician import Tactician
from DeluxeMod.Skills.Toad import Toad
from DeluxeMod.States.CorrosiveMucus import CorrosiveMucus
from DeluxeMod.States.CryoFreeze import CryoFreeze
from DeluxeMod.States.Dehydration import Dehydration
from DeluxeMod.States.Emptiness import Emptiness
from DeluxeMod.States.Hunger import Hunger
from DeluxeMod.States.Blindness import Blindness
from DeluxeMod.States.Mutilation import Mutilation
from DeluxeMod.States.Regeneration import Regeneration
from DeluxeMod.States.Weakness import Weakness
from DeluxeMod.Weapons.AbyssalBlade import AbyssalBlade
from DeluxeMod.Weapons.Boomerang import Boomerang
from DeluxeMod.Weapons.ButterflyKnife import ButterflyKnife
from DeluxeMod.Weapons.Chainsaw import Chainsaw
from DeluxeMod.Weapons.CursedSword import CursedSword
from DeluxeMod.Weapons.Dagger import Dagger
from DeluxeMod.Weapons.ElectricWhip import ElectricWhip
from DeluxeMod.Weapons.Emitter import Emitter
from DeluxeMod.Weapons.GrenadeLauncher import GrenadeLauncher
from DeluxeMod.Weapons.Gunbai import Gunbai
from DeluxeMod.Weapons.HellBow import HellBow
from DeluxeMod.Weapons.Hook import Hook
from DeluxeMod.Weapons.MagicMirror import MagicMirror
from DeluxeMod.Weapons.NeedleFan import NeedleFan
from DeluxeMod.Weapons.Shurikens import Shurikens
from DeluxeMod.Weapons.StarBow import StarBow
from DeluxeMod.Weapons.Tomahawk import Tomahawk
from DeluxeMod.Weapons.ThrowingSickles import ThrowingSickles
from DeluxeMod.Weapons.VampiricWhip import VampiricWhip

all_states = (rebuild.all_states + deluxe.all_states + [Emptiness] + [Weakness, Hunger, Dehydration, Mutilation] +
              [Blindness] +
              [CorrosiveMucus, CryoFreeze, Regeneration])
all_items = (rebuild.all_items + [CryoGrenade, CaffeineCandy, SourCandy, SweetCandy, DeathGrenade, EnergyGrenade] +
             [MucusInTheBottle]
             )
all_weapons = (
        rebuild.all_weapons + deluxe.all_weapons + [AbyssalBlade, Hook, HellBow, ElectricWhip, Tomahawk] +
        [CursedSword, GrenadeLauncher, Boomerang, Shurikens, NeedleFan, Emitter, Chainsaw, VampiricWhip, Dagger] +
        [StarBow, MagicMirror, ButterflyKnife, ThrowingSickles, Gunbai]
)
MagicMirror.form_pool = [weapon for weapon in all_weapons if weapon is not MagicMirror]
all_skills = (rebuild.all_skills + deluxe.all_skills + [ExplosionMagic, SweetTooth, Echo, Tactician, Dash, Heroism] +
              [FinalBlow, Toad] + [Weaponsmith]
              # + [Invulnerable] Fix it first.
              )

game_items_pool = rebuild.game_items_pool + [MucusInTheBottle]

all_matches = [AndroidMatch, BasicMatch, BeastDungeon, BotDungeon, ElementalDungeon, GuardianDungeon,
               SlimeDungeon, TestGameMatch, TournierMatch]

Stockpile.item_pool = Stockpile.item_pool + [CryoGrenade, EnergyGrenade, DeathGrenade]
