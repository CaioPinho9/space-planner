import multiprocessing
import pickle
from datetime import datetime


class SharedMemory:
    def __init__(self, thread_count):
        # Use manager to share the values across processes
        manager = multiprocessing.Manager()

        # Shared variables for inter-process communication
        self._best_income = manager.Value('d', 0.0)
        self._best_log = manager.list()
        self._best_index = manager.Value('i', -1)

        self.start_time = None

        # Shared arrays
        self._total_income = manager.list([0] * thread_count)
        self._simulation_index = manager.list([0] * thread_count)

    def increase_thread_income(self, thread_id, income):
        self._total_income[thread_id] += income

    def update_simulation_index(self, thread_id, index):
        self._simulation_index[thread_id] = index

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
        # read from file pickle
        with open("buyable.pickle", "rb") as f:
            return pickle.load(f)

    @property
    def total_income(self):
        return self._total_income

    @property
    def simulation_index(self):
        return self._simulation_index

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
        with open("buyable.pickle", "wb") as f:
            pickle.dump(value, f)

    def to_dict(self):
        total_income_sum = sum(self.total_income)
        simulation_index_sum = sum(self.simulation_index)
        if simulation_index_sum == 0 or not self.start_time:
            return {
                "best_income": 0,
                "best_log": [],
                "best_index": -1,
                "simulation_index": 0,
                "average_income": 0,
                "time_elapsed": 0,
                "simulations_per_second": 0
            }
        elapsed_time = datetime.now() - self.start_time
        return {
            "best_income": self.best_income,
            "best_log": list(self.best_log),
            "best_index": self.best_index,
            "simulation_index": simulation_index_sum,
            "average_income": total_income_sum / simulation_index_sum,
            "time_elapsed": elapsed_time.total_seconds(),
            "simulations_per_second": simulation_index_sum / elapsed_time.total_seconds()
        }
