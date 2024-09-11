from analyse.predictor import Predictor
from data.things.thing import Thing


class PotatoType(Thing):
    def __init__(self, name, power_output):
        super().__init__(name, Predictor.predict_thing_cost(1, name), 1)
        self.base_power_output = power_output
        self._power_output = self.base_power_output
        self._efficiency = self._power_output / self.current_cost

    @property
    def power_output(self):
        return self._power_output

    @power_output.setter
    def power_output(self, value):
        self._power_output = value

    def buy(self):
        self.quantity += 1
        return self._buff

    @property
    def multiplier(self):
        return self._multiplier

    @multiplier.setter
    def multiplier(self, value):
        self._multiplier = value
        self.power_output = self.base_power_output * self._multiplier

    def _update_quantity(self):
        self.current_cost = Predictor.predict_thing_cost(self._quantity + 1, self.name)
        self._efficiency = self.power_output / self.current_cost
