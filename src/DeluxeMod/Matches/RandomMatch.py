import random

from VegansDeluxe.core import ls
from VegansDeluxe.matchmakery.Events.MatchEvents import DisplayItemChoiceEvent

from DeluxeMod.Matches.BasicMatch import BasicMatch


class RandomMatch(BasicMatch):
    """A basic match that equips every player automatically at random."""

    name = ls("deluxe.matches.random")

    async def distribute_starting_items(self):
        for player in self.session.entities:
            given = {item.id for item in player.items}
            for _ in range(self.item_amount):
                pool = [item for item in self.item_pool if item.id not in given]
                if not pool:
                    pool = self.item_pool
                item = random.choice(pool)()
                player.items.append(item)
                given.add(item.id)

            event = DisplayItemChoiceEvent(self.session.id, self.session.turn, player.id)
            await self.engine.event_manager.publish(event)

    async def choose_weapons(self):
        for player in self.session.entities:
            if player in self.players_with_weapon_choice:
                continue
            player.weapon = random.choice(self.weapon_pool)(self.session.id, player.id)
            self.players_with_weapon_choice.append(player)

        await self.attempt_finish_weapon_choice()

    async def choose_skills(self):
        for player in self.session.entities:
            if player in self.players_with_skill_choice:
                continue

            skill_pool = self.player_skill_pool(player)
            given = {skill.id for skill in player.skills}
            for _ in range(self.skill_amount):
                pool = [skill for skill in skill_pool if skill.id not in given]
                if not pool:
                    pool = skill_pool
                skill = random.choice(pool)()
                await player.attach_state(skill, self.engine.event_manager)
                given.add(skill.id)

            self.players_with_skill_choice.append(player)

        await self.attempt_finish_skill_choice()
