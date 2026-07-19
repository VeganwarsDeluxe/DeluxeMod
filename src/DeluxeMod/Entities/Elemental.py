import math
import random

from VegansDeluxe.core import AttachedAction, RegisterWeapon, MeleeWeapon, ls, HPLossGameEvent
from VegansDeluxe.core import EventContext
from VegansDeluxe.core import SelfOnly
from VegansDeluxe.core import PreDeathGameEvent
from VegansDeluxe.core import RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core.Actions.Action import DecisiveAction
from VegansDeluxe.rebuild.Weapons.Revolver import ShootYourself

import DeluxeMod.content as content
from VegansDeluxe.matchmakery.Entities.NPC import NPC

from DeluxeMod.Skills.FinalBlow import FinalBlowAction


class Elemental(NPC):
    def __init__(self, session_id: str="0", name=ls("elemental.name")):
        super().__init__(session_id, name=name)

        self.weapon = ElementalWeapon(self.session_id, self.id)

        self.hp = 8
        self.max_hp = 8
        self.energy = 7
        self.max_energy = 7

        self.items = [item() for item in content.all_items]
        self.skill_pool = content.all_skills.copy()
        self.skill_pool.remove(content.Weaponsmith)
        #TODO: Gotta fix it.

        self.team = 'elemental'

        self.anger = False
        self.child = False
        self.birthed = False
        self.glitched = False

        @RegisterEvent(self.session_id, event=HPLossGameEvent, priority=2)
        async def hp_loss(context: EventContext[HPLossGameEvent]):
            if context.event.canceled:
                return
            session: Session = context.session
            if context.event.source != self:
                return
            if self.birthed:
                return
            if self.child:
                if self.hp-context.event.hp_loss <= 2:
                    self.anger = True
                    session.say(ls("elemental.anger").format(self.name))
                    context.event.canceled = True
                return

            if self.hp-context.event.hp_loss < self.max_hp / 2:
                self.hp = 0
                session.say(ls("elemental.split"))
                await self.spawn_children(session, math.floor(self.max_hp / 2))
                self.birthed = True
                context.event.canceled = True

    async def spawn_children(self, session: Session, hp: int):
        for _ in range(2):
            elemental_name = ls("elemental.name_number").format(_+1) if not self.glitched else self.name
            elemental = Elemental(self.session_id, name=elemental_name)
            elemental.max_hp = hp
            elemental.hp = hp
            elemental.child = True
            elemental.anger = self.anger
            elemental.team = self.team
            session.attach_entity(elemental)
            for state in content.all_states:
                state_instance = state()
                await elemental.attach_state(state_instance, session.event_manager)
                elemental.states.append(state_instance)
            for skill in self.skill_pool:
                skill_instance = skill()
                await elemental.attach_state(skill_instance, session.event_manager)
                elemental.states.append(skill_instance)

    async def choose_act(self, session, action_manager):
        await super().choose_act(session, action_manager)
        self.weapon = random.choice(content.all_weapons)(session.id, self.id)
        await action_manager.update_entity_actions(session, self)

        cost = False
        while not cost:
            if self.energy <= 0:
                action = action_manager.get_action(session, self, Singularity.id)
            else:
                action = random.choice(action_manager.get_available_actions(session, self))
            if not action:
                action = random.choice(action_manager.get_available_actions(session, self))
            if not action.targets:
                continue
            action.target = random.choice(action.targets)
            if action.id == ShootYourself.id or action.id == FinalBlowAction.id:
                continue
            action_manager.queue_action(session, self, action.id)
            if self.anger:
                cost = random.choice([True, False, False, False])
            else:
                cost = action.cost


@RegisterWeapon
class ElementalWeapon(MeleeWeapon):
    id = 'elemental_weapon'
    name = ls("elemental.weapon.name")

    cubes = 0
    damage_bonus = 0
    energy_cost = 0
    accuracy_bonus = 0


@AttachedAction(Elemental)
class WarpReality(DecisiveAction):
    id = 'warp_reality'
    name = ls("elemental.warp_reality.name")
    target_type = SelfOnly()

    async def func(self, source, target):
        self.source.inbound_accuracy_bonus = -5
        self.session.say(ls("elemental.warp_reality.text").format(source.name))


@AttachedAction(Elemental)
class Singularity(DecisiveAction):
    id = 'reload_singularity'
    name = ls("elemental.reload_singularity.name")
    target_type = SelfOnly()

    async def func(self, source, target):
        self.session.say(ls("elemental.reload_singularity.text").format(source.name, source.max_energy))
        source.energy = source.max_energy
