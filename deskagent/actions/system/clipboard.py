




class GetClipboard(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        pb = NSPasteboard.generalPasteboard()
        content = pb.stringForType_(NSStringPboardType)
        return content

class SetClipboard(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)

    def execute(self, config):
        text = config.get('text', "")

        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, NSStringPboardType)

#TODO
class CleanClipboard(Action):
    def __init__(self, logger=None):
        Action.__init__(self, logger)