import datetime

from server.daemon import Daemon
from server.gameserver import ServerDaemon


class MaintenanceDaemon(Daemon):
    def __init__(self):
        Daemon.__init__(self, "maintenance.pid")

        self.triggered = True

    def start_subdaemons(self):
        d = ServerDaemon()
        d.start()

    def stop_subdaemons(self):
        d = ServerDaemon()
        d.stop()

    def restart_subdaemons(self):
        d = ServerDaemon()
        d.restart()

    def cleanup(self):
        self.stop_subdaemons()

    def run(self):
        self.restart_subdaemons()

        while True:
            now = datetime.datetime.utcnow()

            if 3 <= now.hour <= 6 and not self.triggered:
                self.restart_subdaemons()
                self.triggered = True
            elif now.hour > 6 and self.triggered:
                self.triggered = False


if __name__ == "__main__":
    d = MaintenanceDaemon()
    d.start()