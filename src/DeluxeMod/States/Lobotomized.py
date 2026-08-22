import random

from VegansDeluxe.core import Enemies
from VegansDeluxe.core import ExecuteActionEvent, PostUpdateActionsGameEvent
from VegansDeluxe.core import RegisterEvent, RegisterState
from VegansDeluxe.core import Entity, Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.matchmakery.Events.MatchEvents import RequestActionChoiceEvent


class Lobotomized(State):
    id = 'lobotomized'


@RegisterState(Lobotomized)
async def register(root_context: StateContext[Lobotomized]):
    session: Session = root_context.session
    source: Entity = root_context.entity

    @RegisterEvent(session.id, event=PostUpdateActionsGameEvent)
    async def restrict_actions(context: EventContext[PostUpdateActionsGameEvent]):
        if context.event.entity_id != source.id:
            return

        allowed = {'attack'} if source.energy > 0 else {'reload'}
        for action in context.action_manager.get_actions(session, source):
            if action.id not in allowed:
                action.removed = True

    @RegisterEvent(session.id, event=ExecuteActionEvent, priority=-1)
    async def redirect_attack(context: EventContext[ExecuteActionEvent]):
        action = context.event.action
        if action.source != source or action.id != 'attack':
            return

        enemies = filter_targets(source, Enemies(), session.entities)
        action.target = random.choice(enemies) if enemies else source

    @RegisterEvent(session.id, event=RequestActionChoiceEvent, priority=-1)
    async def auto_act(context: EventContext[RequestActionChoiceEvent]):
        if context.event.entity_id != source.id or context.event.canceled or source.dead:
            return

        action_id = 'attack' if source.energy > 0 else 'reload'
        action = context.action_manager.get_action(session, source, action_id)
        if not action:
            return

        if action_id == 'attack':
            enemies = filter_targets(source, Enemies(), session.entities)
            action.target = random.choice(enemies) if enemies else source
        else:
            action.target = source

        context.action_manager.queue_action_instance(action)
        context.event.canceled = True
