"""Native macOS audio tool adapter used by audio actions."""
import platform
import subprocess

from deskagent.platform.base.audio import AudioService


class MacOSAudioService(AudioService):
    def check_available(self):
        if platform.system() != "Darwin":
            raise RuntimeError("System audio actions are available only on macOS")

    def list_voices(self):
        return subprocess.run(["/usr/bin/say", "-v", "?"], capture_output=True,
                              text=True, timeout=10, check=True).stdout

    def start_speech(self, source, voice=None, rate=None):
        command = ["/usr/bin/say", "-f", str(source)]
        if voice:
            command += ["-v", voice]
        if rate:
            command += ["-r", str(rate)]
        return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def render_speech(self, source, destination, voice=None):
        command = ["/usr/bin/say", "-f", str(source), "-o", str(destination)]
        if voice:
            command += ["-v", voice]
        subprocess.run(command, capture_output=True, timeout=120, check=True)

    def start_playback(self, source):
        return subprocess.Popen(["/usr/bin/afplay", str(source)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def file_info(self, source):
        return subprocess.run(["/usr/bin/afinfo", str(source)], capture_output=True,
                              text=True, timeout=15, check=True).stdout

    def convert(self, source, destination, file_format, data_format, channels=None, track=None):
        command = ["/usr/bin/afconvert", "-f", file_format, "-d", data_format]
        if channels is not None:
            command += ["-c", str(channels)]
        if track is not None:
            command += ["--read-track", str(track)]
        command += [str(source), "-o", str(destination)]
        subprocess.run(command, capture_output=True, timeout=120, check=True)
