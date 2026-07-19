from VegansDeluxe.core import ActionTag
from VegansDeluxe.core import AttachedAction
from VegansDeluxe.core import DeliveryPackageEvent
from VegansDeluxe.core import DeliveryRequestEvent
from VegansDeluxe.core import EventContext
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core import Next
from VegansDeluxe.core import AttackGameEvent
from VegansDeluxe.core import RegisterEvent
from VegansDeluxe.core import RegisterWeapon
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon


@RegisterWeapon
class ButterflyKnife(MeleeWeapon):
    id = 'butterfly_knife'
    name = ls("weapon.butterfly_knife.name")
    description = ls("weapon.butterfly_knife.description")

    cubes = 3
    accuracy_bonus = 1
    energy_cost = 2
    damage_bonus = 0

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.target_action_bonus_damage = 0

        @RegisterEvent(session_id, event=AttackGameEvent)
        async def handle_opponent_miss(context: EventContext[AttackGameEvent]):
            target = context.event.target
            source = context.event.source
            if target.id != self.entity_id:
                return
            if not isinstance(target.weapon, ButterflyKnife):
                return
            if context.event.damage:
                return

            target.energy = min(target.energy + 1, target.max_energy)
            context.session.say(ls("weapon.butterfly_knife.miss_energy").format(target.name))


@AttachedAction(ButterflyKnife)
class ButterflyKnifeAttack(MeleeAttack):
    async def func(self, source, target):
        self.weapon.target_action_bonus_damage = 0

        @Next(self.session.id, event=DeliveryPackageEvent)
        async def delivery(context: EventContext[DeliveryPackageEvent]):
            for action in context.action_manager.get_queued_entity_actions(self.session, target):
                if ActionTag.SKIP in action.tags or ActionTag.RELOAD in action.tags:
                    self.weapon.target_action_bonus_damage = 3
                    break

        await self.event_manager.publish(DeliveryRequestEvent(self.session.id, self.session.turn))
        bonus_damage = self.weapon.target_action_bonus_damage
        damage = await self.attack(source, target, bonus_damage=bonus_damage)
        if bonus_damage and damage.calculated:
            self.session.say(ls("weapon.butterfly_knife.bonus_damage").format(source.name, target.name))
        return damage
