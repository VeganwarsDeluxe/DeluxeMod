from VegansDeluxe.core import PostUpdatesGameEvent, At, AttackGameEvent, PreMoveGameEvent
from VegansDeluxe.core import RegisterState, RegisterEvent
from VegansDeluxe.core import Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Actions.EntityActions import SkipActionGameEvent
from VegansDeluxe.core.Translator.LocalizedString import ls


class Hunger(State):
    id = 'hunger'

    def __init__(self):
        super().__init__()
        self.hunger = 0

        self.removed_energy = 0


@RegisterState(Hunger)
async def register(root_context: StateContext[Hunger]):
    session: Session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=PreMoveGameEvent)
    async def pre_move(context: EventContext[PreMoveGameEvent]):
        if not state.hunger:
            return
        source.notifications.append(
            ls("state.hunger.notification").format(state.hunger)
        )

    @RegisterEvent(session.id, event=PreMoveGameEvent)
    async def apply_hunger_effects(context: EventContext[PreMoveGameEvent]):
        if not state.hunger:
            return
        accuracy_penalty = 1
        max_damage_penalty = 0
        max_energy_penalty = 0

        if state.hunger >= 4:
            max_damage_penalty = 1

        if state.hunger >= 6:
            accuracy_penalty = 2
            max_energy_penalty = 1

        source.outbound_accuracy_bonus -= accuracy_penalty

        if not state.removed_energy:
            state.removed_energy = max_energy_penalty
            source.max_energy -= state.removed_energy

        @At(session.id, turn=session.turn, event=AttackGameEvent)
        async def attack_handler(actions_context: EventContext[AttackGameEvent]):
            if actions_context.event.source != source:
                return
            if actions_context.event.damage:
                actions_context.event.damage -= max_damage_penalty

    @RegisterEvent(session.id, event=SkipActionGameEvent)
    async def handle_pre_damages_event(context: EventContext[SkipActionGameEvent]):
        """
        Handle skip turn event,
        """
        if not state.hunger:
            return
        state.hunger = max(0, state.hunger - 5)
        if state.hunger < 6:
            source.max_energy += state.removed_energy
            state.removed_energy = 0

    @RegisterEvent(session.id, event=PostUpdatesGameEvent)
    async def use_items(context: EventContext[PostUpdatesGameEvent]):
        hunger_reducing_items = {'adrenaline', 'jet', 'chitin', 'rage-serum', 'stimulator'}

        for item in list(source.inventory):
            if item.id in hunger_reducing_items:
                if state.hunger >= 3:
                    state.hunger -= 3
                else:
                    state.hunger = 0
                session.say(ls("state.hunger.reduced_by_item").format(source.name, item.name, state.hunger))
                source.inventory.remove(item)
