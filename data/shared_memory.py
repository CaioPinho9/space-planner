import multiprocessing


class SharedMemory:
    def __init__(self, thread_count):
        # Use manager to share the values across processes
        manager = multiprocessing.Manager()

        # Shared variables for inter-process communication
        self._best_income = manager.Value('d', 0.0)  # 'd' for double (float)
        self._best_log = manager.list()  # Use manager.list() for a shared list
        self._best_index = manager.Value('i', -1)  # 'i' for integer

        # Shared arrays
        self._total_income = manager.list([0] * thread_count)  # Shared list for incomes
        self._simulation_index = manager.list([0] * thread_count)  # Shared list for indices

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

    @best_income.setter
    def best_income(self, value):
        self._best_income.value = value

    @best_log.setter
    def best_log(self, value):
        self._best_log[:] = value

    @best_index.setter
    def best_index(self, value):
        self._best_index.value = value

    @property
    def total_income(self):
        return self._total_income

    @property
    def simulation_index(self):
        return self._simulation_index

    def to_dict(self):
        return {
            "best_income": self.best_income,
            "best_log": list(self.best_log),
            "best_index": self.best_index,
            "total_income": sum(self.total_income),
            "simulation_index": sum(self.simulation_index)
        }
