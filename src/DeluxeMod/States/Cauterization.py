from VegansDeluxe.core import PreDamagesGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild.States.Aflame import Aflame
from VegansDeluxe.rebuild.States.Bleeding import Bleeding


class Cauterization(State):
    id = 'cauterization'


@RegisterState(Cauterization)
async def register(root_context: StateContext[Cauterization]):
    session: Session = root_context.session
    source = root_context.entity
    bleeding = source.get_state(Bleeding)

    @RegisterEvent(
        session.id,
        event=PreDamagesGameEvent,
        priority=-1,
        filters=[lambda e: bleeding.active and source.get_state(Aflame).flame]
    )
    async def func(context: EventContext[PreDamagesGameEvent]):
        bleeding.active = False
        bleeding.bleeding = 3
        session.say(ls("deluxe.state.aflame.cauterize").format(source.name), source_id=source.id,
                    target_id=source.id)
