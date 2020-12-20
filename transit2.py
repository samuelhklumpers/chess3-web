import socket
import threading
import traceback


class Tunnel:
    def __init__(self, port):
        self.port = port
        self.rooms = {}
        self.workers = []

    def start(self):
        s = socket.socket()

        s.bind(('', self.port))
        s.settimeout(1.0)
        s.listen(128)
        try:
            while True:
                try:
                    c, a = s.accept()
                    tag = c.recv(1024).decode()
                    self.add_connection(tag, c)
                except socket.timeout:
                    ...
        except:
            self.close()

    def add_connection(self, tag, c):
        if tag not in self.rooms:
            self.rooms[tag] = []

        room = self.rooms[tag]

        worker = threading.Thread(target=lambda: self.transmit(tag, c, room))

        room.append(c)

        worker.start()
        self.workers.append(worker)

    def remove_connection(self, tag, conn):
        try:
            conn.shutdown(0)
            conn.close()
        except:
            traceback.print_exc()

        room = self.rooms[tag]
        if not room:
            return

        room.remove(conn)

        if not room:
            del self.rooms[tag]

    def transmit(self, tag, conn, room):
        try:
            data = True
            while data:
                data = conn.recv(1024)

                for _, conn2 in room:
                    if conn != conn2:
                        conn2.send(data)

            if conn in room:
                self.remove_connection(tag, conn)
        except:
            ...

    def close(self):
        while self.rooms:
            tag, room = next(iter(self.rooms))

            while tag:
                th, conn = room[-1]
                self.remove_connection(tag, conn)

                if th.is_alive():
                    print("couldn't close thread")
