

class SetVolume(Action):
    def __init__(self, logger=None):

        Action.__init__(self, logger)

    def execute(self, config):

        volume_level = config.get('volume_level', None)
        if volume_level is None:
            raise ValueError('Volume level must be set')

        if not isinstance(volume_level, int):
            raise ValueError('Volume level must be int')

        run(["osascript", "-e", f"set volume output volume {volume_level}"])


class IncreaseVolume(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        cmd = ['osascript', '-e', 'output volume of (get volume settings)']
        volume_level = check_output(cmd).decode('utf-8').strip()
        volume_new = int(volume_level) + 10
        run(["osascript", "-e", f"set volume output volume {volume_new}"])


class DecreaseVolume(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        cmd = ['osascript', '-e', 'output volume of (get volume settings)']
        volume_level = check_output(cmd).decode('utf-8').strip()
        volume_new = int(volume_level) - 10
        run(["osascript", "-e", f"set volume output volume {volume_new}"])


class Mute(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        run(["osascript", "-e", "set volume output muted true"])


class Unmute(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        run(["osascript", "-e", "set volume output muted false"])


class GetVolume(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        cmd = ['osascript', '-e', 'output volume of (get volume settings)']
        volume_level = check_output(cmd).decode('utf-8').strip()
        return volume_level