from VegansDeluxe.core import ActionTag, AttachedAction, DecisiveItem, Item, RegisterItem, SelfOnly
from VegansDeluxe.core.Translator.LocalizedString import ls
from VegansDeluxe.rebuild import Bleeding

MEAT_HP = 1
MEAT_ENERGY = 2


@RegisterItem
class PieceOfMeat(Item):
    id = 'piece_of_meat'
    name = ls("deluxe.item.piece_of_meat_name")


@AttachedAction(PieceOfMeat)
class PieceOfMeatAction(DecisiveItem):
    id = 'piece_of_meat'
    name = ls("deluxe.item.piece_of_meat_name")
    target_type = SelfOnly()

    tags = DecisiveItem.tags + [ActionTag.MEDICINE]

    async def func(self, source, target):
        source.hp = min(source.hp + MEAT_HP, source.max_hp)
        source.energy = min(source.energy + MEAT_ENERGY, source.max_energy)

        bleeding = source.get_state(Bleeding)
        if bleeding.active:
            bleeding.bleeding -= 1
        else:
            bleeding.active = True

        self.session.say(ls("deluxe.item.piece_of_meat.effect").format(source.name),
                         source_id=source.id, target_id=source.id)
