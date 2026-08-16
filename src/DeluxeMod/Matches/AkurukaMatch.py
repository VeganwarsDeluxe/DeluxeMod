from VegansDeluxe.core import ls

from DeluxeMod.Matches.BasicMatch import BasicMatch
from DeluxeMod.Weapons.Akuruka import Akuruka


class AkurukaMatch(BasicMatch):
    name = ls('deluxe.matches.akuruka')

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)
        self.weapon_pool = [Akuruka]
        self.item_pool = []
        self.skill_pool = []
        self.item_amount = 0
        self.skill_amount = 0
        self.weapon_choice_window = 1
        self.item_choice_window = 0
        self.skill_choice_window = 0
