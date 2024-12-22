import VegansDeluxe.deluxe as deluxe
import VegansDeluxe.rebuild as rebuild
from VegansDeluxe.rebuild.Skills.Weaponsmith import Weaponsmith

from DeluxeMod.Items.CaffeineCandy import CaffeineCandy
from DeluxeMod.Items.CryoGrenade import CryoGrenade
from DeluxeMod.Items.DeathGrenade import DeathGrenade
from DeluxeMod.Items.EnergyGrenade import EnergyGrenade
from DeluxeMod.Items.MucusInTheBottle import MucusInTheBottle
from DeluxeMod.Items.SourCandy import SourCandy
from DeluxeMod.Items.SweetCandy import SweetCandy
from DeluxeMod.Skills.Dash import Dash
from DeluxeMod.Skills.Echo import Echo
from DeluxeMod.Skills.ExplosionMagic import ExplosionMagic
from DeluxeMod.Skills.FinalBlow import FinalBlow
from DeluxeMod.Skills.Heroism import Heroism
from DeluxeMod.Skills.SweetTooth import SweetTooth
from DeluxeMod.Skills.Tactician import Tactician
from DeluxeMod.Skills.Toad import Toad
from DeluxeMod.States.CorrosiveMucus import CorrosiveMucus
from DeluxeMod.States.Dehydration import Dehydration
from DeluxeMod.States.Emptiness import Emptiness
from DeluxeMod.States.Hunger import Hunger
from DeluxeMod.States.Mutilation import Mutilation
from DeluxeMod.States.Regeneration import Regeneration
from DeluxeMod.States.Weakness import Weakness
from DeluxeMod.Weapons.AbyssalBlade import AbyssalBlade
from DeluxeMod.Weapons.Boomerang import Boomerang
from DeluxeMod.Weapons.Chainsaw import Chainsaw
from DeluxeMod.Weapons.CursedSword import CursedSword
from DeluxeMod.Weapons.Dagger import Dagger
from DeluxeMod.Weapons.ElectricWhip import ElectricWhip
from DeluxeMod.Weapons.Emitter import Emitter
from DeluxeMod.Weapons.GrenadeLauncher import GrenadeLauncher
from DeluxeMod.Weapons.HellBow import HellBow
from DeluxeMod.Weapons.Hook import Hook
from DeluxeMod.Weapons.NeedleFan import NeedleFan
from DeluxeMod.Weapons.Shurikens import Shurikens
from DeluxeMod.Weapons.Tomahawk import Tomahawk
from DeluxeMod.Weapons.VampiricWhip import VampiricWhip

# Testing!

all_states = (rebuild.all_states + deluxe.all_states + [Emptiness] + [Weakness, Hunger, Dehydration, Mutilation] +
              [CorrosiveMucus, Regeneration])
all_items = (rebuild.all_items + [CryoGrenade, CaffeineCandy, SourCandy, SweetCandy, DeathGrenade, EnergyGrenade] +
             [MucusInTheBottle]
             )
all_weapons = (
        rebuild.all_weapons + deluxe.all_weapons + [AbyssalBlade, Hook, HellBow, ElectricWhip, Tomahawk] +
        [CursedSword, GrenadeLauncher, Boomerang, Shurikens, NeedleFan, Emitter, Chainsaw, VampiricWhip, Dagger]
)
all_skills = (rebuild.all_skills + deluxe.all_skills + [ExplosionMagic, SweetTooth, Echo, Tactician, Dash, Heroism] +
              [FinalBlow, Toad] + [Weaponsmith]
              # + [Invulnerable] Fix it first.
              )

game_items_pool = rebuild.game_items_pool + [CryoGrenade, EnergyGrenade, MucusInTheBottle]
