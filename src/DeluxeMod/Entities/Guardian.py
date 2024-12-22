import random

from VegansDeluxe.core import (
    AttachedAction, RegisterWeapon, RangedAttack, RangedWeapon,
    Entity, Enemies, Session,
    ls, PostDamageGameEvent, OwnOnly, ActionTag
)
from VegansDeluxe.core.Actions.Action import DecisiveAction, filter_targets
from VegansDeluxe.core.utils import percentage_chance
from VegansDeluxe.rebuild import DamageThreshold, Armor, Stun

from VegansDeluxe.core.Entities.NPC import NPC


class Guardian(NPC):
    def __init__(self, session_id: str, name=ls("guardian.name")):
        super().__init__(session_id, name)

        self.weapon = GuardianWeapon(session_id, self.id)
        self.hp = 9
        self.max_hp = 9
        self.max_energy = 12
        self.team = 'guardian'
        self.evade_cooldown_turn = 0

    async def choose_act(self, session: Session, action_manager):
        if session.turn == 1:
            self.get_state(DamageThreshold).threshold = 424242

        if not self.weapon:
            self.weapon = GuardianWeapon(self.session_id, self.id)

        await super().choose_act(session, action_manager)
        targets = [entity for entity in self.nearby_entities if entity != self and entity.hp > 0]
        if targets:
            target = random.choice(targets)

            if self.energy == 0:
                action_manager.queue_action(session, self, GuardianReload.id)
                return

            if self.hp < 5:
                attack = action_manager.get_action(session, self, GuardianRedHeart.id)
                attack.target = target
                action_manager.queue_action_instance(attack)
                return
            else:
                attack = action_manager.get_action(session, self, GuardianOrangeHeart.id)
                attack.target = target
                action_manager.queue_action_instance(attack)
                return


@RegisterWeapon
class GuardianWeapon(RangedWeapon):
    id = 'Guardian_weapon'
    name = ls("guardian.weapon.name")

    cubes = 3
    damage_bonus = 0
    energy_cost = 3
    accuracy_bonus = 0


