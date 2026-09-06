from VegansDeluxe.core import AttachedAction, EventContext, HPLossGameEvent, MeleeAttack, RegisterEvent, \
    RegisterWeapon, percentage_chance
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon

GROWTH_CHANCE = 67


@RegisterWeapon
class FryingPan(MeleeWeapon):
    id = 'frying_pan'
    name = ls("deluxe.weapon.frying_pan.name")
    description = ls("deluxe.weapon.frying_pan.description")

    energy_cost = 2
    damage_bonus = 0

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.cubes = 2
        self.accuracy_bonus = 2

        @RegisterEvent(session_id, event=HPLossGameEvent)
        async def grow_on_enemy_hp_loss(context: EventContext[HPLossGameEvent]):
            entity = context.session.get_entity(entity_id)
            if not entity or entity.weapon is not self:
                return

            victim = context.event.source
            if victim == entity or entity.is_ally(victim):
                return

            if not percentage_chance(GROWTH_CHANCE):
                return

            self.cubes += 1
            self.accuracy_bonus = max(self.accuracy_bonus - 1, 0)
            context.session.say(ls("deluxe.weapon.frying_pan.grow").format(entity.name, self.cubes),
                                source_id=entity_id, target_id=entity_id)


@AttachedAction(FryingPan)
class FryingPanAttack(MeleeAttack):
    pass
