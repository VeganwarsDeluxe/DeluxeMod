from VegansDeluxe.core import PostUpdatesGameEvent
from VegansDeluxe.core import PreDamagesGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent, StateContext, EventContext, Session
from VegansDeluxe.core import State
from VegansDeluxe.core.Translator.LocalizedString import ls


class Weakness(State):
    id = 'weakness'

    def __init__(self):
        super().__init__()
        self.weakness = 0
        self.triggered = False


@RegisterState(Weakness)
async def register(root_context: StateContext[Weakness]):
    session: Session = root_context.session
    state = root_context.state
    target = root_context.entity

    @RegisterEvent(session.id, event=PreDamagesGameEvent)
    async def func_damage(context: EventContext[PreDamagesGameEvent]):
        if state.weakness > 0 and not state.triggered:
            if target.weapon:
                session.say(
                    ls("state.weakness.energy_cost_increase").format(target.name, target.weapon.energy_cost + 1))
                target.weapon.energy_cost += 1
                state.weakness += 1
                state.triggered = True

    @RegisterEvent(session.id, event=PostUpdatesGameEvent)
    async def func_reset(context: EventContext[PostUpdatesGameEvent]):
        if state.weakness == 1:
            if target.weapon:
                session.say(ls("state.weakness.recovery").format(target.name))
                if state.triggered:
                    target.weapon.energy_cost -= 1

                state.triggered = False

            state.weakness -= 1