@AttachedAction(GuardianWeapon)
class GuardianRedHeart(RangedAttack):
    id = 'guardian.red_heart'
    name = ls("guardian.red_heart.name")
    target_type = Enemies()

    async def func(self, source, target):
        self.session.say(ls("guardian.red_heart.text").format())
        final_damage = self.calculate_damage(source, target)

        source.energy = max(source.energy - self.weapon.energy_cost, 0) #расход энергии

        post_damage = await self.publish_post_damage_event(source, target, final_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        if final_damage > 0:
            self.session.say(ls("guardian.red_heart.attack.text").format(source.name, target.name, final_damage))
        else:
            self.session.say(ls("guardian.red_heart.attack.text.miss").format(source.name, target.name))

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage


@AttachedAction(GuardianWeapon)
class GuardianCyanHeart(RangedAttack):
    id = 'guardian.cyan_heart'
    name = ls("guardian.cyan_heart.name")
    target_type = Enemies()

    async def func(self, source, target):
        self.session.say(ls("guardian.cyan_heart.text").format())
        self.weapon.cubes = 2

        source.energy = max(source.energy - self.weapon.energy_cost, 0) #расход энергии

        final_damage = self.calculate_damage(source, target)
        post_damage = await self.publish_post_damage_event(source, target, final_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        if final_damage:
            self.session.say(ls("guardian.cyan_heart.attack.text").format(source.name, target.name, final_damage))

            if percentage_chance(30):
                stun_state = target.get_state(Stun)
                stun_state.stun += 2
                self.session.say(ls("stun").format(target.name))
        else:
            self.session.say(ls("guardian.cyan_heart.text.miss").format(source.name, target.name))

        return final_damage

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage


@AttachedAction(GuardianWeapon)
class GuardianOrangeHeart(RangedAttack):
    id = 'guardian.orange_heart'
    name = ls("guardian.orange_heart.name")
    target_type = Enemies()

    def __init__(self, session: Session, source: Entity, weapon: GuardianWeapon):
        super().__init__(session, source, weapon)
        self.targets_count = None

    async def func(self, source, target):
        self.session.say(ls("guardian.orange_heart.text"))
        self.weapon.cubes = 2
        self.weapon.damage_bonus = 1
        self.targets_count = 2

        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        # Get the list of targets
        targets = self.form_target_list(source, target)

        # Loop through each target and resolve the attack
        for target in targets:
            final_damage = self.calculate_damage(source, target)
            post_damage = await self.publish_post_damage_event(source, target, final_damage)
            target.inbound_dmg.add(source, post_damage, self.session.turn)
            source.outbound_dmg.add(target, post_damage, self.session.turn)

            # Report the outcome for each target separately
            if final_damage > 0:
                self.session.say(ls("guardian.orange_heart.attack.text").format(source.name, target.name, final_damage))
            else:
                self.session.say(ls("guardian.orange_heart.text.miss").format(source.name, target.name))

        self.weapon.damage_bonus = 0

    def form_target_list(self, source, target) -> list[Entity]:
        targets = [target]

        while len(targets) < self.targets_count:
            target_pool = [ta for ta in filter_targets(source, Enemies(), self.session.entities) if ta not in targets]
            if not target_pool:
                break
            selected_target = random.choice(target_pool)
            targets.append(selected_target)

        return targets

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage


@AttachedAction(GuardianWeapon)
class GuardianBlackHeart(RangedAttack):
    id = 'guardian.black_heart'
    name = ls("guardian.black_heart.name")
    target_type = Enemies()

    async def func(self, source, target):
        self.session.say(ls("guardian.black_heart.text").format())
        target.hp = max(0, target.hp - 999)
        self.session.say(ls("guardian.black_heart.attack.text").format(source.name, target.name))


@AttachedAction(GuardianWeapon)
class GuardianYellowHeart(RangedAttack):
    id = 'guardian.yellow_heart'
    name = ls("guardian.yellow_heart.name")
    target_type = Enemies()
    priority = -1

    def __init__(self, session: Session, source: Entity, weapon: GuardianWeapon):
        super().__init__(session, source, weapon)
        self.targets_count = None

    async def func(self, source, target):
        self.session.say(ls("guardian.yellow_heart.text").format())
        self.weapon.cubes = 2
        self.weapon.damage_bonus = 1
        self.targets_count = 2

        targets = self.form_target_list(source, target)

        for target in targets:
            final_damage = self.calculate_damage(source, target)
            post_damage = await self.publish_post_damage_event(source, target, final_damage)
            target.inbound_dmg.add(source, post_damage, self.session.turn)
            source.outbound_dmg.add(target, post_damage, self.session.turn)

            self.session.say(ls("guardian.yellow_heart.attack.text").format(source.name, target.name, final_damage))
        else:
            self.session.say(ls("guardian.yellow_heart.text.miss").format(source.name, target.name))

        self.weapon.damage_bonus = 0

    def form_target_list(self, source, target) -> list[Entity]:
        targets = [target]

        while len(targets) < self.targets_count:
            target_pool = [ta for ta in filter_targets(source, Enemies(), self.session.entities) if ta not in targets]
            if not target_pool:
                break
            selected_target = random.choice(target_pool)
            targets.append(selected_target)

        return targets

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage


@AttachedAction(GuardianWeapon)
class GuardianGreenHeart(RangedAttack):
    id = 'guardian.green_heart'
    name = ls("guardian.green_heart.name")
    target_type = OwnOnly()
    priority = -2

    def __init__(self, *args):
        super().__init__(*args)
        self.tags += [ActionTag.MEDICINE]

    async def func(self, source, target):
        # ну ви звісно генії дофіга. будьте обережні з цим
        target.get_state(Armor).remove((2, 100))
        target.hp = min(target.hp + 1, target.max_hp)
        self.session.say(ls("guardian.green_heart.text").format(source.name))
        self.session.say(ls("guardian.green_heart.effect").format(source.name, source.hp))


@AttachedAction(GuardianWeapon)
class GuardianReload(DecisiveAction):
    id = 'guardian.reload'
    name = ls("guardian.reload.name")
    target_type = OwnOnly()
    energy = 0
    priority = -1

    async def func(self, source, target):
        self.session.say(ls("guardian.reload.text").format(source.name))
        source.energy = source.max_energy
