from VegansDeluxe.core import ActionTag, Attack, AttachedAction, DeliveryPackageEvent, DeliveryRequestEvent, \
    Enemies, Entity, EventContext, MeleeAttack, Next, RegisterWeapon, percentage_chance
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

COOLDOWN = 3


@RegisterWeapon
class ChainedDagger(MeleeWeapon):
    id = 'chained_dagger'
    name = ls("deluxe.weapon.chained_dagger.name")
    description = ls("deluxe.weapon.chained_dagger.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.cooldown_turn = 0


@AttachedAction(ChainedDagger)
class ChainedDaggerAttack(MeleeAttack):
    pass


@AttachedAction(ChainedDagger)
class SwapWeapon(Attack):
    id = 'swap_weapon'
    name = ls("deluxe.weapon.chained_dagger.action.name")
    priority = -1
    target_type = Enemies()

    @property
    def hidden(self) -> bool:
        return self.session.turn < self.weapon.cooldown_turn

    async def func(self, source: Entity, target: Entity):
        @Next(self.session.id, event=DeliveryPackageEvent)
        async def delivery(context: EventContext[DeliveryPackageEvent]):
            action_manager = context.action_manager

            self.weapon.cooldown_turn = self.session.turn + COOLDOWN
            damage = await self.attack(source, target)
            if not damage.calculated:
                self.session.say(ls("deluxe.weapon.chained_dagger.action_miss").format(source.name, target.name),
                                 source_id=source.id, target_id=target.id)
                return

            target_reloading = False
            for action in action_manager.get_queued_entity_actions(self.session, target):
                if ActionTag.RELOAD in action.tags:
                    target_reloading = True

            if target_reloading or percentage_chance(passive_chance(target)):
                self.session.say(ls("deluxe.weapon.chained_dagger.action.text").format(source.name, target.name),
                                 source_id=source.id, target_id=target.id)
                source.weapon, target.weapon = target.weapon, source.weapon
                await action_manager.update_entity_actions(self.session, source)
                await action_manager.update_entity_actions(self.session, target)
            else:
                self.session.say(ls("deluxe.weapon.chained_dagger.action_miss").format(source.name, target.name),
                                 source_id=source.id, target_id=target.id)

        await self.event_manager.publish(DeliveryRequestEvent(self.session.id, self.session.turn))


def passive_chance(target: Entity):
    return (target.max_energy - target.energy) * 10 + 10
