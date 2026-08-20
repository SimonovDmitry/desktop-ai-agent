


class LockScreen(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        run(["osascript", "-e", 'tell application "System Events" to keystroke "q" using {control down, command down}'])


class SleepComputer(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        run(["osascript", "-e", 'tell application "System Events" to sleep'])


class RestartComputer(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        run(["sudo", "shutdown", "-r", "now"], check=True)


class ShutdownComputer(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        run(["sudo", "shutdown", "now"], check=True)

#TODO
class LogoutComputer(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

# TODO
class CancelShutdownComputer(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)