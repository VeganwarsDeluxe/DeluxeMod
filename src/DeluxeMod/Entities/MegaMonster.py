import random

from DeluxeMod.Entities.Android import Android


class MegaMonster(Android):
    async def choose_act(self, session, action_manager):
        try:
            await super().choose_act(session, action_manager)
        except IndexError:
            self.choose_fallback_act(session, action_manager)
        except AttributeError as error:
            if "'NoneType' object has no attribute 'queued'" not in str(error):
                raise
            action_manager.action_queue = [
                action for action in action_manager.action_queue
                if action is not None
            ]
            self.choose_fallback_act(session, action_manager)

    def choose_fallback_act(self, session, action_manager):
        for action_id in ("attack", "reload", "approach", "skip"):
            action = action_manager.get_action(session, self, action_id)
            if not action or action.hidden or action.removed:
                continue
            if action.targets:
                action.target = random.choice(action.targets)
            action_manager.queue_action_instance(action)
            return
