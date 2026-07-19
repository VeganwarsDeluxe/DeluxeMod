from VegansDeluxe.core import AttackGameEvent
from VegansDeluxe.core import AttachedAction
from VegansDeluxe.core import Entity
from VegansDeluxe.core import EventContext
from VegansDeluxe.core import MeleeAttack
from VegansDeluxe.core import RegisterEvent
from VegansDeluxe.core import RegisterWeapon
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon
from VegansDeluxe.rebuild import Aflame


@RegisterWeapon
class Gunbai(MeleeWeapon):
    id = 'gunbai'
    name = ls("weapon.gunbai.name")
    description = ls("weapon.gunbai.description")

    cubes = 2
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.signal_turn = 0
        self.signal_target_id = None

        @RegisterEvent(session_id, event=AttackGameEvent)
        async def increase_team_weapon_damage(context: EventContext[AttackGameEvent]):
            if context.event.turn != self.signal_turn:
                return
            if context.event.target.id != self.signal_target_id:
                return
            owner = context.session.get_entity(self.entity_id)
            if not owner or not owner.is_ally(context.event.source):
                return
            if context.event.source == owner and context.event.source.weapon == self:
                return
            if not context.event.damage:
                return
            context.event.damage += 1

@AttachedAction(Gunbai)
class GunbaiAttack(MeleeAttack):
    async def func(self, source: Entity, target: Entity):
        damage = await self.attack(source, target)

        if damage.calculated:
            self.weapon.signal_turn = self.session.turn
            self.weapon.signal_target_id = target.id
            self.session.say(ls("weapon.gunbai.signal_text").format(source.name))

            aflame = target.get_state(Aflame)
            if aflame and aflame.flame:
                aflame.flame += 1
                aflame.dealer = source
                aflame.extinguished = False
                self.session.say(ls("weapon.gunbai.fire_text").format(source.name, target.name))

        return damage
