from VegansDeluxe.core import AttachedAction
from VegansDeluxe.core import Enemies
from VegansDeluxe.core import Entity
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core import RegisterState
from VegansDeluxe.core import Session
from VegansDeluxe.core import StateContext, PostDamageGameEvent
from VegansDeluxe.core.Actions.StateAction import DecisiveStateAction
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls


class Dash(Skill):
    id = 'dash'
    name = ls("skill.dash_name")
    description = ls("skill.dash_description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cooldown_turn = 0


@RegisterState(Dash)
async def register(root_context: StateContext[Dash]):
    session: Session = root_context.session
    source = root_context.entity


@AttachedAction(Dash)
class DashAction(DecisiveStateAction):
    id = 'dash'
    name = ls("skill.dash_action_name")
    target_type = Enemies()
    priority = 0

    def __init__(self, session: Session, source: Entity, skill: Dash):
        super().__init__(session, source, skill)
        self.state = skill

    @property
    def blocked(self) -> bool:
        return self.source.weapon.ranged

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.state.cooldown_turn

    async def func(self, source: Entity, target: Entity):
        self.state.cooldown_turn = self.session.turn + 3

        # Получаем текущее оружие
        weapon = source.weapon

        attack_action = MeleeAttack(self.session, source, weapon)

        attack_result = await attack_action.attack(source, target)
        total_damage = attack_result.dealt + 1

        if total_damage:
            self.session.say(
                ls("skill.dash.text").format(source.name, target.name, total_damage)
            )
        else:
            self.session.say(
                ls("skill.dash.text_miss").format(source.name, target.name)
            )

        post_damage = await self.publish_post_damage_event(source, target, total_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        if source not in target.nearby_entities:
            target.nearby_entities.append(source)
        if target not in source.nearby_entities:
            source.nearby_entities.append(target)

        for entity in source.nearby_entities:
            if entity != target and target not in entity.nearby_entities:
                entity.nearby_entities.append(target)
            if entity != target and entity not in target.nearby_entities:
                target.nearby_entities.append(entity)

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage
