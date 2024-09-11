import time



class TimeDebug:
    __DEBUG_TIME_TXT = 'resource/debug/time_debug.txt'

    __start_time = {}
    __end_time = {}

    @classmethod
    def start(cls, process_id, key):
        if process_id != 0:
            return

        if key not in cls.__start_time:
            cls.__start_time[key] = []

        cls.__start_time[key].append(time.time())

    @classmethod
    def end(cls, process_id, key):
        if process_id != 0:
            return

        if key not in cls.__end_time:
            cls.__end_time[key] = []

        cls.__end_time[key].append(time.time())

        if len(cls.__start_time[key]) != len(cls.__end_time[key]):
            raise Exception(f'Key {key} has different start and end times')

        with open(cls.__DEBUG_TIME_TXT, 'w') as f:
            pass

        for key in cls.__start_time:
            avg_time = 0
            start_list = cls.__start_time[key]
            end_list = cls.__end_time[key]
            for i in range(len(start_list)):
                avg_time += ((end_list[i]) - start_list[i]) * 1000

            print(f'{key} took {avg_time} ms')
            with open(cls.__DEBUG_TIME_TXT, 'a') as f:
                f.write(f'{key} took {avg_time} ms\n')
