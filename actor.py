import threading
from typing import List
from threading import Lock
import logging

from message import (
        Message, encode, decode, sort,
        OP_RELEASE, OP_ENTER, OP_ALLOW)
from channel import Chan


class Actor:
    def __init__(self, self_pid:int, peer_pids:List[int]):
        self.queue = []
        self.queue_lock = Lock()
        self.clock = 0
        self.pid = self_pid
        self.peers = peer_pids
        self.chan = Chan(self.pid)

    def allowToEnter(self, requester:int):
        self.clock += 1
        Msg = Message(self.clock, self.pid, OP_ALLOW)
        msg = encode(Msg)
        self.chan.sendTo([requester], msg)

    def allowedToEnter(self) -> bool:
        if len(self.queue) == 0:
            return False
        if self.queue[0].pid != self.pid:
            return False
        contacted = set([r.pid for r in self.queue[1:]])
        if len(contacted) == len(self.peers):
            return True
        else:
            return False

    def cleanupQ(self):
        self.queue_lock.acquire()
        # tmp = [r for r in self.queue if r.op != OP_ALLOW]
        self.queue = sort(self.queue)
        self.queue_lock.release()

    def receive(self, stop:threading.Event, timeout:float):
        msg = self.chan.recvFrom(stop, timeout)
        if msg is None:
            return
        Msg = decode(msg)
        self.clock = max(self.clock, Msg.clock)
        self.clock += 1
        if Msg.op == OP_ENTER:
            logging.info(f"node {self.pid} # clock {self.clock} receive ENTER from node {Msg.pid}")
            self.queue_lock.acquire()
            self.queue.append(Msg)
            self.queue_lock.release()
            self.allowToEnter(Msg.pid)
        elif Msg.op == OP_ALLOW:
            logging.info(f"node {self.pid} # clock {self.clock} receive ALLOW from node {Msg.pid}")
            self.queue_lock.acquire()
            self.queue.append(Msg)
            self.queue_lock.release()
        elif Msg.op == OP_RELEASE:
            logging.info(f"node {self.pid} # clock {self.clock} receive RELEASE from node {Msg.pid}")
            self.queue_lock.acquire()
            del(self.queue[0])
            self.queue_lock.release()
        self.cleanupQ()

    def requestToEnter(self):
        self.clock += 1
        Msg = Message(self.clock, self.pid, OP_ENTER)
        self.queue_lock.acquire()
        self.queue.append(Msg)
        self.queue_lock.release()
        self.cleanupQ()
        msg = encode(Msg)
        self.chan.sendTo(self.peers, msg)

    def release(self):
        tmp = [r for r in self.queue[1:] if r.op == OP_ENTER]
        self.queue_lock.acquire()
        self.queue = tmp
        self.queue_lock.release()
        self.clock += 1
        Msg = Message(self.clock, self.pid, OP_RELEASE)
        msg = encode(Msg)
        self.chan.sendTo(self.peers, msg)
