from datetime import datetime

import pandas as pd
from flask import Flask, request, jsonify

from potato_types import ThingMaker
from simulation import Simulation

app = Flask(__name__)

simulation = Simulation()


@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    simulation_config = request.get_json()

    if simulation_config is None:
        return jsonify({"error": "Invalid request"}), 400

    best_log = pd.DataFrame(columns=["Index", "Time", "Income per Second", "Selected Object", "Cost"])

    ThingMaker.load_thing_maker()

    start_income = ThingMaker.start_income

    simulation_config = {
        "best_index": simulation_config.get("best_index", -1),
        "best_income": simulation_config.get("best_income", 1011),
        "log": simulation_config.get("log", True),
        "start_income": simulation_config.get("start_income", start_income),
        "start_time": datetime.now(),
        "time_steps": simulation_config.get("time_steps", 200000),
        "total_income": simulation_config.get("total_income", 0),
    }

    if simulation_config["start_income"] is None:
        return jsonify({"error": "Missing start income"}), 400

    # Run the simulation
    if not simulation.start_simulation(simulation_config):
        return jsonify({"error": "Simulation already running"}), 400

    log_data = []
    if simulation_config["log"]:
        for index, row in best_log.iterrows():
            log_data.append({
                "Time": row["Time"],
                "Selected Object": row["Selected Object"]
            })

    response = {
        "log": log_data,
        "total_income_per_second": simulation_config["best_income"]
    }

    return jsonify(response)


@app.route('/end_simulation', methods=['POST'])
def end_simulation():
    simulation.end_simulation()
    return jsonify({"message": "Simulation ended"})


@app.route('/save_simulation', methods=['POST'])
def save_simulation():
    simulation.save_simulation()
    return jsonify({"message": "Simulation saved"})


if __name__ == '__main__':
    app.run(debug=True)
