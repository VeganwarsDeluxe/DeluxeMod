import math

from VegansDeluxe.core import RegisterState, RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild.States.Dodge import DodgeGameEvent


class Toad(Skill):
    id = 'toad'
    name = ls("skill.toad.name")
    description = ls("skill.toad.description")


@RegisterState(Toad)
async def register(root_context: StateContext[Toad]):
    session: Session = root_context.session
    source = root_context.entity

    @RegisterEvent(session.id, DodgeGameEvent)
    async def pre_actions(context: EventContext[DodgeGameEvent]):
        if context.event.entity.id != source.id:
            return
        context.event.bonus = -math.inf
        for entity in source.nearby_entities:
            entity.nearby_entities.remove(source) if source in entity.nearby_entities else None
        source.nearby_entities = []

