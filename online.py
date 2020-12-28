import socket
import threading
import time
import traceback

import tkinter as tk

from tkinter import simpledialog


class OnlineDialog(simpledialog.Dialog):
    def __init__(self, parent):
        simpledialog.Dialog.__init__(self, title="Online Chess", parent=parent)

    def body(self, master):
        self.raddr = tk.StringVar()
        self.lport = tk.StringVar()
        self.rport = tk.StringVar()
        self.active = tk.BooleanVar()

        addr_label = tk.Label(master, text="Address:", justify=tk.LEFT)
        addr_entry = tk.Entry(master, textvariable=self.raddr)

        local_label = tk.Label(master, text="Local port (empty defaults to remote port):", justify=tk.LEFT)
        local_entry = tk.Entry(master, textvariable=self.lport)

        remote_label = tk.Label(master, text="Remote port:", justify=tk.LEFT)
        remote_entry = tk.Entry(master, textvariable=self.rport)

        active_label = tk.Label(master, text="Active:", justify=tk.LEFT)
        active_tickbox = tk.Checkbutton(master, variable=self.active)

        addr_label.grid(row=0, column=0)
        addr_entry.grid(row=0, column=1)

        local_label.grid(row=1, column=0)
        local_entry.grid(row=1, column=1)

        remote_label.grid(row=2, column=0)
        remote_entry.grid(row=2, column=1)

        active_label.grid(row=3, column=0)
        active_tickbox.grid(row=3, column=1)

        return addr_entry

    def validate(self):
        addr, lport, rport, active = self.raddr.get(), self.lport.get(), self.rport.get(), self.active.get()

        if rport:
            if lport:
                ...
            else:
                lport = rport

            lport = int(lport)
            rport = int(rport)
        else:
            return False

        self.result = addr, lport, rport, active
        return True


def make_socket(remote_address, remote_port, local_port=None, active=True):
    if not local_port:
        local_port = remote_port

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", local_port))

    def listen(s, ret):
        print("listening")
        s.listen(0)
        s, a = s.accept()
        print("accepted", a)

        ret.append((s, a))

    if active:
        print("trying to connect", (remote_address, remote_port))

        while True:
            try:
                s.connect((remote_address, remote_port))
                break
            except:
                traceback.print_exc()
                print("retrying")
                time.sleep(10)
    else:
        ret = []

        t = threading.Thread(target=lambda: listen(s, ret))
        t.start()

        try:
            while t.is_alive():
                t.join(1)
            s, a = ret[0]
        except:
            s.close()
            t.join()
            print("stopping listening")
            return

    print("connected")

    return s


__all__ = ["OnlineDialog", "make_socket"]