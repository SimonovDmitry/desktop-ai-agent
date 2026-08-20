from deskagent.actions.base import Action


class GetCursorPosition(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        loc = NSEvent.mouseLocation()
        x = int(loc.x)

        screen_height = NSScreen.mainScreen().frame().size.height
        y = int(screen_height - loc.y)

        return {"x": x, "y": y}


#TODO
class MoveMouse(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)


# TODO
class Click(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)
    def execute(self, config):


# TODO
class DoubleClick(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

#TODO
class DragMouse(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

#TODO
class ScrollMouse(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)