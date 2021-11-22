'''
Demo of lamport clock.

Node sequence of entering critical section:
1. Node3
2. Node1
3. Node3
4. Node2
5. Node2
6. Node1
'''
import time
import os
import signal
import queue
import logging
from typing import List
import threading
from multiprocessing import Process, Queue

from actor import Actor


def Node(pid:int, peer_pids:List[int], cmd:Queue):
    node = Actor(pid, peer_pids)
    logfilepath = f"node{pid}.log"
    if os.path.isfile(logfilepath):
        os.remove(logfilepath)
    logging.basicConfig(
            filename=logfilepath,
            level=logging.DEBUG,
            format='%(asctime)s %(message)s')

    def listen(stop:threading.Event):
        while not stop.is_set():
            node.receive(stop, timeout=1.0)

    backgroud_stop = threading.Event()
    backgroud = threading.Thread(
        target=listen, daemon=True, args=(backgroud_stop,))
    backgroud.start()

    while True:
        try:
            token = cmd.get(timeout=1)
        except queue.Empty:
            continue
        if token is None:
            print("None token get")
            break
        logging.info(f"node {pid} # clock {node.clock} request")
        node.requestToEnter()
        while not node.allowedToEnter():
            time.sleep(0.05)
        logging.info(f"node {pid} # clock {node.clock} # enter")
        time.sleep(3)   # do some shit inside critical section
        logging.info(f"node {pid} # clock {node.clock} release")
        node.release()

    backgroud_stop.set()
    backgroud.join()


if __name__ == '__main__':
    print(f"main process id: {os.getpid()}")

    # ignore SIGINT
    default_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    queue1 = Queue()
    queue2 = Queue()
    queue3 = Queue()

    node1 = Process(
        name="node1", target=Node, args=(1, [2,3], queue1))
    node2 = Process(
        name="node2", target=Node, args=(2, [1,3], queue2))
    node3 = Process(
        name="node3", target=Node, args=(3, [1,2], queue3))

    node1.start()
    node2.start()
    node3.start()
    print("All nodes are started!")

    # restore default signal handler for SIGINT
    signal.signal(signal.SIGINT, default_handler)

    try:
        # step 1
        time.sleep(1)
        queue3.put("request")

        # step 2
        time.sleep(1)
        queue1.put("request")

        # step 3
        time.sleep(1)
        queue3.put("request")

        # step 4
        time.sleep(1)
        queue2.put("request")

        # step 5
        time.sleep(1)
        queue2.put("request")

        # step 6
        time.sleep(1)
        queue1.put("request")

        time.sleep(1)
        print("All request sent!")

        signal.pause()

    except KeyboardInterrupt:
        print("receive keyboard interupt")
        queue1.put(None)
        queue2.put(None)
        queue3.put(None)
        node1.join()
        node2.join()
        node3.join()

        print("Reap all child processes. Exiting...")

