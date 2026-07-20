from VegansDeluxe.core import ls
from VegansDeluxe.matchmakery import Dungeon


class Room57(Dungeon):
    """A three-room run: slimes, Androids, then the Elemental."""

    name = ls("matches.room_57")

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
            # Each level is a clean, ordinary Match: it creates a fresh player
            # and its own NPCs through the Match's existing join logic. Dead
            # players are included and therefore return alive in the new room.
            await current.join_session(entity.id, entity.name)
