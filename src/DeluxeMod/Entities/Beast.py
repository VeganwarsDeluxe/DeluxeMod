import random

from VegansDeluxe.core import AttachedAction, RegisterWeapon, MeleeAttack, MeleeWeapon, Entity, Enemies, Session, ls
from VegansDeluxe.core import OwnOnly
from VegansDeluxe.core import PostDamageGameEvent
from VegansDeluxe.core.Actions.Action import DecisiveAction
from VegansDeluxe.core.utils import percentage_chance
from VegansDeluxe.rebuild import DamageThreshold

from VegansDeluxe.core.Entities.NPC import NPC


class Beast(NPC):
    def __init__(self, session_id: str, name=ls("beast.name")):
        super().__init__(session_id, name)

        self.weapon = BeastWeapon(session_id, self.id)

        self.hp = 4
        self.max_hp = 4
        self.max_energy = 6

        self.team = 'beast'

        self.evade_cooldown_turn = 0

    async def choose_act(self, session: Session[Entity], action_manager):
        if session.turn == 1:
            self.get_state(DamageThreshold).threshold = 6

        if not self.weapon:
            self.weapon = BeastWeapon(self.session_id, self.id)

        await super().choose_act(session, action_manager)

        if self.nearby_entities != list(filter(lambda t: t != self, session.entities)) and percentage_chance(75):
            action_manager.queue_action(session, self, BeastApproach.id)
            return

        if percentage_chance(5):
            action_manager.queue_action(session, self, BeastGrowl.id)
            return

        if self.energy == 0:
            action_manager.queue_action(session, self, BeastReload.id)
            return

        targets = [entity for entity in self.nearby_entities if entity != self and entity.hp > 0]
        if targets:
            target = random.choice(targets)
            if target.hp == 1:
                attack = action_manager.get_action(session, self, BeastBite.id)
                attack.target = target
                action_manager.queue_action_instance(attack)
                return
            else:
                # Если цель имеет 5 и больше энергии, проверяем кулдаун уклонения
                if target.energy >= 5:
                    if session.turn >= self.evade_cooldown_turn:
                        action_manager.queue_action(session, self, BeastEvade.id)
                        self.evade_cooldown_turn = session.turn + 4
                        return
                    else:
                        # Кулдаун на уклонение еще активен, выбираем другое действие
                        attack = action_manager.get_action(session, self, BeastAttack.id)
                        attack.target = target
                        action_manager.queue_action_instance(attack)
                        return
                else:
                    if target.energy == 0:
                        attack = action_manager.get_action(session, self, BeastAttackTwo.id)
                        attack.target = target
                        action_manager.queue_action_instance(attack)
                        return
                    else:
                        attack = action_manager.get_action(session, self, BeastAttack.id)
                        attack.target = target
                        action_manager.queue_action_instance(attack)
                        return
        else:
            # Нет целей -- перезарядка
            action_manager.queue_action(session, self, BeastReload.id)
            return


@AttachedAction(Beast)
class BeastApproach(DecisiveAction):
    id = 'beast_approach'
    name = ls("beast.approach.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        source.nearby_entities = list(filter(lambda t: t != source, self.session.entities))
        for entity in source.nearby_entities:
            if source not in entity.nearby_entities:
                entity.nearby_entities.append(source)
        self.session.say(ls("beast.approach.text").format(source.name))


@AttachedAction(Beast)
class BeastReload(DecisiveAction):
    id = 'beast_reload'
    name = ls("beast.reload.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        self.session.say(ls("beast.reload.text").format(source.name, source.max_energy))
        source.energy = source.max_energy


@AttachedAction(Beast)
class BeastEvade(DecisiveAction):
    id = 'beast_evade'
    name = ls("beast.evade.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        self.source.inbound_accuracy_bonus = -6
        self.session.say(ls("beast.evade.text").format(source.name))


@AttachedAction(Beast)
class BeastGrowl(DecisiveAction):
    id = 'beast_growl'
    name = ls("beast.growl.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        self.session.say(ls("beast.growl.text").format(source.name))


@RegisterWeapon
class BeastWeapon(MeleeWeapon):
    id = 'beast_weapon'
    name = ls("beast.weapon.name")

    cubes = 3
    damage_bonus = 0
    energy_cost = 2
    accuracy_bonus = 1


@AttachedAction(BeastWeapon)
class BeastAttack(MeleeAttack):
    id = 'beast_attack'
    name = ls("beast.attack.name")
    target_type = Enemies()


@AttachedAction(BeastWeapon)
class BeastAttackTwo(MeleeAttack):
    id = 'Beast_attack_Two'
    name = ls("beast.AttackTwo.name")
    target_type = Enemies()

    async def func(self, source, target):

        self.weapon.damage_bonus = 1
        final_damage = self.calculate_damage(source, target)

        post_damage = await self.publish_post_damage_event(source, target, final_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        self.session.say(ls("beast.AttackTwo.text").format(source.name, target.name, final_damage))
        self.weapon.damage_bonus = 0

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage


@AttachedAction(BeastWeapon)
class BeastBite(MeleeAttack):
    id = 'beast_bite'
    name = ls("beast.bite.name")

    async def func(self, source, target):
        target.hp = max(0, target.hp - 1)
        self.session.say(ls("beast.bite.text").format(source.name, target.name))
