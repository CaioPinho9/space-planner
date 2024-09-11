import multiprocessing
import numpy as np
import pickle
from datetime import datetime
from multiprocessing import shared_memory

from managers.thing_maker import ThingMaker


class SharedMemory:
    def __init__(self, thread_count):
        self._thread_count = thread_count

        # Initialize shared memory for variables
        self._best_income = multiprocessing.Value('d', 0.0)
        self._best_index = multiprocessing.Value('i', -1)

        # Shared memory for best_log (list of lists)
        self._best_log_size = 4096  # Adjust this size based on your needs
        self._best_log_shm = shared_memory.SharedMemory(create=True, size=self._best_log_size)
        self._best_log = np.ndarray((self._best_log_size,), dtype='b', buffer=self._best_log_shm.buf)

        # Shared arrays
        self._total_income_shm, self._total_income = self._create_shared_array(thread_count)
        self._simulation_index_shm, self._simulation_index = self._create_shared_array(thread_count)
        self._simulation_index_since_last_thing_shm, self._simulation_index_since_last_thing = self._create_shared_array(thread_count)

        # Shared memory for things list (serialized)
        self._things_size = 4096  # Placeholder size, adjust as needed
        self._things_shm = shared_memory.SharedMemory(create=True, size=self._things_size)
        self._things_array = np.ndarray((self._things_size,), dtype='b', buffer=self._things_shm.buf)

        self.start_time = datetime.now()

    def _create_shared_array(self, size):
        shm = shared_memory.SharedMemory(create=True, size=size * np.dtype('d').itemsize)
        array = np.ndarray((size,), dtype='d', buffer=shm.buf)
        return shm, array

    def _serialize(self, obj):
        return pickle.dumps(obj)

    def _deserialize(self, data):
        return pickle.loads(data)

    def increase_simulation(self, thread_id, income, multiplier):
        self._simulation_index[thread_id] += multiplier
        self._simulation_index_since_last_thing[thread_id] += multiplier
        self._total_income[thread_id] += income * multiplier

    @property
    def best_income(self):
        return self._best_income.value

    @property
    def best_log(self):
        # Check if there is something to deserialize
        serialized_data = self._best_log.tobytes()
        if len(serialized_data) > 0:
            try:
                return self._deserialize(serialized_data)
            except (pickle.PickleError, EOFError) as e:
                print(f"Error deserializing best_log: {e}")
        return []

    @property
    def best_index(self):
        return self._best_index.value

    @property
    def things(self):
        # Check if there is something to deserialize
        serialized_data = self._things_array.tobytes()
        if len(serialized_data) > 0:
            try:
                return self._deserialize(serialized_data)
            except (pickle.PickleError, EOFError) as e:
                print(f"Error deserializing things: {e}")
        return []

    @best_income.setter
    def best_income(self, value):
        self._best_income.value = value

    @best_log.setter
    def best_log(self, value):
        # Serialize the list of lists and store it in shared memory
        serialized_data = self._serialize(value)
        size = len(serialized_data)

        # Resize shared memory if necessary
        if size > self._best_log_shm.size:
            self._resize_shared_memory(self._best_log_shm, size)
            self._best_log = np.ndarray((size,), dtype='b', buffer=self._best_log_shm.buf)

        np.copyto(self._best_log, np.frombuffer(serialized_data, dtype='b'))

    @best_index.setter
    def best_index(self, value):
        self._best_index.value = value

    @things.setter
    def things(self, value):
        # Serialize the list of objects and store it in shared memory
        serialized_data = self._serialize(value)
        size = len(serialized_data)

        # Resize shared memory if necessary
        if size > self._things_shm.size:
            self._resize_shared_memory(self._things_shm, size)
            self._things_array = np.ndarray((size,), dtype='b', buffer=self._things_shm.buf)

        np.copyto(self._things_array, np.frombuffer(serialized_data, dtype='b'))

    def _resize_shared_memory(self, shm, new_size):
        shm.close()
        shm.unlink()
        new_shm = shared_memory.SharedMemory(create=True, size=new_size)
        new_array = np.ndarray((new_size,), dtype='b', buffer=new_shm.buf)
        return new_shm, new_array

    @property
    def total_income(self):
        return self._total_income

    @property
    def simulation_index(self):
        return self._simulation_index

    @property
    def simulation_index_since_last_thing(self):
        return self._simulation_index_since_last_thing

    @simulation_index_since_last_thing.setter
    def simulation_index_since_last_thing(self, value):
        np.copyto(self._simulation_index_since_last_thing, value)

    @total_income.setter
    def total_income(self, value):
        np.copyto(self._total_income, value)

    def to_dict(self):
        total_income_sum = sum(self.total_income)
        simulation_index_sum = sum(self.simulation_index)
        simulation_index_since_last_thing_sum = sum(self.simulation_index_since_last_thing)

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
            "best_log": self.best_log,
            "best_index": self.best_index,
            "simulation_index": simulation_index_sum,
            "average_income": total_income_sum / simulation_index_since_last_thing_sum,
            "time_elapsed": elapsed_time.total_seconds(),
            "simulations_per_second": simulation_index_sum / elapsed_time.total_seconds(),
            "simulation_time": elapsed_time.total_seconds() / simulation_index_sum * self._thread_count,
            "current_income": ThingMaker.current_income(self.things)
        }

    def reset_buy(self):
        self.simulation_index_since_last_thing = [0] * len(self.simulation_index_since_last_thing)
        self.total_income = [0] * len(self.total_income)
