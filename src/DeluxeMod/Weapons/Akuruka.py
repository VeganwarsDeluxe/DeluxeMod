import random

from VegansDeluxe.core import AttachedAction, Entity, InstantWeaponAction, MeleeAttack, PostDamagesGameEvent, State, \
    DecisiveAction, DecisiveStateAction, PostUpdateActionsGameEvent, RegisterEvent, RegisterState
from VegansDeluxe.core import EventContext, PreMoveGameEvent, RegisterWeapon, SelfOnly, percentage_chance
from VegansDeluxe.core.Translator.LocalizedList import LocalizedList
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon
from VegansDeluxe.rebuild.States.Stun import Stun

import DeluxeMod.content


class AkurukaPowerState(State):
    id = 'akuruka_power'

    def __init__(self):
        super().__init__()
        self.items_turn = None
        self.weapon_turn = None
        self.power_turn = None
        self.transformed = False
        self.timer = 0


@RegisterState(AkurukaPowerState)
async def register_akuruka_power(root_context):
    session = root_context.session
    source = root_context.entity
    state = root_context.state

    @RegisterEvent(session.id, event=PostUpdateActionsGameEvent)
    async def reroll_decisive_costs(context: EventContext[PostUpdateActionsGameEvent]):
        if not state.transformed or context.event.entity_id != source.id:
            return
        for action in context.action_manager.get_actions(session, source):
            if isinstance(action, DecisiveAction):
                action_type = type(action)
                if not hasattr(action_type, '_akuruka_base_cost'):
                    action_type._akuruka_base_cost = action_type.cost
                    base_cost = action_type._akuruka_base_cost

                    def akuruka_cost(current_action):
                        if hasattr(current_action, '_akuruka_cost'):
                            return current_action._akuruka_cost
                        return base_cost.__get__(current_action, type(current_action))

                    action_type.cost = property(akuruka_cost)
                action._akuruka_cost = 0 if percentage_chance(25) else 1


@RegisterWeapon
class Akuruka(MeleeWeapon):
    id = 'akuruka'
    name = ls('deluxe.weapon.akuruka.name')
    description = ls('deluxe.weapon.akuruka.description')

    cubes = 2
    accuracy_bonus = 4
    energy_cost = 2

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.transformed = False


@AttachedAction(Akuruka)
class AkurukaAttack(MeleeAttack):
    pass


@AttachedAction(Akuruka)
class AkurukaTransform(InstantWeaponAction):
    id = 'akuruka_transform'
    name = ls('deluxe.weapon.akuruka.transform.name')
    target_type = SelfOnly()
    priority = -10

    @property
    def hidden(self) -> bool:
        return self.weapon.transformed

    async def func(self, source: Entity, target: Entity):
        if self.weapon.transformed:
            return
        self.weapon.transformed = True
        power_state = AkurukaPowerState()
        power_state.transformed = True
        power_state.timer = 5
        await source.attach_state(power_state, self.event_manager)
        source.max_hp *= 3
        source.hp *= 3
        self.session.say(ls('deluxe.weapon.akuruka.transform.text').format(source.name),
                         source_id=source.id, target_id=source.id)

        async def notify_timer(event):
            if power_state.transformed:
                source.notifications.append(ls('deluxe.weapon.akuruka.timer').format(power_state.timer))

        self.event_manager.every(notify_timer, self.session.id, turns=1, start=self.session.turn + 1,
                                 event=PreMoveGameEvent,
                                 filters=[lambda event: event.session_id == self.session.id])

        async def transformation_end(event):
            if not power_state.transformed or source.dead:
                return
            if power_state.timer <= 1:
                power_state.timer = 0
                source.hp = 0
                self.session.say(ls('deluxe.weapon.akuruka.death').format(source.name),
                                 source_id=source.id, target_id=source.id)
            else:
                power_state.timer -= 1

        self.event_manager.every(transformation_end, self.session.id, turns=1, start=self.session.turn + 1,
                                 event=PostDamagesGameEvent)


