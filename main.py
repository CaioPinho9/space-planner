from datetime import datetime

import pandas as pd

from potato_types import ThingMaker
from simulation import run_simulation

# Simulation parameters
simulation_times = 200000  # number of times to run the simulation
time_steps = 1800  # number of seconds to simulate

best_log = pd.DataFrame(columns=["Index", "Time", "Income per Second", "Thing", "Cost", "Quantity"])
best_income = 91
best_index = -1
from_pickle = False

total_income = 0
start_income = 32.5

ThingMaker.load_thing_maker(from_pickle)

start_income = ThingMaker.start_income if from_pickle else start_income

simulation_config = {
    "time_steps": time_steps,
    "simulation_times": simulation_times,
    "best_index": best_index,
    "best_income": best_income,
    "start_income": start_income,
    "total_income": total_income,
    "start_time": datetime.now()
}

# Run the simulation
for index in range(simulation_times):
    simulation_config["simulation_index"] = index
    run_simulation(simulation_config)

# Print the log while formatting
for index, row in best_log.iterrows():
    print(f"Time: {row['Time']}, Object: {row['Selected Object']}")
print(f"\nTotal Income per Second: {best_income:.2f}")
