from VegansDeluxe.core import ls
from VegansDeluxe.matchmakery import Dungeon

class Room57(Dungeon):
    name = ls("deluxe.matches.room_57")
    description = ls("deluxe.matches.room_57.description")

    async def create_first_match(self):
        from DeluxeMod.Matches.SlimeMatch import SlimeMatch
        return SlimeMatch(self.id, self.engine)

    async def create_next_match(self, previous):
        from DeluxeMod.Matches.AndroidMatch import AndroidMatch
        from DeluxeMod.Matches.ElementalMatch import ElementalMatch
        from DeluxeMod.Matches.SlimeMatch import SlimeMatch

        if isinstance(previous, SlimeMatch):
            return AndroidMatch(self.id, self.engine)
        if isinstance(previous, AndroidMatch):
            return ElementalMatch(self.id, self.engine)
        return None

    async def initialize_match(self, previous, current):
        if previous is None:
            return

        for entity in self.dungeon_players(previous):
            await current.join_session(entity.id, entity.name)
