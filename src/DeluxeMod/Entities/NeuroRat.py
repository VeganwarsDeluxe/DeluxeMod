import random

from VegansDeluxe.core import AttachedAction, ls
from VegansDeluxe.core import OwnOnly
from VegansDeluxe.core.Actions.Action import DecisiveAction

import DeluxeMod.content as content
from VegansDeluxe.core.Entities.NPC import NPC


class NeuroRat(NPC):
    def __init__(self, session_id: str, name="NeuroRat", rat_id=""):
        # TODO: Localization!
        super().__init__(session_id, name=name)

        # if not rat_id:
        #    self.battle_ai = battle_ai
        # else:
        #    self.battle_ai = BattleAI(engine, ai_id=rat_id)

        self.weapon = random.choice(content.all_weapons)(self.session_id, self.id)

        self.hp = 4
        self.max_hp = 4
        self.energy = 5
        self.max_energy = 5

        self.items = []
        self.choose_items()
        self.choose_skills()

    def choose_items(self):
        given = []
        for _ in range(2):
            item = random.choice(content.game_items_pool)()
            pool = list(filter(lambda i: i.id not in given, content.game_items_pool))
            if pool:
                item = random.choice(pool)()
            given.append(item.id)
            self.items.append(item)

    def choose_skills(self):
        given = []
        for _ in range(2):
            skill = random.choice(content.all_skills)()
            pool = list(filter(lambda i: i.id not in given, content.all_skills))
            if pool:
                skill = random.choice(pool)()
            given.append(skill.id)
            self.states.append(skill)

    async def choose_act(self, session, action_manager):
        await super().choose_act(session, action_manager)
        """
        training_data = battle_ai.compile_training_data(session, self, choice_index=0)

        best_action, chart = battle_ai.predict_action(
            training_data["player"], training_data["opponents"], training_data["actions"], training_data["turn"]
        )
        action = engine.action_manager.get_action(session, self, best_action.id)
        if action.targets:
            action.target = random.choice(action.targets)
        else:
            action_id = sorted(chart, key=lambda x: chart[x])[1]
            action = engine.action_manager.get_action(session, self, action_id)
            action.target = random.choice(action.targets)

        if action.type == "item":
            if action.item:
                self.items.remove(action.item)
            else:
                pass

        engine.action_manager.queue_action_instance(action)

        self.output_decision(chart, training_data, best_action)
        """

    def output_decision(self, chart, data, best_action):
        tts = "-" * 14
        tts += f"\n{chart}\n"
        tts += f"chose {best_action}. from\n"
        tts += f"{data}\n"
        tts += "-" * 14
        print(tts)


@AttachedAction(NeuroRat)
class SlimeReload(DecisiveAction):
    id = 'reload'
    name = ls("slime.reload.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        self.session.say(ls("slime.reload.text").format(source.name, source.max_energy))
        source.energy = source.max_energy


@AttachedAction(NeuroRat)
class SlimeApproach(DecisiveAction):
    id = 'approach'
    name = ls("slime.approach.name")
    target_type = OwnOnly()

    async def func(self, source, target):
        source.nearby_entities = list(filter(lambda t: t != source, self.session.entities))
        for entity in source.nearby_entities:
            entity.nearby_entities.append(source) if source not in entity.nearby_entities else None
        self.session.say(ls("slime.approach.text").format(source.name))
