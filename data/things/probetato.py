from analyse.predictor import Predictor
from data.buff import Buff
from data.things.potato_types import PotatoType


class Probetato(PotatoType):
    def __init__(self, name, power_output):
        super().__init__(name, power_output)
        self._efficiency = self._probetato_efficiency()
        self._buff = Buff("ProbetatoBuff", 27, self.power_output * 0.5 if self.quantity >= 3 else self.base_power_output * 1.5)

    def _probetato_efficiency(self):
        return self.power_output / self.current_cost if self.quantity >= 3 else self.base_power_output / self.current_cost

    @property
    def power_output(self):
        return self._power_output if self.quantity >= 3 else 0

    def _update_quantity(self):
        self.current_cost = Predictor.predict_thing_cost(self._quantity + 1, self.name)
        if self._quantity == 4:
            self.current_cost += 550
        self._efficiency = self._probetato_efficiency()
