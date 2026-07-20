from VegansDeluxe.rebuild import Fist

from DeluxeMod.Entities.MegaMonster import MegaMonster


class MegaRhino(MegaMonster):
    def __init__(self, session_id: str, party_size: int, name="Mega-Rhino"):
        super().__init__(session_id, name=name)
        self.weapon = Fist(self.session_id, self.id)
        self.items = []
        self.states = []
        self.hp = 5 + party_size * 3
        self.max_hp = self.hp
        self.energy = 3 + party_size
        self.max_energy = self.energy
        self.weapon.damage_bonus = party_size * 2
        self.team = "mega_monsters"

    def choose_weapon(self):
        return Fist(self.session_id, self.id)

    def choose_items(self):
        return ()

    def choose_skills(self):
        return []
