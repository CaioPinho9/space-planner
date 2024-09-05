import multiprocessing
import threading
import warnings
from datetime import datetime
from random import choices

import pandas as pd

from potato_types import ThingMaker


# 27s buff probetato
# 20s potato plant to activate
# day 3:11min night 25s 3:36total

class Simulation:
    def __init__(self):
        self.running_simulation = False
        self.threads = []
        self.lock = threading.Lock()
        self.best_log = None
        self.configuration = None

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

    def start_simulation(self, simulation_config):
        if self.running_simulation:
            return False

        process_count = multiprocessing.cpu_count()

        simulation_config["simulation_index"] = [0] * process_count
        self.configuration = simulation_config
        self.running_simulation = True

        for i in range(process_count):
            self.threads.append(threading.Thread(target=self.run_simulation, args=(i,)))
            self.threads[i].start()
        return True

    def end_simulation(self):
        self.running_simulation = False
        for thread in self.threads:
            thread.join()

    def run_simulation(self, id):
        time_steps = self.configuration["time_steps"]
        while self.running_simulation:
            simulation_index = self.configuration["simulation_index"][id]
            income_per_second = self.configuration["start_income"]
            current_log = pd.DataFrame(columns=["Index", "Time", "Income per Second", "Selected Object", "Cost"])
            simulation_things = ThingMaker.reset_simulation_things()
            current_w = 0
            # Calculate total efficiency
            normalized_efficiencies = self.__calculate_normalized_efficiencies(simulation_things, income_per_second, time_steps)
            last_bought = False
            for t in range(time_steps):
                current_w += income_per_second  # accumulate income

                if last_bought:
                    normalized_efficiencies = self.__calculate_normalized_efficiencies(simulation_things, income_per_second, time_steps)
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
                                "Index": simulation_index,
                                "Time": t,
                                "Income per Second": income_per_second,
                                "Thing": selected_obj.name,
                                "Cost": cost,
                                "Quantity": quantity
                            }])], ignore_index=True)

            if income_per_second > self.configuration["best_income"]:
                with self.lock:
                    if income_per_second > self.configuration["best_income"]:
                        self.configuration['best_income'] = income_per_second
                        self.configuration['best_index'] = simulation_index
                        self.configuration['best_log'] = current_log
                        self.best_log = current_log

            self.configuration["simulation_index"][id] += 1
            if id == 0:
                self.print_simulation_results(income_per_second, current_w)

    def print_simulation_results(self, income_per_second, current_w):
        best_income = self.configuration['best_income']
        best_index = self.configuration['best_index']
        simulation_index = sum(self.configuration['simulation_index'])

        start_time = self.configuration['start_time']
        elapsed_time = datetime.now() - start_time

        print(f"\rSimulation {simulation_index} completed with income per second: {income_per_second:.0f}", end=' | ')
        print(f"Best Simulation {best_index} completed with income per second: {best_income:.0f}", end=' | ')
        print(f"Time taken: {elapsed_time}", end=' | ')
        print(f"Simulations per second: {(simulation_index + 1) / elapsed_time.total_seconds():.2f}", end=' | ')
        print(f"Average income: {current_w / (simulation_index + 1):.2f}", end='')

    def save_simulation(self):
        ThingMaker.save_thing_maker(self.configuration["best_income"])