@AttachedAction(AkurukaPowerState)
class AkurukaItems(InstantWeaponAction):
    id = 'akuruka_items'
    name = ls('deluxe.weapon.akuruka.items.name')
    target_type = SelfOnly()
    priority = -9

    @property
    def hidden(self) -> bool:
        return not self.state.transformed or self.state.items_turn == self.session.turn

    def __init__(self, session, source, state):
        super().__init__(session, source, state)
        self.state = state

    async def func(self, source: Entity, target: Entity):
        if self.hidden:
            return
        self.state.items_turn = self.session.turn
        self.state.timer = max(0, self.state.timer - 1)
        items = [random.choice(DeluxeMod.content.all_items)() for _ in range(random.randint(1, 3))]
        source.items.extend(items)
        self.session.say(ls('deluxe.weapon.akuruka.items.text').format(
            source.name, LocalizedList([item.name for item in items])), source_id=source.id, target_id=source.id)


@AttachedAction(AkurukaPowerState)
class AkurukaWeapon(InstantWeaponAction):
    id = 'akuruka_weapon'
    name = ls('deluxe.weapon.akuruka.weapon.name')
    target_type = SelfOnly()
    priority = -8

    @property
    def hidden(self) -> bool:
        return not self.state.transformed or self.state.weapon_turn == self.session.turn

    def __init__(self, session, source, state):
        super().__init__(session, source, state)
        self.state = state

    async def func(self, source: Entity, target: Entity):
        if self.hidden:
            return
        self.state.weapon_turn = self.session.turn
        pool = [weapon for weapon in DeluxeMod.content.all_weapons if weapon is not Akuruka]
        new_weapon = random.choice(pool)(source.session_id, source.id)
        source.weapon = new_weapon
        self.session.say(ls('deluxe.weapon.akuruka.weapon.text').format(source.name, new_weapon.name),
                         source_id=source.id, target_id=source.id)


@AttachedAction(AkurukaPowerState)
class AkurukaPower(InstantWeaponAction):
    id = 'akuruka_power'
    name = ls('deluxe.weapon.akuruka.power.name')
    target_type = SelfOnly()
    priority = -7

    @property
    def hidden(self) -> bool:
        return not self.state.transformed or self.state.power_turn == self.session.turn

    def __init__(self, session, source, state):
        super().__init__(session, source, state)
        self.state = state

    async def func(self, source: Entity, target: Entity):
        if self.hidden:
            return
        skill_pool = [skill for skill in DeluxeMod.content.all_skills
                      if not any(state.id == skill.id for state in source.states)]
        if not skill_pool:
            return
        self.state.power_turn = self.session.turn
        self.state.timer = max(0, self.state.timer - random.randint(1, 2))
        skill = random.choice(skill_pool)
        await source.attach_state(skill(), self.event_manager)
        self.session.say(ls('deluxe.weapon.akuruka.power.text').format(source.name, skill.name),
                         source_id=source.id, target_id=source.id)


@AttachedAction(AkurukaPowerState)
class AkurukaTransformOut(DecisiveStateAction):
    id = 'akuruka_transform_out'
    name = ls('deluxe.weapon.akuruka.transform_out.name')
    target_type = SelfOnly()
    priority = -6

    @property
    def hidden(self) -> bool:
        return not self.state.transformed

    def __init__(self, session, source, state):
        super().__init__(session, source, state)
        self.state = state

    async def func(self, source: Entity, target: Entity):
        if self.hidden:
            return
        stun_turns = max(1, 6 - self.state.timer)
        source.get_state(Stun).stun += stun_turns
        source.hp = (source.hp + 2) // 3
        source.max_hp = (source.max_hp + 2) // 3
        source.weapon = Akuruka(source.session_id, source.id)
        self.state.transformed = False
        self.session.say(ls('deluxe.weapon.akuruka.transform_out.text').format(source.name, stun_turns),
                         source_id=source.id, target_id=source.id)
