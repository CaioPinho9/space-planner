import json
from copy import deepcopy


class ThingMaker:
    start_income = None

    _save_file = 'resource/save/things.json'

    _simulation_things = []
    shared_memory = None

    @property
    def simulation_things(self):
        return self._simulation_things

    @simulation_things.setter
    def simulation_things(self, value):
        self._simulation_things = value

    def add_things(self, things):
        temp = self.shared_memory.things
        temp.extend(things)
        self.shared_memory.things = temp
        self.simulation_things = self.shared_memory.things

    def reset_simulation_things(self):
        try:
            return deepcopy(self.shared_memory.things)
        except Exception:
            return None

    def save_thing_maker(self):
        things_json = {}
        for thing in self.shared_memory.things:
            things_json.update(thing.serialize())

        with open(self._save_file, 'w') as f:
            json.dump(things_json, f, indent=4)

    def load_thing_maker(self):
        try:
            with open(self._save_file, 'r') as f:
                things_json = json.load(f)

            temp = self.shared_memory.things
            for thing in temp:
                thing.quantity = things_json.get(thing.name, 0)
            self.shared_memory.things = temp
        except FileNotFoundError:
            pass

        self.reset_simulation_things()

    @staticmethod
    def current_income(things):
        total = 0
        for thing in things:
            if type(thing).__name__ == 'Upgrade':
                continue
            if thing.name == 'Probetato':
                total -= thing.power_output * min(thing.quantity, 3)
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
