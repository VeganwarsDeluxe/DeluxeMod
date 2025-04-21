from VegansDeluxe.core import EnergyPaymentEvent
from VegansDeluxe.core import RegisterState, RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import StateContext, EventContext, percentage_chance
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls


class Tactician(Skill):
    id = 'tactician'
    name = ls("skill.tactician_name")
    description = ls("skill.tactician_description")

    def __init__(self):
        super().__init__()


@RegisterState(Tactician)
async def register(root_context: StateContext[Tactician]):
    session: Session = root_context.session
    source = root_context.entity

    @RegisterEvent(session.id, event=EnergyPaymentEvent)
    async def func(context: EventContext[EnergyPaymentEvent]):
        if context.event.entity_id != source.id:
            return

        if percentage_chance(25):
            session.say(ls("skill.tactician_effect_text").format(source.name))
            context.event.energy_payment = 0
