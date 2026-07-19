import math

from VegansDeluxe.core import AttackGameEvent
from VegansDeluxe.core import PostDamagesGameEvent
from VegansDeluxe.core import PostUpdatesGameEvent
from VegansDeluxe.core import RegisterEvent, RegisterState
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.matchmakery.Events.MatchEvents import RequestActionChoiceEvent
from VegansDeluxe.rebuild import Aflame
from VegansDeluxe.rebuild.States.Aflame import FireAttackGameEvent
from VegansDeluxe.core.Translator.LocalizedString import ls


class CryoFreeze(State):
    id = 'cryo_freeze'

    def __init__(self):
        super().__init__()
        self.freeze = 0
        self.stacks = 0
        self.applied_turn = 0

    def apply(self, session: Session):
        self.freeze = max(self.freeze, 2)
        self.stacks += 1
        self.applied_turn = session.turn

    def clear(self):
        self.freeze = 0
        self.stacks = 0
        self.applied_turn = 0

    def active(self, session: Session) -> bool:
        return self.freeze > 0 and session.turn > self.applied_turn

    def damage_multiplier(self, session: Session) -> float:
        if not self.active(session):
            return 1
        if session.turn - self.applied_turn != 1:
            return 1
        return 1 + self.stacks * 0.5


@RegisterState(CryoFreeze)
async def register(root_context: StateContext[CryoFreeze]):
    session: Session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=PostUpdatesGameEvent)
    async def remove_actions(context: EventContext[PostUpdatesGameEvent]):
        if not state.active(session):
            return
        for action in context.action_manager.get_actions(session, source):
            action.removed = True

    @RegisterEvent(session.id, event=RequestActionChoiceEvent, priority=-1)
    async def cancel_action_choice(context: EventContext[RequestActionChoiceEvent]):
        if source.id != context.event.entity_id or not state.active(session):
            return
        context.event.canceled = True

    @RegisterEvent(session.id, event=AttackGameEvent)
    async def increase_weapon_attack_damage(context: EventContext[AttackGameEvent]):
        if context.event.target != source:
            return
        if not state.active(session) or not context.event.damage:
            return

        context.event.damage = math.floor(context.event.damage * state.damage_multiplier(session))
        state.clear()
        session.say(ls("state.cryo_freeze.break").format(source.name))

    @RegisterEvent(session.id, event=FireAttackGameEvent)
    async def melt_by_fire(context: EventContext[FireAttackGameEvent]):
        if context.event.target != source or not state.freeze:
            return

        context.event.damage = 0
        aflame = source.get_state(Aflame)
        if aflame:
            aflame.flame = 0
            aflame.timer = 0
            aflame.extinguished = False
        state.clear()
        session.say(ls("state.cryo_freeze.melt").format(source.name))

    @RegisterEvent(session.id, event=PostDamagesGameEvent)
    async def expire(context: EventContext[PostDamagesGameEvent]):
        if not state.active(session):
            return

        if state.freeze == 1:
            state.clear()
            session.say(ls("state.cryo_freeze.recovery").format(source.name))
            return

        state.freeze -= 1
