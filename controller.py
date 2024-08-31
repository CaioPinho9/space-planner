from datetime import datetime

import pandas as pd
from flask import Flask, request

from potato_types import ThingMaker
from simulation import Simulation

app = Flask(__name__)

simulation = Simulation()


@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    simulation_config = request.get_json()

    if simulation_config is None:
        return {"error": "Invalid request"}, 400

    best_log = pd.DataFrame(columns=["Index", "Time", "Income per Second", "Selected Object", "Cost"])

    ThingMaker.load_thing_maker(True)

    start_income = ThingMaker.start_income

    simulation_config = {
        "best_index": simulation_config.get("best_index", -1),
        "best_income": simulation_config.get("best_income", 1011),
        "log": simulation_config.get("log", True),
        "simulation_times": simulation_config.get("simulation_times", 200000),
        "start_income": start_income,
        "start_time": datetime.now(),
        "time_steps": simulation_config.get("simulation_times", 200000),
        "total_income": simulation_config.get("total_income", 0),
    }

    # Run the simulation
    simulation.start_simulation(simulation_config)

    if simulation_config["log"]:
        # Print the log while formatting
        for index, row in best_log.iterrows():
            print(f"Time: {row['Time']}, Object: {row['Selected Object']}")
        print(f"\nTotal Income per Second: {simulation_config['best_income']:.2f}")


if __name__ == '__main__':
    app.run(debug=True)
