import random

from VegansDeluxe.core import AttachedAction
from VegansDeluxe.core import OwnOnly, ActionTag
from VegansDeluxe.core import PreActionsGameEvent, At
from VegansDeluxe.core import RegisterEvent, PreDeathGameEvent, EventContext
from VegansDeluxe.core import RegisterState
from VegansDeluxe.core import Session, Enemies
from VegansDeluxe.core import StateContext
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Actions.StateAction import DecisiveStateAction
from VegansDeluxe.core.Entities.Entity import Entity
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedList import LocalizedList
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild import Stun


class FinalBlow(Skill):
    id = 'final_blow'
    name = ls("skill.final_blow.name")
    description = ls("skill.final_blow.description")

    def __init__(self):
        super().__init__()
        self.cooldown_turn = 0
        self.active = False
        self.timer = 0


@RegisterState(FinalBlow)
async def register(root_context: StateContext[FinalBlow]):
    session: Session = root_context.session
    final_blow = root_context.state
    source = root_context.entity

    @RegisterEvent(session.id, event=PreDeathGameEvent, priority=3)
    async def handle_pre_death_event(context: EventContext[PreDeathGameEvent]):
        if final_blow.active and root_context.entity.id == context.event.entity.id:
            if context.event.canceled:
                return
            # Activate final blow logic
            final_blow.timer = 1
            context.event.canceled = True


@AttachedAction(FinalBlow)
class FinalBlowAction(DecisiveStateAction):
    id = 'final_blow'
    name = ls("skill.final_blow_action.name")
    priority = 0
    target_type = OwnOnly()

    def __init__(self, session: Session, source: Entity, skill: FinalBlow):
        super().__init__(session, source, skill)
        self.state = skill
        self.tags += [ActionTag.HARMFUL]
        self.targets_count = 2

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.state.cooldown_turn

    async def func(self, source: Entity, target: Entity):
        # Set long cooldown
        self.state.cooldown_turn = self.session.turn + 999

        # Select two random targets
        targets = self.select_random_targets(source)

        for target in targets:
            if isinstance(target, Entity) and target.hp > 0:
                target.hp -= 1
                self.session.say(ls("state.final_blow.hp.decrease").format(source.name, LocalizedList([t.name for t in targets])))

        stun_state = source.get_state(Stun)
        stun_state.stun += 3

        @At(self.session.id, turn=self.session.turn + 1, event=PreActionsGameEvent)
        async def final_blow_death(context: EventContext[PreActionsGameEvent]):
            source.dead = True
            self.session.say(ls("state.final_blow.death").format(source.name))

    def select_random_targets(self, source: Entity) -> list[Entity]:
        """Select two random enemies from the available enemies."""
        targets = []

        # Get a list of enemies excluding the source (self)
        target_pool = filter_targets(source, Enemies(), self.session.entities)

        # Select two unique enemies if possible
        while len(targets) < self.targets_count:
            if not target_pool:
                break  # Exit if no more enemies are available
            selected_target = random.choice(target_pool)
            target_pool.remove(selected_target)  # Remove selected target from the pool
            targets.append(selected_target)

        return targets


