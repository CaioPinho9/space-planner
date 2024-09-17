import multiprocessing
import threading
import warnings
from random import choices

import pandas as pd

from analyse.time_debug import TimeDebug
from data.shared_memory import SharedMemory
from managers.buff_manager import BuffManager
from managers.thing_maker import ThingMaker
from managers.thing_maker_starter import ThingMakerStarter


# 27s buff probetato
# 20s potato plant to activate
# day 3:11min night 25s 3:36total

class Simulation:
    def __init__(self, thing_maker, process_count=None):
        self.running_simulation = False
        self.process_count = multiprocessing.cpu_count() if process_count is None else process_count
        self.shared_memory = SharedMemory(self.process_count)
        self.thing_maker = thing_maker
        self.processes = []
        self.lock = threading.Lock()
        self.start_income = None
        self.time_steps = None
        self.thing_maker_starter = ThingMakerStarter(self.thing_maker)

    @classmethod
    def _calculate_normalized_efficiencies(cls, simulation_things, current_income, time_steps):
        TimeDebug.start('calculate_normalized_efficiencies')
        normalized_efficiencies = []

        mask_efficiency = [thing.buyable and not thing.current_cost / current_income > time_steps for thing in simulation_things]
        total_efficiency = sum(thing.efficiency for i, thing in enumerate(simulation_things) if mask_efficiency[i])

        for i, thing in enumerate(simulation_things):
            efficiency = 0

            if mask_efficiency[i]:
                efficiency = thing.efficiency / total_efficiency

            normalized_efficiencies.append(efficiency)
        TimeDebug.end('calculate_normalized_efficiencies')
        return normalized_efficiencies

    def start_simulation(self, start_income, time_steps):
        if self.running_simulation:
            return False

        self.start_income = start_income
        self.time_steps = time_steps
        self.running_simulation = True
        self.shared_memory = SharedMemory(self.process_count)
        self.thing_maker.shared_memory = self.shared_memory

        self.thing_maker_starter.start()
        self.thing_maker.load_thing_maker()

        self.processes = []
        for i in range(self.process_count):
            self.processes.append(multiprocessing.Process(target=self.run_simulation, args=(i)))
            self.processes[i].start()
        return True

    def end_simulation(self):
        self.running_simulation = False
        for process in self.processes:
            process.terminate()

    def run_simulation(self, process_id):
        count = 0
        while True:
            try:
                TimeDebug.start('simulation_index')
                simulation_index = self.shared_memory.simulation_index[process_id]
                TimeDebug.end('simulation_index')
                current_log = pd.DataFrame(columns=["Time", "Income", "Thing", "Cost", "Quantity"])

                TimeDebug.start('reset_simulation_things')
                simulation_things = self.thing_maker.reset_simulation_things()
                TimeDebug.end('reset_simulation_things')

                if simulation_things is None:
                    print("Simulation things is None")
                    continue

                buff_manager = BuffManager()

                TimeDebug.start('current_income')
                income_per_second = ThingMaker.current_income(simulation_things)
                TimeDebug.end('current_income')

                if income_per_second == 0:
                    income_per_second = 0.1

                current_w = 0
                # Calculate total efficiency
                normalized_efficiencies = self._calculate_normalized_efficiencies(simulation_things, income_per_second, self.time_steps)
                last_bought = False

                TimeDebug.start('time_steps')
                for t in range(self.time_steps):
                    current_w += income_per_second  # accumulate income
                    TimeDebug.start('buff_use')
                    income_per_second += buff_manager.use()
                    TimeDebug.end('buff_use')

                    TimeDebug.start('efficiencies')
                    if last_bought:
                        normalized_efficiencies = self._calculate_normalized_efficiencies(simulation_things, income_per_second, self.time_steps)
                    else:
                        normalized_efficiencies = [
                            0 if upgrade.current_cost <= current_w - income_per_second else efficiency
                            for upgrade, efficiency in zip(simulation_things, normalized_efficiencies)
                        ]
                    TimeDebug.end('efficiencies')

                    # Decide what to buy based on normalized efficiencies
                    TimeDebug.start('choices')
                    selected_obj = choices(simulation_things, weights=normalized_efficiencies, k=1)[0]
                    TimeDebug.end('choices')

                    TimeDebug.start('buy?')
                    if selected_obj.current_cost <= current_w:
                        last_bought = False
                        if selected_obj.buyable:
                            quantity = selected_obj.quantity
                            TimeDebug.start('current_cost')
                            cost = selected_obj.current_cost
                            TimeDebug.end('current_cost')
                            current_w -= cost
                            last_bought = True

                            TimeDebug.start('power_output')
                            income_per_second += selected_obj.power_output
                            TimeDebug.end('power_output')

                            TimeDebug.start('buy')
                            buff = selected_obj.buy()
                            TimeDebug.end('buy')

                            TimeDebug.start('add_buff')
                            income_per_second += buff_manager.add_buff(buff)
                            TimeDebug.end('add_buff')

                            TimeDebug.start('log')
                            # Log the event
                            with warnings.catch_warnings():
                                warnings.simplefilter(action='ignore', category=FutureWarning)
                                current_log = pd.concat([current_log, pd.DataFrame([{
                                    "Time": t,
                                    "Income": income_per_second,
                                    "Thing": selected_obj.name,
                                    "Cost": cost,
                                    "Quantity": quantity
                                }])], ignore_index=True)
                            TimeDebug.end('log')
                    TimeDebug.end('buy?')
                TimeDebug.end('time_steps')

                TimeDebug.start('best_income')
                if income_per_second > self.shared_memory.best_income:
                    with self.lock:
                        TimeDebug.start('best_income_inner')
                        if income_per_second > self.shared_memory.best_income:
                            self.shared_memory.best_income = income_per_second
                            self.shared_memory.best_index = simulation_index
                            self.shared_memory.best_log = current_log.to_dict(orient='records')
                        TimeDebug.end('best_income_inner')
                TimeDebug.end('best_income')
                count += 1

                TimeDebug.start('increase_simulation')
                self.shared_memory.increase_simulation(process_id, income_per_second)
                TimeDebug.end('increase_simulation')
            except TypeError as e:
                print(e)
                continue

    def save_simulation(self):
        self.thing_maker.save_thing_maker()

    def get_simulation_results(self):
        return self.shared_memory

    def reset_simulation(self):
        if self.running_simulation:
            return False

        self.shared_memory.things = []
        self.thing_maker_starter.start()
        self.thing_maker.save_thing_maker()

    def buy_thing(self):
        self.shared_memory.reset_buy()
