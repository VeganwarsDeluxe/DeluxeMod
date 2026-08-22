from VegansDeluxe.core import AttachedAction, MeleeAttack, PreDamagesGameEvent, RegisterEvent, RegisterWeapon
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.core.Weapons.Weapon import MeleeWeapon


@RegisterWeapon
class Pen(MeleeWeapon):
    id = 'pen'
    name = ls("deluxe.weapon.pen.name")
    description = ls("deluxe.weapon.pen.description")

    cubes = 3
    accuracy_bonus = 2
    energy_cost = 2
    damage_bonus = 0

    def __init__(self, session_id: str, entity_id: str):
        super().__init__(session_id, entity_id)
        self.proc_count = 0

        @RegisterEvent(session_id, event=PreDamagesGameEvent)
        async def handle_parity(context):
            session = context.session
            source = session.get_entity(entity_id)
            if source is None or source.weapon is not self:
                return

            for target in session.entities:
                if target == source:
                    continue

                dealt = sum(log.damage for log in target.inbound_dmg.damages if log.source == source)
                received = sum(log.damage for log in source.inbound_dmg.damages if log.source == target)

                if dealt and dealt == received:
                    source.inbound_dmg.cancel(target)
                    source.energy = min(source.energy + self.energy_cost, source.max_energy)
                    self.proc_count += 1
                    session.say(ls("deluxe.weapon.pen.text").format(source.name, target.name),
                                source_id=source.id, target_id=target.id)


@AttachedAction(Pen)
class PenAttack(MeleeAttack):
    pass
