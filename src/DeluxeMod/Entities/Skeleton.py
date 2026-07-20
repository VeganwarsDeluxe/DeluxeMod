from DeluxeMod.Entities.MegaMonster import MegaMonster
from DeluxeMod.Weapons.Sword import Sword


class Skeleton(MegaMonster):
    def __init__(self, session_id: str, name="Skeleton"):
        super().__init__(session_id, name=name)
        self.weapon = Sword(self.session_id, self.id)
        self.items = []
        self.states = []
        self.hp = 4
        self.max_hp = 4
        self.team = "mega_monsters"

    def choose_weapon(self):
        return Sword(self.session_id, self.id)

    def choose_items(self):
        return ()

    def choose_skills(self):
        return []
