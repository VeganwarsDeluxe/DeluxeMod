from VegansDeluxe.core import PreDamagesGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Translator.LocalizedString import ls


class Mutilation(State):
    id = 'mutilation'

    def __init__(self):
        super().__init__()
        self.mutilation = 1
        self.active = False
        self.triggered = False


@RegisterState(Mutilation)
async def register(root_context: StateContext[Mutilation]):
    session: Session = root_context.session
    target = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=PreDamagesGameEvent, filters=[lambda e: state.active])
    async def func(context: EventContext[PreDamagesGameEvent]):
        if state.mutilation >= 3:
            session.say(
                ls("state.mutilation_accuracy_bonus_loss").format(target.name))  # , target.weapon.accuracy_bonus - 1
            target.weapon.accuracy_bonus -= 1
            state.active = False
            state.mutilation = 1
        elif state.triggered:
            session.say(ls("state.mutilation_timer").format(target.name, max(state.mutilation, 0)))

        state.triggered = False
