import multiprocessing
import pickle
from datetime import datetime

from potato_types import ThingMaker


class SharedMemory:
    def __init__(self, thread_count):
        # Use self.manager to share the values across processes
        self._things = []
        manager = multiprocessing.Manager()

        # Shared variables for inter-process communication
        self._best_income = manager.Value('d', 0.0)
        self._best_log = manager.list()
        self._best_index = manager.Value('i', -1)

        self.start_time = None

        # Shared arrays
        self._total_income = manager.list([0] * thread_count)
        self._simulation_index = manager.list([0] * thread_count)
        self._simulation_index_since_last_thing = manager.list([0] * thread_count)

        self._shared_memory_file = "resource/shared/shared_things.pickle"

    def increase_thread_income(self, thread_id, income):
        self._total_income[thread_id] += income

    def increase_simulation_index(self, thread_id):
        self._simulation_index[thread_id] += 1
        self._simulation_index_since_last_thing[thread_id] += 1

    @property
    def best_income(self):
        return self._best_income.value

    @property
    def best_log(self):
        return self._best_log

    @property
    def best_index(self):
        return self._best_index.value

    @property
    def things(self):
        # read from file
        try:
            with open(self._shared_memory_file, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return []

    @property
    def total_income(self):
        return self._total_income

    @property
    def simulation_index(self):
        return self._simulation_index

    @property
    def simulation_index_since_last_thing(self):
        return self._simulation_index_since_last_thing

    @best_income.setter
    def best_income(self, value):
        self._best_income.value = value

    @best_log.setter
    def best_log(self, value):
        self._best_log[:] = value

    @best_index.setter
    def best_index(self, value):
        self._best_index.value = value

    @things.setter
    def things(self, value):
        # write in file pickle
        with open(self._shared_memory_file, "wb") as f:
            pickle.dump(value, f)


    @simulation_index_since_last_thing.setter
    def simulation_index_since_last_thing(self, value):
        self._simulation_index_since_last_thing[:] = value

    @total_income.setter
    def total_income(self, value):
        self._total_income[:] = value

    def to_dict(self):
        total_income_sum = sum(self.total_income)
        simulation_index_sum = sum(self.simulation_index)
        simulation_index_since_last_thing_sum = sum(self._simulation_index_since_last_thing)

        if simulation_index_sum == 0 or simulation_index_since_last_thing_sum == 0 or not self.start_time:
            return {
                "best_income": 0,
                "best_log": [],
                "best_index": -1,
                "simulation_index": 0,
                "average_income": 0,
                "time_elapsed": 0,
                "simulations_per_second": 0,
                "simulation_time": 0,
                "current_income": 0
            }
        elapsed_time = datetime.now() - self.start_time
        return {
            "best_income": self.best_income,
            "best_log": list(self.best_log),
            "best_index": self.best_index,
            "simulation_index": simulation_index_sum,
            "average_income": total_income_sum / simulation_index_since_last_thing_sum,
            "time_elapsed": elapsed_time.total_seconds(),
            "simulations_per_second": simulation_index_sum / elapsed_time.total_seconds(),
            "simulation_time": elapsed_time.total_seconds() / simulation_index_sum,
            "current_income": ThingMaker.current_income(self.things)
        }

    def reset_buy(self):
        self.simulation_index_since_last_thing = [0] * len(self._simulation_index_since_last_thing)
        self.total_income = [0] * len(self._total_income)
