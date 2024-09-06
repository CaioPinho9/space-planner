import multiprocessing
import threading
import warnings
from datetime import datetime
from random import choices

import pandas as pd

from potato_types import ThingMaker
from data.shared_memory import SharedMemory


# 27s buff probetato
# 20s potato plant to activate
# day 3:11min night 25s 3:36total

class Simulation:
    def __init__(self, process_count=None):
        self.running_simulation = False
        self.process_count = multiprocessing.cpu_count() if process_count is None else process_count
        self.shared_memory = SharedMemory(self.process_count)
        self.processes = []
        self.lock = threading.Lock()
        self.start_income = None
        self.time_steps = None

    @classmethod
    def __calculate_normalized_efficiencies(cls, simulation_things, current_income, time_steps):
        normalized_efficiencies = []

        mask_efficiency = [thing.buyable and not thing.current_cost / current_income > time_steps for thing in simulation_things]
        total_efficiency = sum(thing.efficiency for i, thing in enumerate(simulation_things) if mask_efficiency[i])

        for i, thing in enumerate(simulation_things):
            efficiency = 0

            if mask_efficiency[i]:
                efficiency = thing.efficiency / total_efficiency

            normalized_efficiencies.append(efficiency)
        return normalized_efficiencies

    def start_simulation(self, start_income, time_steps):
        if self.running_simulation:
            return False

        self.start_income = start_income
        self.time_steps = time_steps
        self.running_simulation = True
        self.shared_memory = SharedMemory(self.process_count)
        self.shared_memory.start_time = datetime.now()

        self.processes = []
        for i in range(self.process_count):
            self.processes.append(multiprocessing.Process(target=self.run_simulation, args=(i,)))
            self.processes[i].start()
        return True

    def end_simulation(self):
        self.running_simulation = False
        for process in self.processes:
            process.terminate()

    def run_simulation(self, process_id):
        while True:
            income_per_second = self.start_income
            simulation_index = self.shared_memory.simulation_index[process_id]
            current_log = pd.DataFrame(columns=["Time", "Income per Second", "Thing", "Cost", "Quantity"])
            simulation_things = ThingMaker.reset_simulation_things()
            current_w = 0
            # Calculate total efficiency
            normalized_efficiencies = self.__calculate_normalized_efficiencies(simulation_things, income_per_second, self.time_steps)
            last_bought = False
            for t in range(self.time_steps):
                current_w += income_per_second  # accumulate income

                if last_bought:
                    normalized_efficiencies = self.__calculate_normalized_efficiencies(simulation_things, income_per_second, self.time_steps)
                else:
                    normalized_efficiencies = [
                        0 if upgrade.current_cost <= current_w - income_per_second else efficiency
                        for upgrade, efficiency in zip(simulation_things, normalized_efficiencies)
                    ]

                # Decide what to buy based on normalized efficiencies
                selected_obj = choices(simulation_things, weights=normalized_efficiencies, k=1)[0]

                if selected_obj.current_cost <= current_w:
                    last_bought = False
                    if selected_obj.buyable:
                        quantity = selected_obj.quantity
                        cost = selected_obj.current_cost
                        current_w -= cost
                        last_bought = True

                        income_per_second += selected_obj.power_output

                        selected_obj.buy()

                        # Log the event
                        with warnings.catch_warnings():
                            warnings.simplefilter(action='ignore', category=FutureWarning)
                            current_log = pd.concat([current_log, pd.DataFrame([{
                                "Time": t,
                                "Income per Second": income_per_second,
                                "Thing": selected_obj.name,
                                "Cost": cost,
                                "Quantity": quantity
                            }])], ignore_index=True)

            if income_per_second > self.shared_memory.best_income:
                with self.lock:
                    if income_per_second > self.shared_memory.best_income:
                        self.shared_memory.best_income = income_per_second
                        self.shared_memory.best_index = simulation_index
                        self.shared_memory.best_log = current_log.to_dict(orient='records')

            self.shared_memory.update_simulation_index(process_id, simulation_index + 1)
            self.shared_memory.increase_thread_income(process_id, income_per_second)

    def save_simulation(self):
        ThingMaker.save_thing_maker(self.shared_memory.best_income)

    def get_simulation_results(self):
        return self.shared_memory
