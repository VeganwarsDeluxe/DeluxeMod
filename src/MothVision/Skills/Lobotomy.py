from VegansDeluxe.core import RegisterState
from VegansDeluxe.core import Session
from VegansDeluxe.core import StateContext
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls

from MothVision.Items.Needle import Needle


class Lobotomy(Skill):
    id = 'lobotomy'
    name = ls("moth_vision.skill.lobotomy.name")
    description = ls("moth_vision.skill.lobotomy.description")


@RegisterState(Lobotomy)
async def register(root_context: StateContext[Lobotomy]):
    session: Session = root_context.session
    source = root_context.entity

    source.items.append(Needle())
