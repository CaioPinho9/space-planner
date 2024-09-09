from abc import abstractmethod, ABC


class Thing(ABC):
    def __init__(self, name, cost, quantity, multiplier):
        self.name = name
        self.current_cost = cost
        self._efficiency = 0

        self._multiplier = multiplier
        self._quantity = quantity

    @abstractmethod
    def buy(self):
        pass

    @property
    def buyable(self):
        return True

    @property
    def efficiency(self):
        return self._efficiency

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        self._quantity = value
        self._update_quantity()

    @abstractmethod
    def _update_quantity(self):
        pass

    def set_injection(self, thing_maker):
        pass

    # Serialize in json
    def serialize(self):
        return {
            self.name: self.quantity
        }
