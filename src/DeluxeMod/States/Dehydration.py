from VegansDeluxe.core import PreDamagesGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Translator.LocalizedString import ls


class Dehydration(State):
    id = 'dehydration'

    def __init__(self):
        super().__init__()
        self.dehydration = 1
        self.active = False
        self.triggered = False


@RegisterState(Dehydration)
async def register(root_context: StateContext[Dehydration]):
    session: Session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=PreDamagesGameEvent, filters=[lambda e: state.active])
    async def func(context: EventContext[PreDamagesGameEvent]):
        target = source
        # TODO: Huh? Figure this out.

        if state.dehydration >= 3:
            health_recovered = min(1, source.max_hp - source.hp)
            source.hp += health_recovered
            session.say(ls("state.dehydration_hp_recovery").format(source.name, source.hp))

            state.active = False
            state.dehydration = 1
        elif state.triggered:
            session.say(ls("state.dehydration_timer").format(target.name, max(state.dehydration, 0)))

        state.triggered = False


