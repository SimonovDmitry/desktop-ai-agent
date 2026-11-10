from deskagent.actions.browser.base import BrowserAction


class ListBrowserDownloads(BrowserAction):
    name = "list_browser_downloads"
    description = "List downloads started by the browser action service"
    parameters_schema = {}

    def execute(self, context, parameters):
        return self.run(context, lambda: {
            "downloads": [item.to_dict() for item in self.manager(context).list_downloads()]
        })


class DownloadURL(BrowserAction):
    name = "download_url"
    description = "Download a validated HTTP(S) URL into an allowlisted directory"
    parameters_schema = {
        "url": {"type": "string", "required": True},
        "directory": {"type": "string", "required": False},
        "filename": {"type": "string", "required": False},
        "headers": {"type": "dict", "required": False},
    }

    def execute(self, context, parameters):
        return self.run(
            context,
            lambda: self.manager(context).download(
                parameters["url"], parameters.get("directory"), parameters.get("filename"), parameters.get("headers")
            ).to_dict(),
        )


class WaitForDownload(BrowserAction):
    name = "wait_for_download"
    description = "Wait for a managed download to complete, fail, or be cancelled"
    parameters_schema = {
        "download_id": {"type": "string", "required": True},
        "timeout": {"type": "float", "required": False, "default": 60, "minimum": 0.1, "maximum": 3600},
    }

    def execute(self, context, parameters):
        return self.run(
            context, lambda: self.manager(context).wait_download(
                parameters["download_id"], parameters.get("timeout", 60)
            ).to_dict(),
        )


class CancelDownload(BrowserAction):
    name = "cancel_download"
    description = "Request cancellation of a managed in-progress download"
    parameters_schema = {"download_id": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        return self.run(context, self.manager(context).cancel_download, parameters["download_id"])


class GetDownloadStatus(BrowserAction):
    name = "get_download_status"
    description = "Get byte progress and state for a managed download"
    parameters_schema = {"download_id": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        return self.run(
            context, lambda: self.manager(context).download_status(parameters["download_id"]).to_dict()
        )


class RevealDownloadedFile(BrowserAction):
    name = "reveal_downloaded_file"
    description = "Reveal a completed download in the system file manager"
    parameters_schema = {"download_id": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        return self.run(context, self.manager(context).reveal_download, parameters["download_id"])
