import threading
import warnings
from datetime import datetime
from random import choices

import pandas as pd

from potato_types import ThingMaker, Thing


# 27s buff probetato
# 20s potato plant to activate
# day 3:11min night 25s 3:36total

class Simulation:
    def __init__(self):
        self.running_simulation = False
        self.thread = None
        self.best_log = None
        self.configuration = None

    @classmethod
    def __calculate_normalized_efficiencies(cls, upgrades, current_income, time_steps):
        normalized_efficiencies = []

        mask_efficiency = [upgrade.buyable and not upgrade.current_cost / current_income > time_steps for upgrade in upgrades]
        total_efficiency = sum(upgrade.efficiency for i, upgrade in enumerate(upgrades) if mask_efficiency[i])

        for i, upgrade in enumerate(upgrades):
            efficiency = 0

            if mask_efficiency[i]:
                efficiency = upgrade.efficiency / total_efficiency

            normalized_efficiencies.append(efficiency)
        return normalized_efficiencies

    def start_simulation(self, simulation_config):
        if self.running_simulation:
            return False

        simulation_config["simulation_index"] = 0
        self.configuration = simulation_config
        self.running_simulation = True
        self.thread = threading.Thread(target=self.run_simulation)
        self.thread.start()
        return True

    def end_simulation(self):
        self.running_simulation = False
        self.thread.join()

    def run_simulation(self):
        while self.running_simulation:
            time_steps = self.configuration["time_steps"]
            simulation_index = self.configuration["simulation_index"]
            income_per_second = self.configuration["start_income"]
            current_log = pd.DataFrame(columns=["Index", "Time", "Income per Second", "Selected Object", "Cost"])
            upgrades = ThingMaker.reset_buyable_stuff()
            current_w = 0
            # Calculate total efficiency
            normalized_efficiencies = self.__calculate_normalized_efficiencies(upgrades, income_per_second, time_steps)
            last_bought = False
            for t in range(time_steps):
                current_w += income_per_second  # accumulate income

                if last_bought:
                    normalized_efficiencies = self.__calculate_normalized_efficiencies(upgrades, income_per_second, time_steps)
                else:
                    normalized_efficiencies = [
                        0 if upgrade.current_cost <= current_w - income_per_second else efficiency
                        for upgrade, efficiency in zip(upgrades, normalized_efficiencies)
                    ]

                # Decide what to buy based on normalized efficiencies
                selected_obj = choices(upgrades, weights=normalized_efficiencies, k=1)[0]

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
                self.configuration['best_income'] = income_per_second
                self.configuration['best_index'] = simulation_index
                self.configuration['best_log'] = current_log
                self.best_log = current_log

            self.configuration["total_income"] += income_per_second
            self.configuration["simulation_index"] += 1
            self.print_simulation_results(income_per_second)

    def print_simulation_results(self, income_per_second):
        best_income = self.configuration['best_income']
        best_index = self.configuration['best_index']
        total_income = self.configuration['total_income']
        simulation_index = self.configuration['simulation_index']
        simulation_times = self.configuration['simulation_times']

        start_time = self.configuration['start_time']
        elapsed_time = datetime.now() - start_time

        print(f"\rSimulation {simulation_index} completed with income per second: {income_per_second:.0f}", end=' | ')
        print(f"Best Simulation {best_index} completed with income per second: {best_income:.0f}", end=' | ')
        print(f"Time taken: {elapsed_time}", end=' | ')
        print(f"Time remaining: {elapsed_time / (simulation_index + 1) * (simulation_times - simulation_index)}", end=' | ')
        print(f"Simulations per second: {(simulation_index + 1) / elapsed_time.total_seconds():.2f}", end=' | ')
        print(f"Average income: {total_income / (simulation_index + 1):.2f}", end='')

    def save_simulation(self):
        ThingMaker.save_thing_maker(self.configuration["best_income"])
