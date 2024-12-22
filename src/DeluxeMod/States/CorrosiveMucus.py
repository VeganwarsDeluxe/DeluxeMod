import random

from VegansDeluxe.core import PreDamagesGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Translator.LocalizedString import ls


class CorrosiveMucus(State):
    id = 'corrosive_mucus'

    def __init__(self):
        super().__init__()
        self.corrosive_mucus = 3
        self.active = False


@RegisterState(CorrosiveMucus)
async def register(root_context: StateContext[CorrosiveMucus]):
    session: Session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=PreDamagesGameEvent, filters=[lambda e: state.active])
    async def func(context: EventContext[PreDamagesGameEvent]):
        if state.corrosive_mucus <= 0:
            if source.items:
                # Randomly select an item from the items list
                item_to_remove = random.choice(source.items)
                source.items.remove(item_to_remove)
                session.say(ls("state.corrosive_mucus.item.loss").format(source.name, item_to_remove.name))
            else:
                session.say(ls("state.corrosive_mucus.no_item").format(source.name))

            # Reset the effect
            state.active = False
            state.corrosive_mucus = 3
            return

        # Notify about the countdown
        session.say(ls("state.corrosive_mucus.timer").format(source.name, max(state.corrosive_mucus, 0)))
        state.corrosive_mucus -= 1
