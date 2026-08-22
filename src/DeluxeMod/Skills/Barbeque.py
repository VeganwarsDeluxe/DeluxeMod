from VegansDeluxe.core import At, AttachedAction, Enemies, Entity, EventContext, PreDamagesGameEvent, \
    RegisterState, Session
from VegansDeluxe.core.Actions.Action import DecisiveAction
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild import Stun

COOLDOWN = 20
STUN_DURATION = 5


class Barbeque(Skill):
    id = 'barbeque'
    name = ls("deluxe.skill.barbeque.name")
    description = ls("deluxe.skill.barbeque.description")

    def __init__(self):
        super().__init__()
        self.cooldown_turn = 0


@RegisterState(Barbeque)
async def register(root_context):
    pass


@AttachedAction(Barbeque)
class BarbequeAction(DecisiveAction):
    id = 'barbeque'
    name = ls("deluxe.skill.barbeque.action.name")
    target_type = Enemies()

    def __init__(self, session: Session, source: Entity, skill: Barbeque):
        super().__init__(session, source)
        self.skill = skill

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.skill.cooldown_turn

    async def func(self, source: Entity, target: Entity):
        self.skill.cooldown_turn = self.session.turn + COOLDOWN

        source.get_state(Stun).stun += STUN_DURATION
        target.get_state(Stun).stun += STUN_DURATION

        self.session.say(ls("deluxe.skill.barbeque.text").format(source.name, target.name),
                         source_id=source.id, target_id=target.id)

        for offset in range(1, STUN_DURATION + 1):
            @At(self.session.id, turn=self.session.turn + offset, event=PreDamagesGameEvent)
            async def regen(context: EventContext[PreDamagesGameEvent], so=source, ta=target):
                for entity in (so, ta):
                    if entity.dead:
                        continue
                    entity.hp = min(entity.hp + 1, entity.max_hp)
                    entity.energy = min(entity.energy + 1, entity.max_energy)
                    self.session.say(ls("deluxe.skill.barbeque.tick").format(entity.name),
                                     source_id=entity.id, target_id=entity.id)
