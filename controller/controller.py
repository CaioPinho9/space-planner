from analyse.predictor import Predictor
from flask import Flask, request, jsonify

from analyse.simulation import Simulation
from managers.thing_maker import ThingMaker

flask_app = Flask(__name__)

thing_maker = ThingMaker()
simulation = Simulation(thing_maker)
thing_maker.shared_memory = simulation.shared_memory


@flask_app.route('/simulation/start', methods=['POST'])
def start_simulation():
    configuration = request.get_json()

    if configuration is None:
        return jsonify({"error": "Invalid request"}), 400

    time_steps = configuration.get("time_steps", 900)
    start_income = configuration.get("start_income", None)

    # Run the simulation
    if not simulation.start_simulation(start_income, time_steps):
        return jsonify({"error": "Simulation already running"}), 400

    return jsonify("Simulation started")


@flask_app.route('/simulation/end', methods=['POST'])
def end_simulation():
    simulation.end_simulation()
    return jsonify({"message": "Simulation ended"})


@flask_app.route('/simulation/save', methods=['POST'])
def save_simulation():
    simulation.save_simulation()
    return jsonify({"message": "Simulation saved"})


@flask_app.route('/simulation/results', methods=['GET'])
def get_simulation():
    return jsonify(simulation.get_simulation_results().to_dict())


@flask_app.route('/simulation/reset', methods=['GET'])
def reset_simulation():
    simulation.reset_simulation()
    return jsonify({"message": "Simulation reset"})

@flask_app.route('/thing_maker/buy/<thing_name>', methods=['GET'])
def buy_thing(thing_name):
    if thing_name is None:
        return jsonify({"error": "Missing thing name"}), 400

    simulation.buy_thing()
    thing_maker.buy_thing(thing_name)

    return jsonify("Thing bought")


@flask_app.route('/thing_maker/buyable', methods=['GET'])
def get_buyable_things():
    return jsonify(thing_maker.get_buyable_things())


@flask_app.route('/predictor/thing_price/<thing_name>/<price>', methods=['GET'])
def predict_price(thing_name, price):
    Predictor.add_price_evolution(thing_name, price)
    return jsonify("Price added")

@flask_app.route('/predictor/thing_price', methods=['GET'])
def get_thing_price():
    return jsonify(Predictor.get_thing_price())


if __name__ == '__main__':
    flask_app.run(debug=True)
