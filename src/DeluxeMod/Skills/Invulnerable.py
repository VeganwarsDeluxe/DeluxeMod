from VegansDeluxe.core import OwnOnly
from VegansDeluxe.core import RegisterState, AttachedAction
from VegansDeluxe.core import StateContext, Session, percentage_chance
from VegansDeluxe.core.Actions.StateAction import DecisiveStateAction
from VegansDeluxe.core.Entities.Entity import Entity
from VegansDeluxe.core.Events.Events import PostDamagesGameEvent
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls


class Invulnerable(Skill):
    id = 'invulnerable'
    name = ls("skill.invulnerable.name")
    description = ls("skill.invulnerable.description")


@RegisterState(Invulnerable)
async def register(root_context: StateContext[Invulnerable]):
    """Registers the state context."""
    session: Session = root_context.session
    entity: Entity = root_context.entity

    # Set up any additional initialization for the state if needed
    pass


@AttachedAction(Invulnerable)
class InvulnerableAction(DecisiveStateAction):
    id = 'invulnerable_action'
    priority = 0
    target_type = OwnOnly()

    def __init__(self, session: Session, source: Entity, skill: Invulnerable):
        super().__init__(session, source, skill)
        self.state = skill

    async def func(self, source: Entity, target: Entity):
        """Apply the invulnerable state effect."""
        # Check if the effect triggers with a 10% chance
        if percentage_chance(99):
            pass

            # Modify damage during the PostDamagesGameEvent
            # This requires hooking into the event system if it allows custom handling
            # ^ чатжіпіті от не шариш не кажи. тепер весь код поламано

            # self.session.event_manager.at_event(self.reduce_damage_to_one, self.session.id, PostDamagesGameEvent)

    def reduce_damage_to_one(self, event: PostDamagesGameEvent):
        """Reduce damage to 1 per attack, if the state is active."""
        # for damage_event in event.damage_events:
        #    if damage_event.source == self.source:
        #        damage_event.damage = 1

        # Publish modified event or handle it here if needed
        #self.session.event_manager.publish(event)
