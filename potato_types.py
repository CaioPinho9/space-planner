import json
from abc import ABC, abstractmethod
from copy import deepcopy

from predictor import Predictor


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

    # Serialize in json
    def serialize(self):
        return {
            self.name: self.quantity
        }


class PotatoType(Thing):
    def __init__(self, name, power_output, quantity=0):
        super().__init__(name, Predictor.predict_thing_cost(quantity + 1, name), quantity, 1)
        self.base_power_output = power_output
        self.power_output = self.base_power_output
        self._efficiency = self.current_cost / self.power_output

    def buy(self):
        self.quantity += 1

    @property
    def multiplier(self):
        return self._multiplier

    @multiplier.setter
    def multiplier(self, value):
        self._multiplier = value
        self.power_output = self.base_power_output * self._multiplier

    def _update_quantity(self):
        self.current_cost = Predictor.predict_thing_cost(self._quantity + 1, self.name)
        self._efficiency = self.current_cost / self.power_output


class Upgrade(Thing):
    def __init__(self, name, target, multiplier, cost, quantity=0):
        super().__init__(name, cost, quantity, multiplier)
        self._multiplier = multiplier
        self._target = target
        self._target_obj = None

    def _find_target(self):
        for thing in ThingMaker.simulation_things:
            if thing.name == self._target:
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
    simulation_things = []

    @classmethod
    def create_things(cls):
        cls._things = [
            PotatoType("SolarPanel", power_output=0.0885),
            PotatoType("Potato", power_output=1.0),
            PotatoType("Probetato", power_output=8.0),
            PotatoType("Spudnik", power_output=42.0),
            PotatoType("PotatoPlant", power_output=230),
        ]

        cls._upgrades = [
            Upgrade("CleanSolarPanels", target="SolarPanel", multiplier=0.3 / 0.1, cost=1000),
            Upgrade("SolarAmbience", target="SolarPanel", multiplier=0.0942 / 0.0885, cost=2600),
            Upgrade("MarisPipers", target="Potato", multiplier=2, cost=8000),
            Upgrade("PolishedSolarPanels", target="SolarPanel", multiplier=1 / 0.3, cost=15000),
            Upgrade("MarisPeers", target="Potato", multiplier=2, cost=160000),
            Upgrade("ProbetatoRoots", target="Probetato", multiplier=4, cost=180000),
            Upgrade("GoldenSolarPanels", target="SolarPanel", multiplier=4, cost=500000),
            Upgrade("GoldenSpudnikFoil", target="Spudnik", multiplier=2, cost=600000),
            Upgrade("ProbetatoPlanters", target="Probetato", multiplier=2, cost=1800000),
        ]

        cls._things.extend(cls._upgrades)

        cls.simulation_things = cls._things

    @classmethod
    def reset_simulation_things(cls):
        cls.simulation_things = deepcopy(cls._things)

        return cls.simulation_things

    @classmethod
    def save_thing_maker(cls, income):
        things_json = {}
        for thing in cls.simulation_things:
            things_json.update(thing.serialize())

        things_json['start_income'] = income

        with open('things.json', 'w') as f:
            json.dump(things_json, f, indent=4)

    @classmethod
    def load_thing_maker(cls):
        cls.create_things()

        try:
            with open('things.json', 'r') as f:
                things_json = json.load(f)

            for thing in cls._things:
                thing.quantity = things_json.get(thing.name, 0)
            cls.start_income = things_json.get('start_income', 0)
        except FileNotFoundError:
            pass

        cls._things = [thing for thing in cls._things if thing.buyable]

        cls.reset_simulation_things()
