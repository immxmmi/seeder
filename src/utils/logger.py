import datetime


class Logger:
    DEBUG_ENABLED = False

    @staticmethod
    def configure(debug: bool):
        Logger.DEBUG_ENABLED = debug

    @staticmethod
    def log(level, cls, msg):
        colors = {
            "DEBUG": "\033[94m",
            "INFO": "\033[92m",
            "WARN": "\033[93m",
            "ERROR": "\033[91m",
        }
        reset = "\033[0m"
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{colors.get(level, '')}[{ts}] [{level}] [{cls}] {msg}{reset}")

    @staticmethod
    def debug(cls, msg):
        if Logger.DEBUG_ENABLED:
            Logger.log("DEBUG", cls, msg)

    @staticmethod
    def info(cls, msg):
        Logger.log("INFO", cls, msg)

    @staticmethod
    def warn(cls, msg):
        Logger.log("WARN", cls, msg)

    @staticmethod
    def error(cls, msg):
        Logger.log("ERROR", cls, msg)
