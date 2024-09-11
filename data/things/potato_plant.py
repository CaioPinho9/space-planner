from analyse.predictor import Predictor
from data.buff import Buff
from data.things.potato_types import PotatoType


class PotatoPlant(PotatoType):
    def __init__(self, name, power_output):
        super().__init__(name, power_output)
        self._buff = Buff("PotatoPlantDebuff", 20, -self.power_output)
