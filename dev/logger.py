import sys
import time


# Global variable to hold the current logger instance
_current_logger = None

def log(*args, **kwargs):
    if _current_logger is not None:
        _current_logger.log(*args, **kwargs)


def set_logger(logger):
    global _current_logger
    _current_logger = logger


class Logger:
    def __init__(self, log_level='dev', log_mode=False, log_timestamp=True, write_to_stderr=True, write_to_file=None):
        """
        Initialize the Logger.
        :param log_level: 'dev', 'test', or 'prod'
        :param log_timestamp: If True, include timestamps in log messages.
        :param write_to_stderr: If True, log messages to standard error.
        :param write_to_file: If provided, log messages to the specified file.
        """
        if log_level not in ['dev', 'test', 'prod']:
            raise ValueError("log_level must be 'dev', 'test', or 'prod'")
        self.log_level = log_level
        self.log_timestamp = log_timestamp
        self.write_to_stderr = write_to_stderr
        self.write_to_file = write_to_file
        if write_to_file:
            self.file = open(write_to_file, 'a')


    def _write(self, message):
        if self.write_to_stderr:
            print(message, file=sys.stderr)
        if self.write_to_file:
            self.file.write(message + '\n')
            self.file.flush()


    def log(self, *args, level='dev'):
        """
        Log a message based on the current log_level. Any number of
        positional arguments can be passed. They will be converted to
        strings and concatenated with spaces, similar to the built-in
        print function.

        :param level: The log level (0=testing, ..., n=prod).
        """
        msg = ''
        if self.log_timestamp:
            if 'strftime' in dir(time):
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                timestamp = f'{time.time_ns()/1e9:.2f}'
            msg += f"[{timestamp}] "
        msg += f"({self.log_level.upper()}) "
        msg += ' '.join(str(arg) for arg in args)

        if self.log_level == 'dev':
            self._write(msg)
        elif self.log_level == 'test' and level in ['test', 'prod']:
            self._write(msg)
        elif self.log_level == 'prod' and level == 'prod':
            self._write(msg)
