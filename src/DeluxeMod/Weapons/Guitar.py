from VegansDeluxe.core import ActionTag, At, AttachedAction, DecisiveWeaponAction, Enemies, Entity, EventContext, \
    ExecuteActionEvent, MeleeAttack, PostActionsGameEvent, PostDamageGameEvent, RegisterWeapon, Session
from VegansDeluxe.core.ObjectTags import ObjectTag
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

FEEDBACK_ENERGY = 4
FEEDBACK_COOLDOWN = 5


@RegisterWeapon
class Guitar(MeleeWeapon):
    id = 'guitar'
    name = ls("deluxe.weapon.guitar.name")
    description = ls("deluxe.weapon.guitar.description")

    cubes = 4
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.feedback_cooldown_turn = 0


@AttachedAction(Guitar)
class GuitarAttack(MeleeAttack):
    pass


@AttachedAction(Guitar)
class Feedback(DecisiveWeaponAction):
    id = 'feedback'
    name = ls("deluxe.weapon.guitar.feedback.name")
    target_type = Enemies()
    priority = -4

    def __init__(self, session: Session, source: Entity, weapon: Guitar):
        super().__init__(session, source, weapon)
        self.weapon: Guitar = weapon

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.feedback_cooldown_turn

    @property
    def blocked(self) -> bool:
        return self.source.energy < FEEDBACK_ENERGY

    async def func(self, source: Entity, target: Entity):
        self.weapon.feedback_cooldown_turn = self.session.turn + FEEDBACK_COOLDOWN

        source.energy = max(source.energy - FEEDBACK_ENERGY, 0)

        self.session.say(ls("deluxe.weapon.guitar.feedback.text").format(source.name, target.name),
                         source_id=source.id, target_id=target.id)

        countered = False
        reflect_action_id = None

        @At(self.session.id, turn=self.session.turn, event=ExecuteActionEvent, priority=-10)
        async def watch(context: EventContext[ExecuteActionEvent]):
            nonlocal reflect_action_id
            action = context.event.action
            if action.source != target or action.target != source:
                return
            if ActionTag.ATTACK not in action.tags:
                return
            if action.id != 'attack':
                reflect_action_id = action.id

        @At(self.session.id, turn=self.session.turn, event=PostDamageGameEvent,
            filters=[lambda event: event.source == target and event.target == source])
        async def counter(context: EventContext[PostDamageGameEvent]):
            nonlocal countered
            if countered or not context.event.damage:
                return
            countered = True
            blocked_damage = context.event.damage
            context.event.damage = 0

            has_reflect = reflect_action_id and not target.dead
            message_key = "deluxe.weapon.guitar.feedback.effect_reflect" if has_reflect \
                else "deluxe.weapon.guitar.feedback.effect"
            self.session.say(ls(message_key).format(source.name, target.name),
                             source_id=source.id, target_id=target.id)

            counter_attack = context.action_manager.get_action(context.session, source, 'attack')
            if counter_attack:
                await counter_attack.attack(source, target, pay_energy=False, bonus_damage=blocked_damage)

            if has_reflect:
                owner_type, action_type = context.action_manager.get_action_from_all_actions(reflect_action_id)
                if ObjectTag.WEAPON in owner_type.tags:
                    reflected = action_type(self.session, source, owner_type(self.session.id, source.id))
                elif ObjectTag.ENTITY in owner_type.tags:
                    reflected = action_type(self.session, source)
                else:
                    reflected = action_type(self.session, source, owner_type())

                reflected.target = target
                await reflected.execute()

        @At(self.session.id, turn=self.session.turn, event=PostActionsGameEvent)
        async def fallback(context: EventContext[PostActionsGameEvent]):
            if countered or target.dead:
                return
            attack_action = context.action_manager.get_action(context.session, source, 'attack')
            if attack_action:
                await attack_action.attack(source, target, pay_energy=False)
