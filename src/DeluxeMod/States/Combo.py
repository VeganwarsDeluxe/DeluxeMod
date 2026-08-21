from VegansDeluxe.core import PostTickGameEvent, PreActionsGameEvent
from VegansDeluxe.core import RegisterEvent, RegisterState
from VegansDeluxe.core import Entity, Session
from VegansDeluxe.core import State
from VegansDeluxe.core import StateContext, EventContext
from VegansDeluxe.core.Translator.LocalizedString import ls

COMBO_DURATION = 2


class Combo(State):
    id = 'combo'

    def __init__(self):
        super().__init__()
        self.stacks = 0
        self.duration = 0
        self.boosted_weapon = None
        self.applied_bonus = 0

    def trigger(self, session: Session, source: Entity):
        was_active = self.duration > 0
        self.stacks += 1
        self.duration = COMBO_DURATION

        if was_active:
            session.say(ls("deluxe.state.combo.continue").format(source.name, self.stacks),
                        source_id=source.id, target_id=source.id)
        else:
            session.say(ls("deluxe.state.combo.start").format(source.name),
                        source_id=source.id, target_id=source.id)

    @property
    def bonus_cubes(self) -> int:
        if self.duration <= 0:
            return 0
        return 1 + self.stacks // 2

    def revert_bonus(self):
        if self.boosted_weapon is not None:
            self.boosted_weapon.cubes -= self.applied_bonus
            self.boosted_weapon = None
        self.applied_bonus = 0


@RegisterState(Combo)
async def register(root_context: StateContext[Combo]):
    session: Session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=PreActionsGameEvent)
    async def apply_bonus_cubes(context: EventContext[PreActionsGameEvent]):
        if state.boosted_weapon is not None and state.boosted_weapon is not source.weapon:
            state.revert_bonus()

        desired = state.bonus_cubes
        if desired != state.applied_bonus:
            source.weapon.cubes += desired - state.applied_bonus
            state.applied_bonus = desired
            state.boosted_weapon = source.weapon if desired else None

    @RegisterEvent(session.id, event=PostTickGameEvent)
    async def tick(context: EventContext[PostTickGameEvent]):
        if state.duration <= 0:
            return

        source.energy = min(source.energy + 1, source.max_energy)
        state.duration -= 1

        if state.duration <= 0:
            state.revert_bonus()
            session.say(ls("deluxe.state.combo.end").format(source.name, state.stacks),
                        source_id=source.id, target_id=source.id)
            state.stacks = 0
