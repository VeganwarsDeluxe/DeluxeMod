from VegansDeluxe.core import RegisterState, RegisterEvent, HPLossGameEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext


class DeathMatchLives(State):
    id = 'death_match_lives'

    def __init__(self):
        super().__init__()
        self.lives = 3


@RegisterState(DeathMatchLives)
async def register(root_context: StateContext[DeathMatchLives]):
    session: Session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=HPLossGameEvent)
    async def func(context: EventContext[HPLossGameEvent]):
        session.say("буль")
