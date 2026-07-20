from DeluxeMod.Entities.MegaMonster import MegaMonster


class Rat(MegaMonster):
    def __init__(self, session_id: str, name="Rat"):
        super().__init__(session_id, name=name)
        self.items = []
        self.states = []
        self.hp = 4
        self.max_hp = 4
        self.team = "mega_monsters"

    def choose_items(self):
        return ()

    def choose_skills(self):
        return []
