from VegansDeluxe.core import AttackGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent, At
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

    @RegisterEvent(session.id, event=AttackGameEvent, priority=-10)
    async def func(context: EventContext[AttackGameEvent]):
        if context.event.source != source:
            return

        if percentage_chance(25):
            session.say(ls("skill.tactician_effect_text").format(source.name))
            weapon = context.event.source.weapon if context.event.source else None
            if weapon:
                original_energy_cost = weapon.energy_cost
                weapon.energy_cost = 0

                @At(session.id, turn=session.turn + 1, event=AttackGameEvent)
                async def reset_energy_cost(energy_cost_context: EventContext[AttackGameEvent]):
                    if energy_cost_context.event.source == source:
                        e_weapon = energy_cost_context.event.source.weapon if energy_cost_context.event.source else None
                        if e_weapon:
                            e_weapon.energy_cost = original_energy_cost
