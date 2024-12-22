import random

from VegansDeluxe.core import AttachedAction
from VegansDeluxe.core import Enemies
from VegansDeluxe.core import Entity
from VegansDeluxe.core import PreActionsGameEvent
from VegansDeluxe.core import RegisterState
from VegansDeluxe.core import Session
from VegansDeluxe.core import StateContext, EventContext, At, PostDamageGameEvent, PreDamageGameEvent
from VegansDeluxe.core.Actions.StateAction import DecisiveStateAction
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild import Aflame, Stun


class ExplosionMagic(Skill):
    id = 'explosion_magic'
    name = ls("skill.explosion.magic_name")
    description = ls("skill.explosion.magic_description")

    def __init__(self):
        super().__init__()

        self.damage = 10

        self.cooldown_turn = 0
        self.preparation_texts = [
            ls("skill.explosion.delay_text_1"),
            ls("skill.explosion.delay_text_2"),
            ls("skill.explosion.delay_text_3"),
            ls("skill.explosion.delay_text_4"),
        ]


@RegisterState(ExplosionMagic)
async def register(root_context: StateContext[ExplosionMagic]):
    session: Session = root_context.session
    source = root_context.entity


@AttachedAction(ExplosionMagic)
class Explosion(DecisiveStateAction):
    id = 'explosion'
    name = ls("skill.explosion.action_name")
    priority = 0
    target_type = Enemies()

    def __init__(self, session: Session, source: Entity, skill: ExplosionMagic):
        super().__init__(session, source, skill)
        self.state = skill

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.state.cooldown_turn

    async def func(self, source: Entity, target: Entity):
        self.session.say(ls("skill.explosion.staff_text").format(source.name, target.name))
        random_text = random.choice(self.state.preparation_texts)
        self.session.say(random_text.format(source.name))

        stun_state = source.get_state(Stun)
        stun_state.stun += 3

        self.state.cooldown_turn = self.session.turn + 12

        @At(self.session.id, turn=self.session.turn + 1, event=PreActionsGameEvent)
        async def apply_explosion(context: EventContext[PreActionsGameEvent]):
            calculated_damage = self.state.damage
            displayed_damage = await self.publish_pre_damage_event(source, target, calculated_damage)

            source.energy = max(0, source.energy - 10)
            self.session.say(ls("skill.explosion.stun_text").format(source.name))

            aflame = target.get_state(Aflame)
            aflame.add_flame(self.session, target, source, 6)
            self.session.say(ls("skill.explosion.text").format(source.name))
            self.session.say(ls("skill.explosion.effect_text").format(target.name, displayed_damage, source.name))

            dealt_damage = await self.publish_post_damage_event(source, target, displayed_damage)
            target.inbound_dmg.add(source, dealt_damage, self.session.turn)
            source.outbound_dmg.add(target, dealt_damage, self.session.turn)

    async def publish_post_damage_event(self, source, target, displayed_damage):
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, displayed_damage)
        await self.event_manager.publish(message)
        return message.damage

    async def publish_pre_damage_event(self, source, target, calculated_damage):
        message = PreDamageGameEvent(self.session.id, self.session.turn, source, target, calculated_damage)
        await self.event_manager.publish(message)
        return message.damage
