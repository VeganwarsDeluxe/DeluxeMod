from VegansDeluxe.core import PreDamagesGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Translator.LocalizedString import ls


class Emptiness(State):
    id = 'emptiness'

    def __init__(self):
        super().__init__()
        self.emptiness = 1
        self.active = False


@RegisterState(Emptiness)
async def register(root_context: StateContext[Emptiness]):
    session: Session = root_context.session
    target = root_context.entity
    state = root_context.state

    state.triggered = False

    @RegisterEvent(session.id, event=PreDamagesGameEvent, filters=[lambda e: state.active])
    async def func(context: EventContext[PreDamagesGameEvent]):
        if state.emptiness >= 3:
            session.say(ls("state.emptiness.energy_loss").format(target.name, target.max_energy - 1))
            target.max_energy -= 1
            state.active = False
            state.emptiness = 1
        elif state.triggered:
            session.say(ls("state.emptiness.timer").format(target.name, max(state.emptiness, 0)))

        state.triggered = False
