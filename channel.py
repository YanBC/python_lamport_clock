import socket
from struct import pack, unpack
import threading
from typing import List

from message import Message


CHAN_ADDR = ""      # wildcard addr (INADDR_ANY)
# CHAN_ADDR = "<broadcast>"      # broadcast addr (INADDR_BROADCAST), unavailable on MacOS
CHAN_PORT = 9553
ChanFMT = 'l18s'


def get_sock(addr:str=CHAN_ADDR, port:int=CHAN_PORT) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind((addr, port))
    return sock


class Chan:
    def __init__(self, recv_pid:int) -> None:
        '''
        pid, as in peer id, bad naming, I know
        '''
        self.sock = get_sock()
        self.pid = recv_pid

    def sendTo(self, pid_list:List[int], msg:bytes) -> None:
        for pid in pid_list:
            data = pack(ChanFMT, pid, msg)
            self.sock.sendto(data, ('<broadcast>', CHAN_PORT))

    def recvFrom(self, stop:threading.Event, timeout:float) -> bytes:
        '''
        return the next message recveived,
        storing in buffer or not,
        if not, will block
        '''
        msg = None
        self.sock.settimeout(timeout)
        while not stop.is_set():
            try:
                data, _ = self.sock.recvfrom(1024)
            except socket.timeout:
                continue
            target_pid, msg = unpack(ChanFMT, data)
            if target_pid == self.pid:
                break
        return msg
