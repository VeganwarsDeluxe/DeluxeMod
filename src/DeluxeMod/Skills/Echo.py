from math import ceil

from VegansDeluxe.core import RegisterState, RegisterEvent, AttackGameEvent
from VegansDeluxe.core import StateContext, EventContext, Session
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls


class Echo(Skill):
    id = 'echo'
    name = ls("skill.echo_name")
    description = ls("skill.echo_description")

    def __init__(self):
        super().__init__()
        self.last_damage = 0
        self.last_attack_turn = None


@RegisterState(Echo)
async def register(root_context: StateContext[Echo]):
    session: Session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=AttackGameEvent, priority=2)
    async def apply_bonus(context: EventContext[AttackGameEvent]):
        if context.event.source != source:
            return

        current_turn = session.turn

        if context.event.damage == 0:
            state.last_damage = 0
            state.last_attack_turn = None
            return

        if state.last_attack_turn == current_turn - 1:
            bonus_damage = ceil(state.last_damage * 0.5)
            context.event.damage += bonus_damage
        else:
            state.last_damage = 0

        state.last_damage = context.event.damage
        state.last_attack_turn = current_turn
