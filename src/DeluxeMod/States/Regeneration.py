from VegansDeluxe.core import PreDamagesGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Translator.LocalizedString import ls


class Regeneration(State):
    id = 'regeneration'

    def __init__(self):
        super().__init__()
        self.regeneration = 3
        self.active = False


@RegisterState(Regeneration)
async def register(root_context: StateContext[Regeneration]):
    session: Session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=PreDamagesGameEvent, filters=[lambda e: state.active])
    async def func(context: EventContext[PreDamagesGameEvent]):
        if state.regeneration <= 0:
            health_recovered = min(1, source.max_hp - source.hp)
            source.hp += health_recovered
            session.say(ls("state.regeneration_hp_recovery").format(source.name, source.hp))
            state.active = False
            state.regeneration = 3
        else:
            session.say(ls("state.regeneration_timer").format(source.name, max(state.regeneration, 0)))
            state.regeneration -= 1

