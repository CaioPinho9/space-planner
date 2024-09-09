from data.things.thing import Thing


class Upgrade(Thing):
    def __init__(self, name, target, multiplier, cost, quantity=0):
        super().__init__(name, cost, quantity, multiplier)
        self._multiplier = multiplier
        self._target = target
        self._target_obj = None
        self._thing_maker = None

    def set_injection(self, thing_maker):
        self._thing_maker = thing_maker

    def _find_target(self):
        if self._target_obj:
            return self._target_obj

        for thing in self._thing_maker.simulation_things:
            if thing.name == self._target:
                self._target_obj = thing
                return thing

    def buy(self):
        self.quantity = 1

    def _update_quantity(self):
        if not self.quantity:
            return

        self._efficiency = 0

        thing = self._find_target()
        thing.multiplier *= self._multiplier

    @property
    def efficiency(self):
        thing = self._find_target()
        self._efficiency = (thing.power_output * self._multiplier) / self.current_cost
        return self._efficiency

    @property
    def power_output(self):
        thing = self._find_target()
        return (thing.power_output * self._multiplier * thing.quantity) - (thing.power_output * thing.quantity)

    @property
    def buyable(self):
        return not self._quantity
