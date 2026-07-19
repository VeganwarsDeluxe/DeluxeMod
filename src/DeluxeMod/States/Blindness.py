from VegansDeluxe.core import PreActionsGameEvent
from VegansDeluxe.core import PreDamagesGameEvent
from VegansDeluxe.core import PostDamagesGameEvent
from VegansDeluxe.core import PostUpdateActionsGameEvent
from VegansDeluxe.core import RegisterEvent, RegisterState
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild import Aflame


class Blindness(State):
    id = 'blindness'

    def __init__(self):
        super().__init__()
        self.stacks: list[dict[str, int]] = []
        self.triggered_turn = 0

    def blind(self, session: Session):
        self.stacks.append({"applied_turn": session.turn, "turns": 2})

    def active_stacks(self, session: Session) -> list[dict[str, int]]:
        return [stack for stack in self.stacks if session.turn > stack["applied_turn"] and stack["turns"] > 0]

    def clear(self):
        self.stacks.clear()
        self.triggered_turn = 0


@RegisterState(Blindness)
async def register(root_context: StateContext[Blindness]):
    session: Session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=PreActionsGameEvent)
    async def apply_accuracy_penalty(context: EventContext[PreActionsGameEvent]):
        penalty = len(state.active_stacks(session))
        if not penalty:
            return

        source.outbound_accuracy_bonus -= penalty
        state.triggered_turn = session.turn

    @RegisterEvent(session.id, event=PostUpdateActionsGameEvent)
    async def blind_actions(context: EventContext[PostUpdateActionsGameEvent]):
        if context.event.entity_id != source.id:
            return
        if not state.active_stacks(session):
            return

        for action in context.action_manager.get_actions(session, source):
            action.name = ls("state.blindness.action_name")

    @RegisterEvent(session.id, event=PreDamagesGameEvent)
    async def clear_by_fire(context: EventContext[PreDamagesGameEvent]):
        if not state.stacks:
            return

        aflame = source.get_state(Aflame)
        if not aflame or not aflame.flame:
            return

        state.clear()
        session.say(ls("state.blindness.fire_recovery").format(source.name))

    @RegisterEvent(session.id, event=PostDamagesGameEvent)
    async def reset_blindness(context: EventContext[PostDamagesGameEvent]):
        if not state.stacks or state.triggered_turn != session.turn:
            return

        for stack in state.active_stacks(session):
            stack["turns"] -= 1
        state.stacks = [stack for stack in state.stacks if stack["turns"] > 0]
        state.triggered_turn = 0
        if not state.stacks:
            session.say(ls("state.blindness.recovery").format(source.name))
