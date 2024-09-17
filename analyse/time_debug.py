import multiprocessing
import time


class TimeDebug:
    __DEBUG_TIME_TXT = 'resource/debug/time_debug.txt'

    __start_time = {}
    __end_time = {}
    __mean_time = {}
    __current_iteration = {}
    __multiprocessing_pid = multiprocessing.Value('i', -10)

    @classmethod
    def start(cls, key):
        pid = multiprocessing.current_process().pid
        if cls.__multiprocessing_pid.value <= -2:
            cls.__multiprocessing_pid.value += 1
        elif cls.__multiprocessing_pid.value == -1:
            with multiprocessing.Lock():
                if cls.__multiprocessing_pid.value == -1:
                    cls.__multiprocessing_pid.value = pid

        if pid != cls.__multiprocessing_pid.value:
            return

        cls.__start_time[key] = time.time()

    @classmethod
    def end(cls, key):
        pid = multiprocessing.current_process().pid
        if pid != cls.__multiprocessing_pid.value:
            return

        cls.__end_time[key] = time.time()

        mean_time = (cls.__end_time[key] - cls.__start_time[key]) * 1000

        if key not in cls.__mean_time:
            cls.__mean_time[key] = 0
            cls.__current_iteration[key] = 0

        cls.__mean_time[key] = (cls.__mean_time[key] * cls.__current_iteration[key] + mean_time) / (cls.__current_iteration[key] + 1)

        cls.__current_iteration[key] += 1

        text = [f'{key}: {mean_time:.5f}ms' for key, mean_time in cls.__mean_time.items()]
        text = '\n'.join(text)

        with open(cls.__DEBUG_TIME_TXT, 'w') as f:
            f.write(text)
