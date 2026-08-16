import random

from VegansDeluxe.core import At, AttachedAction, Entity, InstantWeaponAction, MeleeAttack, PostDamagesGameEvent, State
from VegansDeluxe.core import RegisterWeapon, SelfOnly, percentage_chance
from VegansDeluxe.core.Translator.LocalizedList import LocalizedList
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

import DeluxeMod.content


class AkurukaPowerState(State):
    id = 'akuruka_power'

    def __init__(self):
        super().__init__()
        self.items_turn = None
        self.weapon_turn = None
        self.power_turn = None


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
    @property
    def cost(self) -> int:
        if self.weapon.transformed and percentage_chance(25):
            return 0
        return super().cost


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
        await source.attach_state(AkurukaPowerState(), self.event_manager)
        source.max_hp += 8
        source.hp += 8
        self.session.say(ls('deluxe.weapon.akuruka.transform.text').format(source.name),
                         source_id=source.id, target_id=source.id)

        @At(self.session.id, turn=self.session.turn + 5, event=PostDamagesGameEvent)
        async def transformation_end(context):
            if source.dead:
                return
            source.hp = 0
            self.session.say(ls('deluxe.weapon.akuruka.death').format(source.name),
                             source_id=source.id, target_id=source.id)


@AttachedAction(AkurukaPowerState)
class AkurukaItems(InstantWeaponAction):
    id = 'akuruka_items'
    name = ls('deluxe.weapon.akuruka.items.name')
    target_type = SelfOnly()
    priority = -9

    @property
    def hidden(self) -> bool:
        return self.state.items_turn == self.session.turn

    def __init__(self, session, source, state):
        super().__init__(session, source, state)
        self.state = state

    async def func(self, source: Entity, target: Entity):
        if self.hidden:
            return
        self.state.items_turn = self.session.turn
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
        return self.state.weapon_turn == self.session.turn

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
        return self.state.power_turn == self.session.turn

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
        skill = random.choice(skill_pool)
        await source.attach_state(skill(), self.event_manager)
        self.session.say(ls('deluxe.weapon.akuruka.power.text').format(source.name, skill.name),
                         source_id=source.id, target_id=source.id)
