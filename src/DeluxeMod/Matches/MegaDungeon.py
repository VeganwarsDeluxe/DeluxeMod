import random
from math import floor

from VegansDeluxe.core import (
    EventContext,
    At,
    PostDamageGameEvent,
    PostDeathsGameEvent,
    PreMoveGameEvent,
    RegisterEvent,
    ls,
    percentage_chance,
)
from VegansDeluxe.matchmakery import Dungeon
from VegansDeluxe.matchmakery.Events.MatchEvents import DisplayItemChoiceEvent
from VegansDeluxe.rebuild import DamageThreshold, Stun

from DeluxeMod.Entities.MegaRhino import MegaRhino
from DeluxeMod.Entities.Rat import Rat
from DeluxeMod.Entities.Skeleton import Skeleton
from DeluxeMod.Matches.BasicMatch import BasicMatch


class MegaDungeon(Dungeon):
    name = ls("matches.mega_dungeon")

    async def create_first_match(self):
        return MegaRatMatch(self.id, self.engine)

    async def create_next_match(self, previous):
        if isinstance(previous, MegaRatMatch):
            return MegaRatSkeletonMatch(self.id, self.engine)
        if isinstance(previous, MegaRatSkeletonMatch):
            return MegaRhinoMatch(self.id, self.engine)
        return None

    async def initialize_match(self, previous, current):
        if previous is None:
            return
        for entity in self.dungeon_players(previous):
            await current.join_session(entity.id, entity.name)


class MegaMatch(BasicMatch):
    player_team = "players"

    async def init_async(self):
        await super().init_async()
        self.register_mega_rules()

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)
        player.team = self.player_team
        return player

    async def attach_monster(self, monster):
        import DeluxeMod.content

        self.session.attach_entity(monster)
        await self.engine.attach_states(monster, DeluxeMod.content.all_states)
        return monster

    async def distribute_starting_items(self):
        for player in self.session.get_team(self.player_team):
            given = []
            for _ in range(self.item_amount):
                item = random.choice(self.item_pool)()
                pool = list(filter(lambda i: i.id not in given, self.item_pool))
                if pool:
                    item = random.choice(pool)()
                given.append(item.id)
                player.items.append(item)

            event = DisplayItemChoiceEvent(self.session.id, self.session.turn, player.id)
            await self.engine.event_manager.publish(event)

    def register_mega_rules(self):
        @RegisterEvent(self.session.id, event=PreMoveGameEvent)
        async def roll_turn_armor(context: EventContext[PreMoveGameEvent]):
            session = context.session
            for entity in session.alive_entities:
                if isinstance(entity, Rat) and percentage_chance(2):
                    entity.metadata["mega_armored_turn"] = session.turn
                    session.say(ls("mega.rat.armor").format(entity.name))
                if isinstance(entity, MegaRhino) and percentage_chance(60):
                    entity.metadata["mega_armored_turn"] = session.turn
                    session.say(ls("mega.rhino.armor").format(entity.name))

        @RegisterEvent(self.session.id, event=PostDamageGameEvent, priority=-100)
        async def apply_turn_armor(context: EventContext[PostDamageGameEvent]):
            event = context.event
            target = event.target
            if target.metadata.get("mega_armored_turn") == event.turn:
                event.damage = 0

        @RegisterEvent(self.session.id, event=PostDeathsGameEvent)
        async def schedule_skeleton_resurrection(context: EventContext[PostDeathsGameEvent]):
            session = context.session
            for skeleton in session.entities:
                if not isinstance(skeleton, Skeleton) or not skeleton.dead:
                    continue
                if skeleton.metadata.get("mega_resurrection_scheduled"):
                    continue
                skeleton.metadata["mega_resurrection_scheduled"] = True
                turn = session.turn + 5

                @At(
                    session.id,
                    turn=turn,
                    event=PostDeathsGameEvent,
                )
                async def resurrect(resurrection_context: EventContext[PostDeathsGameEvent], entity=skeleton):
                    entity.metadata["mega_resurrection_scheduled"] = False
                    if any(not ally.dead and ally.is_ally(entity) for ally in session.entities):
                        entity.dead = False
                        entity.hp = max(1, floor(entity.max_hp / 2))
                        entity.energy = 0
                        entity.get_state(Stun).stun = 1
                        session.say(ls("mega.skeleton.resurrect").format(entity.name))


class MegaRatMatch(MegaMatch):
    name = ls("matches.mega_dungeon.rats")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)
        self.rats = 0

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)
        self.rats += 1
        rat = Rat(self.id, name=ls("mega.rat.number").format(self.rats))
        await self.attach_monster(rat)
        return player


class MegaRatSkeletonMatch(MegaMatch):
    name = ls("matches.mega_dungeon.rats_and_skeletons")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)
        self.rats = 0
        self.skeletons = 0
        self.skill_amount = 3

    async def join_session(self, user_id, user_name):
        player = await super().join_session(user_id, user_name)

        self.rats += 1
        rat = Rat(self.id, name=ls("mega.rat.number").format(self.rats))
        await self.attach_monster(rat)

        self.skeletons += 1
        skeleton = Skeleton(self.id, name=ls("mega.skeleton.number").format(self.skeletons))
        await self.attach_monster(skeleton)
        return player


class MegaRhinoMatch(MegaMatch):
    name = ls("matches.mega_dungeon.mega_rhinos")

    def __init__(self, chat_id, engine):
        super().__init__(chat_id, engine)
        self.rhinos_spawned = False
        self.skill_amount = 3

    async def launch(self):
        party_size = len(self.session.get_team(self.player_team))
        self.skill_amount = 5 if party_size == 1 else 3
        if not self.rhinos_spawned:
            rhino_count = max(1, round(party_size / 5) + 1)
            for index in range(1, rhino_count + 1):
                rhino = MegaRhino(
                    self.id,
                    party_size,
                    name=ls("mega.rhino.number").format(index),
                )
                await self.attach_monster(rhino)
                rhino.get_state(DamageThreshold).threshold = 9
            self.rhinos_spawned = True
        await super().launch()
