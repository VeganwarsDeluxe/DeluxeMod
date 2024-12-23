import uuid

from VegansDeluxe.core import AttachedAction, FreeAction, OwnOnly, ls
from VegansDeluxe.core.Actions.EntityActions import ReloadAction, SkipTurnAction, ApproachAction
from VegansDeluxe.core.Entities.Entity import Entity
from VegansDeluxe.core.Question.Question import Question
from VegansDeluxe.core.Question.QuestionEvents import QuestionGameEvent


class TelegramEntity(Entity):
    def __init__(self, session_id: str, user_name, user_id, code=''):
        super().__init__(session_id)
        self.user_id = user_id
        self.id = str(user_id) if user_id else str(uuid.uuid4())

        self.name = user_name
        self.locale = code

        self.skill_cycle = 0





@AttachedAction(TelegramEntity)
class ApproachAction(ApproachAction):
    pass


@AttachedAction(TelegramEntity)
class ReloadAction(ReloadAction):
    pass


@AttachedAction(TelegramEntity)
class SkipTurnAction(SkipTurnAction):
    pass
