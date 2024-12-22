import random

from VegansDeluxe.core import AttachedAction, RegisterItem, ActionTag
from VegansDeluxe.core import DecisiveItem
from VegansDeluxe.core import Enemies
from VegansDeluxe.core import Entity
from VegansDeluxe.core import Item
from VegansDeluxe.core import Session, PostDamageGameEvent
from VegansDeluxe.core.Actions.Action import filter_targets
from VegansDeluxe.core.Translator.LocalizedList import LocalizedList
from VegansDeluxe.core.Translator.LocalizedString import ls


@RegisterItem
class EnergyGrenade(Item):
    id = 'energy_grenade'
    name = ls("item.energy_grenade_name")


@AttachedAction(EnergyGrenade)
class EnergyGrenadeAction(DecisiveItem):
    id = 'energy_grenade'
    name = ls("item.energy_grenade_name")
    target_type = Enemies()

    def __init__(self, session: Session, source: Entity, item: Item):
        super().__init__(session, source, item)
        self.tags += [ActionTag.HARMFUL]
        self.range = 1  # Number of targets to hit, set to 1 for now

    async def func(self, source, target):
        damage = 0

        targets = []
        for _ in range(self.range):
            target_pool = list(filter(lambda t: t not in targets,
                                      filter_targets(source, Enemies(), self.session.entities)
                                      ))
            if not target_pool:
                continue  # Skip if no more valid targets
            selected_target = random.choice(target_pool)
            damage = selected_target.energy  # Damage based on target's energy
            post_damage = await self.publish_post_damage_event(source, selected_target, damage)
            selected_target.inbound_dmg.add(source, post_damage, self.session.turn)
            source.outbound_dmg.add(source, post_damage, self.session.turn)
            targets.append(selected_target)

        # Reduce the source's energy
        source.energy = max(source.energy - 2, 0)

        # Announce the action
        self.session.say(
            ls("item.energy_grenade_text")
            .format(source.name, damage, LocalizedList([t.name for t in targets]))
        )

    async def publish_post_damage_event(self, source, target, damage):
        message = PostDamageGameEvent(self.session.id, self.session.turn, source, target, damage)
        await self.event_manager.publish(message)
        return message.damage

    @property
    def blocked(self):
        return self.source.energy < 2
