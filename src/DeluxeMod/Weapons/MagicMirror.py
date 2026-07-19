import random

from VegansDeluxe.core import At, PreActionsGameEvent
from VegansDeluxe.core import AttachedAction
from VegansDeluxe.core import Entity
from VegansDeluxe.core import EventContext
from VegansDeluxe.core import Next
from VegansDeluxe.core import PostTickGameEvent
from VegansDeluxe.core import RangedAttack
from VegansDeluxe.core import RegisterWeapon
from VegansDeluxe.core import SelfOnly
from VegansDeluxe.core import Session
from VegansDeluxe.core.Actions.WeaponAction import InstantWeaponAction
from VegansDeluxe.core.Question.Choice import Choice
from VegansDeluxe.core.Question.Question import Question
from VegansDeluxe.core.Question.QuestionEvents import AnswerGameEvent, QuestionGameEvent
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import RangedWeapon


@RegisterWeapon
class MagicMirror(RangedWeapon):
    id = 'magic_mirror'
    name = ls("weapon.magic_mirror.name")
    description = ls("weapon.magic_mirror.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0

    form_pool = []
    choice_pool_size = 3

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.cooldown_turn = 0


@AttachedAction(MagicMirror)
class MagicMirrorAttack(RangedAttack):
    pass


@AttachedAction(MagicMirror)
class TakeForm(InstantWeaponAction):
    id = 'take_form'
    name = ls("weapon.magic_mirror.take_form.name")
    target_type = SelfOnly()
    priority = -10

    def __init__(self, session: Session, source: Entity, weapon: MagicMirror):
        super().__init__(session, source, weapon)
        self.weapon = weapon

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.cooldown_turn or not self.weapon.form_pool

    async def func(self, source: Entity, target: Entity):
        if self.hidden:
            return

        self.weapon.cooldown_turn = self.session.turn + 9
        source.energy = source.max_energy

        weapon_pool = self.form_weapon_pool(source)
        form_question = Question(text=ls("weapon.magic_mirror.choice.text"))
        for index, weapon_type in enumerate(weapon_pool):
            choice = Choice(
                choice_id=str(index),
                text=weapon_type.name,
                result_text=ls("weapon.magic_mirror.choice.result_text").format(weapon_type.name),
            )
            form_question.add_choice(choice)

        await self.event_manager.publish(QuestionGameEvent(self.session.id, self.session.turn, source.id, form_question))

        @Next(self.session.id, event=AnswerGameEvent, filters=[lambda e: e.question_id == form_question.id])
        async def answer(context: EventContext[AnswerGameEvent]):
            weapon_type = weapon_pool[int(context.event.choice_id)]
            await self.take_form(source, weapon_type)

    def form_weapon_pool(self, source: Entity):
        weapon_pool = []
        for entity in self.session.entities:
            weapon_type = type(entity.weapon)
            if weapon_type is MagicMirror or weapon_type in weapon_pool:
                continue
            weapon_pool.append(weapon_type)
            if len(weapon_pool) >= self.weapon.choice_pool_size:
                return weapon_pool

        while len(weapon_pool) < self.weapon.choice_pool_size:
            fallback_pool = [
                weapon_type for weapon_type in self.weapon.form_pool
                if weapon_type not in weapon_pool and weapon_type is not MagicMirror
            ]
            if not fallback_pool:
                break
            weapon_pool.append(random.choice(fallback_pool))

        return weapon_pool

    async def take_form(self, source: Entity, weapon_type):
        temporary_weapon = weapon_type(source.session_id, source.id)
        source.weapon = temporary_weapon
        self.session.say(ls("weapon.magic_mirror.take_form.text").format(source.name, temporary_weapon.name),
                         at_next_event=PreActionsGameEvent)

        @At(self.session.id, turn=self.session.turn + 2, event=PostTickGameEvent)
        async def restore_mirror(context: EventContext[PostTickGameEvent]):
            source.weapon = self.weapon
            context.session.say(ls("weapon.magic_mirror.restore.text").format(source.name))
