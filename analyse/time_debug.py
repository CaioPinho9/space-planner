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

        avg_time_list = []
        for key in cls.__start_time:
            avg_time = 0
            start_list = cls.__start_time[key]
            end_list = cls.__end_time[key]
            for i in range(len(start_list)):
                avg_time += ((end_list[i]) - start_list[i]) * 1000
                avg_time_list.append(avg_time)

        text = [f'{key}: {avg_time:.2f}ms' for key, avg_time in zip(cls.__start_time, avg_time_list)]
        text = '\n'.join(text)
        with open(cls.__DEBUG_TIME_TXT, 'w') as f:
            f.write(text)
