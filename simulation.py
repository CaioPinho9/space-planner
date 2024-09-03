import warnings
from datetime import datetime
from random import choices

import pandas as pd

from PotatoTypes import ThingMaker

# 27s buff probetato
# 20s potato plant to activate
# day 3:11min night 25s 3:36total

def calculate_normalized_efficiencies(upgrades, current_income, time_steps):
    normalized_efficiencies = []

    mask_efficiency = [upgrade.buyable and not upgrade.current_cost / current_income > time_steps for upgrade in upgrades]
    total_efficiency = sum(upgrade.efficiency for i, upgrade in enumerate(upgrades) if mask_efficiency[i])

    for i, upgrade in enumerate(upgrades):
        efficiency = 0

        if mask_efficiency[i]:
            efficiency = upgrade.efficiency / total_efficiency

        normalized_efficiencies.append(efficiency)
    return normalized_efficiencies

def run_simulation(simulation_config):
    time_steps = simulation_config["time_steps"]

    simulation_index = simulation_config["simulation_index"]
    income_per_second = simulation_config["start_income"]

    current_log = pd.DataFrame(columns=["Index", "Time", "Income per Second", "Thing", "Cost", "Quantity"])
    upgrades = ThingMaker.reset_buyable_stuff()

    current_w = 0
    # Calculate total efficiency
    normalized_efficiencies = calculate_normalized_efficiencies(upgrades, income_per_second, time_steps)
    last_bought = False
    for t in range(time_steps):
        current_w += income_per_second  # accumulate income

        if last_bought:
            normalized_efficiencies = calculate_normalized_efficiencies(upgrades, income_per_second, time_steps)
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

    if income_per_second > simulation_config["best_income"]:
        simulation_config['best_income'] = income_per_second
        simulation_config['best_index'] = simulation_index
        simulation_config['best_log'] = current_log
        current_log.to_csv("best_log.csv", index=False)

        ThingMaker.save_thing_maker(income_per_second)

    simulation_config["total_income"] += income_per_second
    print_simulation_results(simulation_config, income_per_second)

def print_simulation_results(simulation_config, income_per_second):
    best_income = simulation_config['best_income']
    best_index = simulation_config['best_index']
    total_income = simulation_config['total_income']
    simulation_index = simulation_config['simulation_index']
    simulation_times = simulation_config['simulation_times']

    start_time = simulation_config['start_time']
    elapsed_time = datetime.now() - start_time

    print(f"\rSimulation {simulation_index} completed with income per second: {income_per_second:.0f}", end=' | ')
    print(f"Best Simulation {best_index} completed with income per second: {best_income:.0f}", end=' | ')
    print(f"Time taken: {elapsed_time}", end=' | ')
    print(f"Time remaining: {elapsed_time / (simulation_index + 1) * (simulation_times - simulation_index)}", end=' | ')
    print(f"Simulations per second: {(simulation_index + 1) / elapsed_time.total_seconds():.2f}", end=' | ')
    print(f"Average income: {total_income / (simulation_index + 1):.2f}", end='')
