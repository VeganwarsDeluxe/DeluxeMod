import random

from VegansDeluxe.core import RangedAttack, FreeWeaponAction, RegisterWeapon, Entity, Enemies, OwnOnly, AttachedAction
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Events import PostDamageGameEvent
from VegansDeluxe.core.Session import Session
from VegansDeluxe.core.Translator.LocalizedList import LocalizedList
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import RangedWeapon
from VegansDeluxe.rebuild import Aflame


@RegisterWeapon
class GrenadeLauncher(RangedWeapon):
    id = 'grenade_launcher'
    name = ls("weapon.grenade_launcher.name")
    description = ls("weapon.grenade_launcher.description")

    cubes = 4
    accuracy_bonus = 2
    energy_cost = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_molotov = False  # Начальный режим - гранаты


@AttachedAction(GrenadeLauncher)
class GrenadeLauncherAttack(RangedAttack):
    def __init__(self, session: Session, source: Entity, weapon: GrenadeLauncher):
        super().__init__(session, source, weapon)
        self.targets_count = 2

    async def func(self, source, target):
        if self.weapon.is_molotov:
            await self.perform_molotov_attack(source, target)
        else:
            await self.perform_grenade_attack(source, target)

    async def perform_grenade_attack(self, source, target):
        base_damage = self.calculate_damage(source, target)
        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        targets = self.form_target_list(source, target)

        for target in targets:
            post_damage = await self.publish_post_damage_event(source, target, base_damage)
            target.inbound_dmg.add(source, post_damage, self.session.turn)
            source.outbound_dmg.add(target, post_damage, self.session.turn)

        if not base_damage:
            self.session.say(ls("weapon.grenade_launcher.grenade.text_miss").format(source.name, target.name))
        else:
            self.session.say(ls("weapon.grenade_launcher.grenade.text").format(source.name, base_damage,
                                                                        LocalizedList([t.name for t in targets])))

    async def perform_molotov_attack(self, source, target):
        # Пропоную так перевіряти попадання. calculate_damage використовує звичайні стати зброї, і поверне 0 в разі
        # промаху.
        base_damage = self.calculate_damage(source, target)

        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        targets = self.form_target_list(source, target)

        for t in targets:
            aflame = t.get_state(Aflame)
            if not base_damage:
                break
            aflame.add_flame(self.session, t, source, 1)

            post_damage = await self.publish_post_damage_event(source, t, 0)
            t.inbound_dmg.add(source, post_damage, self.session.turn)
            source.outbound_dmg.add(source, post_damage, self.session.turn)

        if base_damage:
            self.session.say(ls("weapon.grenade_launcher.molotov.text")
                             .format(source.name, LocalizedList([t.name for t in targets])))
        else:
            self.session.say(ls("weapon.grenade_launcher.molotov.text_miss")
                             .format(source.name, target.name))

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


@AttachedAction(GrenadeLauncher)
class SwitchGrenadeLauncher(FreeWeaponAction):
    id = 'switch_grenade_launcher'
    target_type = OwnOnly()
    priority = -10

    @property
    def name(self):
        return ls("weapon.grenade_launcher.switch_to_grenade") if self.weapon.is_molotov else \
            ls("weapon.grenade_launcher.switch_to_molotov")

    async def func(self, source, target):
        self.weapon.is_molotov = not self.weapon.is_molotov
