from struct import pack, unpack
from typing import List


OP_RELEASE = 0
OP_ENTER = 1
OP_ALLOW = 2
MSGFMT = "llh"


class Message:
    def __init__(self, clock:int, pid:int, op:int):
        self.clock = clock
        self.pid = pid
        self.op = op

    def __str__(self) -> str:
        return f"clock:{self.clock}:pid:{self.pid}:op:{self.op}"

    def __repr__(self) -> str:
        return str(self)


def encode(Msg:Message) -> bytes:
    return pack(MSGFMT, Msg.clock, Msg.pid, Msg.op)


def decode(msg:bytes) -> Message:
    clock, pid, op = unpack(MSGFMT, msg)
    return Message(clock, pid, op)


def sort(Msg_list:List[Message]) -> List[Message]:
    '''
    sort Msg_list base on clock value in increasing order
    '''
    return sorted(Msg_list, reverse=False, key=lambda Msg: Msg.clock)


if __name__ == '__main__':
    def test_sort():
        import random
        messages = []
        for i in range(10):
            messages.append(Message(i, 3, 3))
        random.shuffle(messages)
        new_messages = sorted(messages, reverse=False, key=lambda Msg: Msg.clock)
        print("Done sorting")

    def test_modem():
        Msg = Message(1,2,3)
        print(Msg)
        msg = encode(Msg)
        another_Msg = decode(msg)
        print(another_Msg)

    # test_sort()
    test_modem()
