from VegansDeluxe.core import ActionTag, EventContext, ExecuteActionEvent, PostUpdateActionsGameEvent, \
    RegisterEvent, RegisterState, Session
from VegansDeluxe.core import StateContext
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls


class Embargo(Skill):
    id = 'embargo'
    name = ls("deluxe.skill.embargo.name")
    description = ls("deluxe.skill.embargo.description")

    def __init__(self):
        super().__init__()
        self.used_item = False


@RegisterState(Embargo)
async def register(root_context: StateContext[Embargo]):
    session: Session = root_context.session
    source = root_context.entity
    state: Embargo = root_context.state

    @RegisterEvent(session.id, event=ExecuteActionEvent, priority=-1)
    async def detect_own_item_use(context: EventContext[ExecuteActionEvent]):
        if state.used_item:
            return
        action = context.event.action
        if action.source == source and ActionTag.ITEM in action.tags:
            state.used_item = True
            session.say(ls("deluxe.skill.embargo.lifted").format(source.name),
                        source_id=source.id, target_id=source.id)

    @RegisterEvent(session.id, event=PostUpdateActionsGameEvent)
    async def block_enemy_items(context: EventContext[PostUpdateActionsGameEvent]):
        if state.used_item:
            return

        entity = session.get_entity(context.event.entity_id)
        if not entity or entity == source or source.is_ally(entity):
            return

        enemies = [e for e in session.entities if not source.is_ally(e)]
        if any(e.get_state(Embargo) for e in enemies):
            return

        for action in context.action_manager.get_actions(session, entity):
            if ActionTag.ITEM in action.tags:
                action.removed = True
