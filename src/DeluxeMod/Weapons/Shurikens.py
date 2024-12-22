from VegansDeluxe.core import PostDamageGameEvent
from VegansDeluxe.core import RangedAttack, RegisterWeapon, Entity, AttachedAction, OwnOnly, FreeWeaponAction
from VegansDeluxe.core.Session import Session
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import RangedWeapon


@RegisterWeapon
class Shurikens(RangedWeapon):
    id = 'shurikens'
    name = ls("weapon.shurikens.name")
    description = ls("weapon.shurikens.description")

    cubes = 1
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.double_shuriken = False
        self.ammo = 4


@AttachedAction(Shurikens)
class ShurikenAttack(RangedAttack):
    def __init__(self, session: Session, source: Entity, weapon: Shurikens):
        super().__init__(session, source, weapon)

    async def func(self, source, target):
        source.energy = max(source.energy - self.weapon.energy_cost, 0)

        if self.weapon.ammo > 0:
            if self.weapon.double_shuriken and self.weapon.ammo >= 2:
                await self.perform_double_shuriken_attack(source, target)
            else:
                await self.perform_single_shuriken_attack(source, target)
        else:
            self.session.say(ls("weapon.shurikens.no_ammo_text").format(source.name))

    async def shuriken_attack(self, source, target):
        total_damage = self.calculate_damage(source, target)
        post_damage = await self.publish_post_damage_event(source, target, total_damage)
        target.inbound_dmg.add(source, post_damage, self.session.turn)
        source.outbound_dmg.add(target, post_damage, self.session.turn)

        if post_damage == 0:
            self.session.say(
                self.MISS_MESSAGE.format(source_name=source.name, attack_text=self.ATTACK_TEXT, target_name=target.name,
                                         weapon_name=self.weapon.name)
            )
        else:
            self.session.say(
                self.ATTACK_MESSAGE.format(attack_emoji=self.ATTACK_EMOJI, source_name=source.name,
                                           attack_text=self.ATTACK_TEXT, target_name=target.name,
                                           weapon_name=self.weapon.name, damage=post_damage)
            )

    async def perform_single_shuriken_attack(self, source, target):
        if self.weapon.ammo > 0:
            await self.shuriken_attack(source, target)
            self.weapon.ammo -= 1

    async def perform_double_shuriken_attack(self, source, target):
        if self.weapon.ammo >= 2:
            await self.shuriken_attack(source, target)
            await self.shuriken_attack(source, target)
            self.weapon.ammo -= 2

    async def publish_post_damage_event(self, source: Entity, target: Entity, damage: int) -> int:
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage


@AttachedAction(Shurikens)
class SwitchShurikenMode(FreeWeaponAction):
    id = 'switch_shuriken_mode'
    name = ls("weapon.shurikens.switch_shuriken_mode")
    target_type = OwnOnly()
    priority = -10

    async def func(self, source, target):
        self.weapon.double_shuriken = not self.weapon.double_shuriken
        if self.weapon.double_shuriken:
            self.session.say(ls("weapon.shurikens.switch_to_double_shuriken_text").format(source.name))
        else:
            self.session.say(ls("weapon.shurikens.switch_to_single_shuriken_text").format(source.name))


@AttachedAction(Shurikens)
class PickUpShuriken(FreeWeaponAction):
    id = 'pick_up'
    name = ls("weapon.shurikens.pickup.name")
    target_type = OwnOnly()

    def __init__(self, session: Session, source: Entity, weapon: Shurikens):
        super().__init__(session, source, weapon)
        self.weapon = weapon

    @property
    def hidden(self) -> bool:
        return self.weapon.ammo >= 4

    async def func(self, source: Entity, target: Entity):
        self.weapon.ammo = 4
        self.session.say(ls("weapon.shurikens.shuriken_pickup_text").format(source.name))
