import random

from VegansDeluxe.core import AttachedAction, DecisiveAction, RegisterState, SelfOnly
from VegansDeluxe.core import Session
from VegansDeluxe.core import StateContext
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild import Stun

MIN_STUN = 7
MAX_STUN = 10


class ClockODestiny(Skill):
    id = 'clock_o_destiny'
    name = ls("moth_vision.skill.clock_o_destiny.name")
    description = ls("moth_vision.skill.clock_o_destiny.description")

    def __init__(self):
        super().__init__()
        self.used = False


@RegisterState(ClockODestiny)
async def register(root_context: StateContext[ClockODestiny]):
    pass


@AttachedAction(ClockODestiny)
class ClockODestinyAction(DecisiveAction):
    id = 'clock_o_destiny'
    name = ls("moth_vision.skill.clock_o_destiny.action.name")
    target_type = SelfOnly()

    def __init__(self, session: Session, source, state: ClockODestiny):
        super().__init__(session, source)
        self.state: ClockODestiny = state

    @property
    def hidden(self) -> bool:
        return self.state.used

    async def func(self, source, target):
        self.state.used = True
        duration = random.randint(MIN_STUN, MAX_STUN)

        for entity in self.session.alive_entities:
            entity.get_state(Stun).stun += duration

        self.session.say(ls("moth_vision.skill.clock_o_destiny.text").format(source.name, duration),
                         source_id=source.id, target_id=source.id)
