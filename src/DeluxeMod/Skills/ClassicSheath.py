from VegansDeluxe.core import EventContext, ExecuteActionEvent, RegisterEvent, RegisterState, Session, \
    StateContext, percentage_chance
from VegansDeluxe.core.Skills.Skill import Skill
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild.Items.ThrowingKnife import ThrowingKnife, ThrowingKnifeAction
from VegansDeluxe.rebuild.States.Bleeding import Bleeding

DAMAGE_BONUS = 1
ACCURACY_BONUS = 1
EXTRA_KNIVES = 1


class ClassicSheath(Skill):
    id = 'classic_sheath'
    name = ls("deluxe.skill.classic_sheath.name")
    description = ls("deluxe.skill.classic_sheath.description")

    requires_item_id = ThrowingKnife.id


class ClassicSheathThrow(ThrowingKnifeAction):
    """
    Reconstructed copy of ThrowingKnifeAction, same pattern AluminiumBat uses for its
    steal+retaliate grenades: intercept and cancel the original in ExecuteActionEvent,
    then execute this modified version directly. Needed because hit_chance is a
    read-only property (no setter) and the base func() has no hook for bonus damage
    or skipping the energy cost, so patching the live action instance isn't possible.
    """

    @property
    def hit_chance(self):
        return super().hit_chance + ACCURACY_BONUS

    async def func(self, source, target):
        if not percentage_chance(self.hit_chance):
            self.session.say(ls("rebuild.item.throwing_knife_name.miss").format(source.name, target.name),
                             source_id=source.id, target_id=target.id)
            return

        bleeding = target.get_state(Bleeding)
        if bleeding.active:
            bleeding.bleeding -= 1
        bleeding.active = True

        await self.session.lose_hp(target, DAMAGE_BONUS)

        self.session.say(
            ls("rebuild.item.throwing_knife.text").format(source.name, target.name),
            source_id=source.id, target_id=target.id
        )


@RegisterState(ClassicSheath)
async def register(root_context: StateContext[ClassicSheath]):
    session: Session = root_context.session
    source = root_context.entity

    for _ in range(EXTRA_KNIVES):
        source.items.append(ThrowingKnife())

    @RegisterEvent(session.id, event=ExecuteActionEvent, priority=-10)
    async def upgrade_throw(context: EventContext[ExecuteActionEvent]):
        action = context.event.action
        if action.source != source or action.id != ThrowingKnifeAction.id:
            return

        action.canceled = True
        replacement = ClassicSheathThrow(context.session, source, action.item)
        replacement.target = action.target
        await replacement.execute()
