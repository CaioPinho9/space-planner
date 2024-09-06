from datetime import datetime

from flask import Flask, request, jsonify

from potato_types import ThingMaker
from simulation import Simulation

app = Flask(__name__)

simulation = Simulation()


@app.route('/simulation/start', methods=['POST'])
def start_simulation():
    configuration = request.get_json()

    if configuration is None:
        return jsonify({"error": "Invalid request"}), 400

    ThingMaker.load_thing_maker()

    start_income = ThingMaker.start_income
    time_steps = configuration.get("time_steps", 900),
    start_income = configuration.get("start_income", start_income),

    if configuration["start_income"] is None:
        return jsonify({"error": "Missing start income"}), 400

    # Run the simulation
    if not simulation.start_simulation(start_income, time_steps):
        return jsonify({"error": "Simulation already running"}), 400

    return jsonify("Simulation started")


@app.route('/simulation/end', methods=['POST'])
def end_simulation():
    simulation.end_simulation()
    return jsonify({"message": "Simulation ended"})


@app.route('/simulation/save', methods=['POST'])
def save_simulation():
    simulation.save_simulation()
    return jsonify({"message": "Simulation saved"})


@app.route('/simulation/results', methods=['GET'])
def get_simulation():
    return jsonify(simulation.get_simulation_results().to_dict())


@app.route('/thing_maker/buy/<thing_name>', methods=['GET'])
def buy_thing(thing_name):
    if thing_name is None:
        return jsonify({"error": "Missing thing name"}), 400

    ThingMaker.buy_thing(thing_name)

    return jsonify("Thing bought")


@app.route('/thing_maker/buyable', methods=['GET'])
def get_buyable_things():
    return jsonify(ThingMaker.get_buyable_things())


if __name__ == '__main__':
    app.run(debug=True)
