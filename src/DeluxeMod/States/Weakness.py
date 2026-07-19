from VegansDeluxe.core import PostDamagesGameEvent
from VegansDeluxe.core import PreActionsGameEvent
from VegansDeluxe.core import PreMoveGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent, StateContext, EventContext, Session
from VegansDeluxe.core import State
from VegansDeluxe.core.Translator.LocalizedString import ls


class Weakness(State):
    id = 'weakness'

    def __init__(self):
        super().__init__()
        self.turns = 0
        self.applied_turn = 0
        self.triggered_turn = 0

    def apply(self, session: Session, turns: int = 2):
        self.turns = max(self.turns, turns)
        self.applied_turn = session.turn


@RegisterState(Weakness)
async def register(root_context: StateContext[Weakness]):
    session: Session = root_context.session
    state = root_context.state
    target = root_context.entity

    @RegisterEvent(session.id, event=PreMoveGameEvent)
    async def notify(context: EventContext[PreMoveGameEvent]):
        if not state.turns or session.turn <= state.applied_turn:
            return

        target.notifications.append(ls("state.weakness.notification").format(state.turns))

    @RegisterEvent(session.id, event=PreActionsGameEvent)
    async def apply_energy_cost_increase(context: EventContext[PreActionsGameEvent]):
        if not state.turns or session.turn <= state.applied_turn:
            return
        if not target.weapon:
            return

        target.weapon.energy_cost += 1
        state.triggered_turn = session.turn
        session.say(ls("state.weakness.energy_cost_increase").format(target.name, 1))

    @RegisterEvent(session.id, event=PostDamagesGameEvent)
    async def reset_energy_cost_increase(context: EventContext[PostDamagesGameEvent]):
        if not state.turns or state.triggered_turn != session.turn:
            return

        if target.weapon:
            target.weapon.energy_cost -= 1

        state.turns -= 1
        state.triggered_turn = 0
        if not state.turns:
            session.say(ls("state.weakness.recovery").format(target.name))

