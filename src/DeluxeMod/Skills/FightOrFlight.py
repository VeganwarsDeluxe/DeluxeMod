from VegansDeluxe.core import ActionTag, At, AttachedAction, Enemies, Entity, EventContext, ExecuteActionEvent, \
    Next, PostActionsGameEvent, RegisterState, Session
from VegansDeluxe.core.Actions.Action import DecisiveAction
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild import Dodge

WEAK_ROLL_ENERGY = 2
WEAK_ROLL_ACCURACY_PENALTY = 2
COOLDOWN = 5


class FightOrFlight(Skill):
    id = 'fight_or_flight'
    name = ls("deluxe.skill.fight_or_flight.name")
    description = ls("deluxe.skill.fight_or_flight.description")

    def __init__(self):
        super().__init__()
        self.cooldown_turn = 0


@RegisterState(FightOrFlight)
async def register(root_context):
    pass


@AttachedAction(FightOrFlight)
class FightOrFlightAction(DecisiveAction):
    id = 'fight_or_flight'
    name = ls("deluxe.skill.fight_or_flight.action.name")
    target_type = Enemies()
    priority = -6

    def __init__(self, session: Session, source: Entity, skill: FightOrFlight):
        super().__init__(session, source)
        self.skill = skill

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.skill.cooldown_turn

    @property
    def blocked(self) -> bool:
        return self.source.energy < 1

    async def func(self, source: Entity, target: Entity):
        self.skill.cooldown_turn = self.session.turn + COOLDOWN
        source.energy = max(source.energy - 1, 0)
        self.session.say(ls("deluxe.skill.fight_or_flight.text").format(source.name, target.name),
                         source_id=source.id, target_id=target.id)

        @At(self.session.id, turn=self.session.turn, event=ExecuteActionEvent, priority=-10)
        async def react(context: EventContext[ExecuteActionEvent]):
            if source.dead or target.dead:
                return

            action = context.event.action
            if action.source != target:
                return

            if action.target == source and ActionTag.ATTACK in action.tags:
                dodge_state = source.get_state(Dodge)
                if dodge_state.dodge_cooldown == 0:
                    dodge_action = context.action_manager.get_action(context.session, source, 'dodge')
                    if dodge_action:
                        dodge_action.target = source
                        await dodge_action.execute()
                else:
                    source.energy = max(source.energy - WEAK_ROLL_ENERGY, 0)
                    source.inbound_accuracy_bonus -= WEAK_ROLL_ACCURACY_PENALTY
                    self.session.say(ls("deluxe.skill.fight_or_flight.weak_roll").format(source.name),
                                     source_id=source.id, target_id=source.id)
            else:
                @Next(self.session.id, event=PostActionsGameEvent)
                async def counter_attack(post_context: EventContext[PostActionsGameEvent]):
                    if source.dead or target.dead:
                        return

                    attack_action = post_context.action_manager.get_action(post_context.session, source, 'attack')
                    if attack_action and target in attack_action.targets:
                        attack_action.target = target
                        await attack_action.execute()
