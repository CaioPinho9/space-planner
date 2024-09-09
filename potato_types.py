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

    def set_injection(self, thing_maker):
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
        self._power_output = self.base_power_output
        self._efficiency = self.current_cost / self._power_output

    @property
    def power_output(self):
        return self._power_output

    @power_output.setter
    def power_output(self, value):
        self._power_output = value

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
        self._efficiency = self.current_cost / thing.power_output * self._multiplier
        return self._efficiency

    @property
    def power_output(self):
        thing = self._find_target()
        return (thing.power_output * self._multiplier * thing.quantity) - (thing.power_output * thing.quantity)

    @property
    def buyable(self):
        return not self._quantity


class Probetato(PotatoType):
    def __init__(self, name, power_output, quantity=0):
        super().__init__(name, power_output, quantity)
        self._efficiency = self._probetato_efficiency()

    def _probetato_efficiency(self):
        return self.current_cost / self.power_output if self.quantity >= 3 else self.current_cost / self.base_power_output

    @property
    def power_output(self):
        return self._power_output if self.quantity >= 3 else 0

    def _update_quantity(self):
        self.current_cost = Predictor.predict_thing_cost(self._quantity + 1, self.name)
        self._efficiency = self._probetato_efficiency()


class ThingMaker:
    start_income = None

    _save_file = 'resource/save/things.json'

    _upgrades = []
    _things = []
    _simulation_things = []
    shared_memory = None

    @property
    def simulation_things(self):
        if not self._simulation_things:
            for thing in self.shared_memory.things:
                thing.set_injection(self)
            return self.reset_simulation_things()
        return self._simulation_things

    @simulation_things.setter
    def simulation_things(self, value):
        self._simulation_things = value

    def create_things(self):
        self.shared_memory.things = [
            PotatoType("SolarPanel", power_output=0.0885),
            PotatoType("Potato", power_output=1.0),
            Probetato("Probetato", power_output=8.0),
            PotatoType("Spudnik", power_output=42.0),
            PotatoType("PotatoPlant", power_output=230),
        ]

        self._upgrades = [
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

        for upgrade in self._upgrades:
            upgrade.set_injection(self)

        temp = self.shared_memory.things
        temp.extend(self._upgrades)
        self.shared_memory.things = temp

        self.simulation_things = self.shared_memory.things

    def reset_simulation_things(self):
        self.simulation_things = deepcopy(self.shared_memory.things)

        self.simulation_things = [thing for thing in self.simulation_things if thing.buyable]

        return self.simulation_things

    def save_thing_maker(self):
        things_json = {}
        for thing in self.shared_memory.things:
            things_json.update(thing.serialize())

        things_json['start_income'] = ThingMaker.current_income(self.shared_memory.things)

        with open(self._save_file, 'w') as f:
            json.dump(things_json, f, indent=4)

    def load_thing_maker(self):
        self.create_things()

        try:
            with open(self._save_file, 'r') as f:
                things_json = json.load(f)

            temp = self.shared_memory.things
            for thing in temp:
                thing.quantity = things_json.get(thing.name, 0)
            self.shared_memory.things = temp
            self.start_income = things_json.get('start_income', 0)
        except FileNotFoundError:
            pass

        self.reset_simulation_things()

    @staticmethod
    def current_income(things):
        total = 0
        for thing in things:
            if isinstance(thing, Probetato):
                total -= thing.power_output * max(thing.quantity, 3)
            total += thing.power_output * thing.quantity
        return total

    def buy_thing(self, name):
        temp = self.shared_memory.things
        for thing in temp:
            if thing.name == name:
                thing.buy()
                self.shared_memory.things = temp
                return True

        return False

    def get_buyable_things(self):
        things = []
        for thing in self.shared_memory.things:
            if thing.buyable:
                things.append({"name": thing.name, "quantity": thing.quantity, "cost": thing.current_cost})
        return things
