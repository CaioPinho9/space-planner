from datetime import datetime

import pandas as pd
from flask import Flask, request, jsonify

from potato_types import ThingMaker
from simulation import Simulation

app = Flask(__name__)

simulation = Simulation()


@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    configuration = request.get_json()

    if configuration is None:
        return jsonify({"error": "Invalid request"}), 400

    ThingMaker.load_thing_maker()

    start_income = ThingMaker.start_income

    configuration = {
        "start_income": configuration.get("start_income", start_income),
        "start_time": datetime.now(),
        "time_steps": configuration.get("time_steps", 900),
    }

    if configuration["start_income"] is None:
        return jsonify({"error": "Missing start income"}), 400

    # Run the simulation
    if not simulation.start_simulation(configuration):
        return jsonify({"error": "Simulation already running"}), 400

    return jsonify("Simulation started")


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
