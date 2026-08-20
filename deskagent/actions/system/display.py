


class SetDisplayBrightness(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        level = config.get('brightness_level', None)

        if level is None:
            raise ValueError('Brightness level must be set')

        level = max(0, min(100, level))
        steps = round(level / 6.25)

        apple_script = f'''
        tell application "System Events"
            repeat 16 times
                key code 145 -- Код клавиши "Яркость вниз"
            end repeat
            repeat {steps} times
                key code 144 -- Код клавиши "Яркость вверх"
            end repeat
        end tell
        '''

        run(['osascript', '-e', apple_script], check=True)

class GetDisplayBrightness(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        pass #TODO: не получается рабочая реализация

class GetDisplays(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config=None):
        screens = NSScreen.screens()
        displays_info = []

        for i, screen in enumerate(screens):
            frame = screen.frame()
            description = screen.deviceDescription()

            display_id = description.objectForKey_("NSScreenNumber")
            is_primary = (i == 0)

            if is_primary:
                name = "Built-in Display" if len(screens) == 1 else "Primary Display"
            else:
                name = f"External Display {i}"

            displays_info.append({"id": str(display_id), "name": name, "primary": is_primary,
                                  "width": int(frame.size.width), "height": int(frame.size.height),
                                  "x": int(frame.origin.x), "y": int(frame.origin.y)})
            return displays_info

class GetScreenSize(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config=None):
        target_id = config.get('display_id') if config else None
        screens = NSScreen.screens()
        selected_screen = screens[0]
        if target_id:
            for screen in screens:
                if str(screen.deviceDescription().objectForKey_("NSScreenNumber")) == str(target_id):
                    selected_screen = screen
                    break
        size = selected_screen.frame().size
        return {"width": int(size.width), "height": int(size.height)}

#TODO
class SetResolution(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)