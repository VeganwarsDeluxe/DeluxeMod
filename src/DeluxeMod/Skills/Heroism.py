from VegansDeluxe.core import AttachedAction, Allies, Own
from VegansDeluxe.core import OwnOnly
from VegansDeluxe.core import RegisterState
from VegansDeluxe.core import Session
from VegansDeluxe.core import StateContext
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Actions.StateAction import DecisiveStateAction
from VegansDeluxe.core.Entities.Entity import Entity
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls


class Heroism(Skill):
    id = 'heroism'
    name = ls("skill.heroism.name")
    description = ls("skill.heroism.description")

    def __init__(self):
        super().__init__()
        self.cooldown_turn = 0


@RegisterState(Heroism)
async def register(root_context: StateContext[Heroism]):
    session: Session = root_context.session
    source = root_context.entity


@AttachedAction(Heroism)
class HeroismAction(DecisiveStateAction):
    id = 'heroism'
    name = ls("skill.heroism_action.name")
    priority = 0
    target_type = OwnOnly()

    def __init__(self, session: Session, source: Entity, skill: Heroism):
        super().__init__(session, source, skill)
        self.state = skill

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.state.cooldown_turn

    def get_allies(self, source: Entity) -> list[Entity]:
        return filter_targets(source, Allies(own=Own.SELF_EXCLUDED), self.session.entities)

    async def func(self, source: Entity, target: Entity):
        # Set long cooldown
        self.state.cooldown_turn = self.session.turn + 999

        # Deduct 1 HP from the user (source)
        source.hp -= 1
        self.session.say(ls("state.heroism.hp.lost").format(source.name, source.hp))

        # Heal 1 HP for all allies
        allies = self.get_allies(source)
        for ally in allies:
            if ally.hp < ally.max_hp:
                health_recovered = min(1, ally.max_hp - ally.hp)
                ally.hp += health_recovered
                self.session.say(ls("state.heroism.hp.recovery").format(ally.name, ally.hp))
