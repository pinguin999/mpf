"""
This module implements a controller which does administration jobs and address management for the bus.
In the normal setup these functions would be performed by a specialized controller board.
"""
import concurrent.futures
import queue
from dataclasses import dataclass
from queue import Empty
import time

from serial.serialutil import SerialException
from typing import List, Optional

# from . import Controller
# from tp_node.ring_bus import Controller, CommunicationError
from . import Controller  # , CommunicationError

log = print  # TODO

RESPONSE_TIMEOUT = .05


class UnknownDestination(Exception):
    pass


@dataclass
class Node:
    address: int
    name: str
    uuid: str


class SoftwareController(Controller):
    def __init__(self, port):
        super().__init__(port)

        # NOTE doesn't make much sense to use queue here, since it can only be one at a time
        self._resp_queue = queue.Queue(maxsize=1)  # incoming responses
        self._cmd_queue = queue.Queue(maxsize=1)  # outgoing commands

        self.__running = True
        self.__nodes: List[Node] = []
        executor = concurrent.futures.ThreadPoolExecutor()
        self.__threads = [executor.submit(thread) for thread in [
            self.__manage_outgoing,
            self.__manage_incoming
        ]]
        # init nodes
        for cmd in ['\n', '0>$closestream', '0>node.reset']:
            self._send_cmd(cmd, expect_response=False)
        self.__threads.append(executor.submit(self.__manage_bus))

    def __manage_incoming(self):
        while self.__running:
        # while True:  # terminiert, durch Exception, sobald Port geschlossen ist
            try:
                line = self._ser.readline() \
                    .decode('ascii') \
                    .strip()
            except UnicodeDecodeError:
                log("Warning: Decode Stream error")
                continue
            if not line:
                continue

            if line.startswith('//'):  # ignore debug msg
                continue
            self._resp_queue.put(line)  #, block=False)
            # data_type, data = line[0], line[1:]
            # if data_type=='#':    # code response
            #   resp_queue.put(line, block=False) #TODO differenciate between data and error response
            # if data_type=='*':    # data response
            #   resp_queue.put(line, block=False)
            # elif data_type=='$':  # event
            #   #print(line)
            #   event, *arguments = re.findall(r"(?:[^\s,']|'(?:\\.|[^'])*')+", data)
            #   event_queue.append((event, *arguments))

    def __manage_outgoing(self):
        while self.__running:
            try:
                # print('fu!!!')
                cmd = self._cmd_queue.get(block=True, timeout=.1)
                self._ser.write(cmd)
                # time.sleep(.5)
            except queue.Empty:  # nothing to send
                pass

    def __manage_bus(self):
        # def get_free_address():
        #     try
        # address_pool = [] # returned addresses, ready to reassign
        address_offset = 0
        while self.__running:
            address: int = address_offset + 1
            request = f"0>$setaddress {address}"
            response = self._send_cmd(request, expect_response=True, dont_log=True)
            # response = self.broadcast('$setaddress {address}', expect_response=True)
            if response is None:  # network down TODO
                pass
            elif response == request:  # message made entire trip without being picked up by any station
                pass
            elif response.startswith('#0'):
                # self.__devices[address] = {"uuid": 0x00}
                node = Node(address, '', '0x00')  # TODO UUID
                self.__nodes.append(node)
                try:
                    name = self.query(('address', address), 'node:config.name')
                    # self._send_cmd(f"{address}>node:config.name", expect_response=True, dont_log=True)
                    node.name = name.strip('\"\'')
                    log("node-discovered", node)
                    # event_queue.append(("device-discovered", address, '0x00'))
                    address_offset += 1
                except UnknownDestination:
                    self.__nodes = filter(lambda x: x.address != address, self.__nodes)

            # for address, device in self.__devices.items():
            #     #address = list(devices.keys())[ping_id]
            #     request = f"{address}>devices.poll_events"
            #     response = sendCmd(request, expect_response=True, dont_log=True)
            #     if response is not None:  # station still there?
            #         if response.startswith('#0'):
            #             pass  # no new events
            #         else:
            #             # response.split(',')
            #             log(f"Event from {address}: {response}")
            #     else:
            #         event_queue.append(("device-lost", address, '0x00'))
            time.sleep(.01)

    def disconnect(self):
        super().disconnect()
        self.__running = False
        # is there no way to clear a queue?
        for queue in [self._cmd_queue, self._resp_queue]:
            try:
                queue.get(timeout=.01)
            except Empty:
                pass
        # self._cmd_queue = queue.Queue(maxsize=1)  # outgoing commands
        for thread in self.__threads:
            try:
                thread.result()  # re-raise exception if thread crashed
            except SerialException:
                pass

    def _send_cmd(self, cmd, expect_response, dont_log=False) -> Optional[str]:
        self._cmd_queue.put(str.encode(cmd + '\n'), timeout=1)  # , block=False)
        log_entry = f">> sending '{cmd}'"
        log_entry += " -> "
        response = None
        try:
            if expect_response:
                response = self._resp_queue.get(timeout=RESPONSE_TIMEOUT)
                log_entry += response
        except queue.Empty:
            log_entry += "[no response!]"
        finally:
            # if not dont_log: log(log_entry)
            return response

    def broadcast(self, cmd, expect_response=False):
        return self._send_cmd(f"0>{cmd}", expect_response)

    def query(self, target: tuple[str, object], cmd, expect_response=True) -> Optional[str]:
        target_type, target = target
        match target_type:
            case 'address':
                node = next(filter(lambda x: x.address == target, self.__nodes), None)
            case 'name':
                node = next(filter(lambda x: x.name == target, self.__nodes), None)
            case 'uuid':
                node = next(filter(lambda x: x.uuid == target, self.__nodes), None)
            case _:
                raise ValueError()
        if node is None:
            raise UnknownDestination()
        address = node.address
        query = f"{address}>{cmd}"
        response = self._send_cmd(query, expect_response)
        if cmd == query:
            raise Exception('connection to node lost')  # FIXME handle better
        return response

    # def query(self, cmd, response='uniline', timeout=.1):
    #     self._ser.timeout = timeout
    #     self._ser.write(str.encode(f'{cmd}\n'))
    #     resp = ''
    #     while True:
    #         line = self._ser.readline().decode('ascii')
    #         if not line:
    #             break
    #         resp += line
    #     if not resp:
    #         #if response == 'silent':
    #         #    return
    #         raise CommunicationError(f"No response from node on command <{cmd}>")
    #     # print(f'{cmd} -> {resp}')
    #     parsed = parse('#{:d} {}', resp)
    #     if parsed and parsed[0] != 0:
    #         raise CommunicationError(f"Error response <{resp.strip()}> from node on command <{cmd}>")
    #     return resp.strip()
    #     # .rstrip().lstrip() #FIXME lstrip on config seem to be nessesarry due to firmware bug
