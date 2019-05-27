import time
import datetime
import threading


class Logger:
    def __init__(self, module_name, log_checks=False, debug_level=4):
        self.last_time = time.time()
        self.debug_level = debug_level
        self.last_percentage = 0
        self.module_name = module_name
        self.log_checks = log_checks
        self.colors = {
            'HEADER': '\033[95m',
            'OKBLUE': '\033[94m',
            'OKGREEN': '\033[92m',
            'WARNING': '\033[93m',
            'FAIL': '\033[91m',
            'ENDC': '\033[0m',
            'BOLD': '\033[1m',
            'UNDERLINE': '\033[4m',
            'WHITE': ''
        }
        self.checks = []
        self.operations = []
        self.last_check = None

    def debug(self, msg, color='WHITE'):
        if self.debug_level > 3:
            color = self.colors[color]
            print(color + f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {self.module_name} DEBUG: {msg}' + self.colors['ENDC'])

    def info(self, msg, color='WHITE'):
        if self.debug_level > 2:
            color = self.colors[color]
            print(color + f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {self.module_name} INFO: {msg}' + self.colors['ENDC'])

    def warning(self, msg, color='WARNING'):
        if self.debug_level > 1:
            color = self.colors[color]
            print(color + f'{datetime.datetime.now()}: {self.module_name} WARNING: {msg}' + self.colors['ENDC'])

    def error(self, msg, color='FAIL'):
        if self.debug_level > 0:
            color = self.colors[color]
            print(color + f'{datetime.datetime.now()}: {self.module_name} ERROR: {msg}' + self.colors['ENDC'])

    def percent(self, i, max_i, msg=None):
        delta_time = time.time() - self.last_time
        if msg is None:
            if delta_time > 10 and int(100 * i / max_i) != self.last_percentage:
                self.last_time = time.time()
                self.last_percentage = int(100 * i / max_i)
                print(f'{int(100 * i / max_i)}%')

        else:
            if delta_time > 10:
                self.last_time = time.time()
                print(msg)

    def init_checks(self):
        if self.log_checks:
            self.checks = []
            self.operations = []
            self.last_check = time.time()

    def chekpoint(self, operation):
        if self.log_checks:
            assert self.last_check is not None, Exception('no check initialized')
            self.checks.append(time.time()-self.last_check)
            self.operations.append(operation)
            self.last_check = time.time()

    def end_checks(self):
        if self.log_checks:
            assert len(self.checks) > 0, Exception('no checkpoints stored')
            overall_time = sum(self.checks)
            for elapsed_time, operation in zip(self.checks, self.operations):
                print(f'{operation}: elapsed time {elapsed_time}, ocupation percentage {int(100 * elapsed_time / overall_time)}%')

            self.last_check = None
            self.checks = []
            self.operations = []

    def start_loading_thread(self, msg, timescale=None):
        self.info(msg)
        interval = 2 if timescale is None else timescale / 100
        self.kill_loading_thread = False
        def loading_thread():
            print(100*'_')
            while True:
                time.sleep(interval)
                if self.kill_loading_thread:
                    break
                print('#', end='', flush=True)

        self.load_thread = threading.Thread(target=loading_thread)
        self.load_thread.start()

    def stop_loading_thread(self, msg):
        print('\n')
        self.info(msg)
        self.kill_loading_thread = True




