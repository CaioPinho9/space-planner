import pickle
from abc import ABC, abstractmethod
from copy import deepcopy

from predict import predict_from_csv

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


class PotatoType(Thing):
    def __init__(self, name, power_output, quantity=0):
        super().__init__(name, predict_from_csv(quantity + 1, name), quantity, 1)
        self.base_power_output = power_output
        self.power_output = self.base_power_output
        self._efficiency = self.current_cost / self.power_output

    def buy(self):
        self._quantity += 1
        self.current_cost = predict_from_csv(self._quantity + 1, self.name)
        self._efficiency = self.current_cost / self.power_output

    @property
    def multiplier(self):
        return self._multiplier

    @multiplier.setter
    def multiplier(self, value):
        self._multiplier = value
        self.power_output = self.base_power_output * self._multiplier


class Upgrade(Thing):
    def __init__(self, name, target, multiplier, cost, quantity=0):
        super().__init__(name, cost, quantity, multiplier)
        self._multiplier = multiplier
        self._target = target
        self._calculate_efficiency = True
        self._target_obj = None

    def _find_target(self):
        if self._target_obj:
            return self._target_obj

        for thing in ThingMaker.buyable_stuff:
            if thing.name == self._target:
                return thing

    def buy(self):
        self._quantity = 1
        self._efficiency = 0

        thing = self._find_target()
        thing.multiplier *= self._multiplier

    @property
    def efficiency(self):
        if self._calculate_efficiency:
            thing = self._find_target()
            self._efficiency = self.current_cost / thing.power_output * self._multiplier

        return self._efficiency

    @property
    def power_output(self):
        thing = self._find_target()
        return (thing.power_output * self._multiplier * thing.quantity) - (thing.power_output * thing.quantity)

    @property
    def buyable(self):
        return not self._quantity

class ThingMaker:
    start_income = None

    _things = []
    _upgrades = []
    buyable_stuff = []

    @classmethod
    def create_things(cls):
        cls._things = [
            PotatoType("SolarPanel", power_output=0.1, quantity=17),
            PotatoType("Potato", power_output=1.0, quantity=5),
            PotatoType("Probetato", power_output=8.0, quantity=5),
            PotatoType("Spudnik", power_output=42.0, quantity=1),
            PotatoType("PotatoPlant", power_output=230, quantity=0),
        ]

        cls._upgrades = [
            Upgrade("EnhancedSolar", target="SolarPanel", multiplier=0.3 / 0.1, cost=1000, quantity=1),
            Upgrade("SolarAmbience", target="SolarPanel", multiplier=0.5 / 0.3, cost=2600),
            Upgrade("MarisPipers", target="Potato", multiplier=2, cost=8000),
            Upgrade("MrSheen", target="SolarPanel", multiplier=1 / 0.3, cost=15000),
            Upgrade("ProbetatoRoots", target="Probetato", multiplier=4, cost=180000),
            Upgrade("GoldenSpudnikFoil", target="Spudnik", multiplier=2, cost=600000),
        ]

        cls._things.extend(cls._upgrades)

        cls.buyable_stuff = cls._things

    @classmethod
    def reset_buyable_stuff(cls):
        cls.buyable_stuff = deepcopy(cls._things)

        return cls.buyable_stuff

    @classmethod
    def save_thing_maker(cls, income):
        with open('things.pkl', 'wb') as f:
            save = cls.buyable_stuff, income
            pickle.dump(save, f)

    @classmethod
    def load_thing_maker(cls, from_pickler):
        if from_pickler:
            with open('things.pkl', 'rb') as f:
                cls._things, cls.start_income = pickle.load(f)
        else:
            cls.create_things()
            for upgrade in cls._things:
                if not upgrade.buyable:
                    upgrade.buy()

        cls._things = [thing for thing in cls._things if thing.buyable]
        cls.reset_buyable_stuff()
