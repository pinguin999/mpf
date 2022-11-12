"""Fast serial communicator."""
import asyncio
from packaging import version
from serial import SerialException, EIGHTBITS, PARITY_NONE, STOPBITS_ONE
from typing import Optional
from mpf.platforms.fast import fast_defines

from mpf.core.utility_functions import Util

# Minimum firmware versions needed for this module
from mpf.platforms.fast.fast_io_board import FastIoBoard

# The following minimum firmware versions are to prevent breaking changes
# in MPF from running on boards that have not been updated.
DMD_MIN_FW = version.parse('0.88')         # Minimum FW for a DMD
NET_MIN_FW = version.parse('2.0')          # Minimum FW for a V2 controller
NET_LEGACY_MIN_FW = version.parse('0.88')  # Minimum FW for a V1 controller
RGB_MIN_FW = version.parse('2.0')          # Minimum FW for an RGB LED controller
RGB_LEGACY_MIN_FW = version.parse('0.87')
IO_MIN_FW = version.parse('1.09')          # Minimum FW for an IO board linked to a V2 controller
IO_LEGACY_MIN_FW = version.parse('0.87')   # Minimum FW for an IO board linked to a V1 controller

LEGACY_ID = 'FP-CPU-0'      # Start of an id for V1 controller
RETRO_ID = 'FP-SBI'         # Start of an id for a Retro controller
V2_FW = '1.80'              # Firmware cutoff from V1 to V2 controllers

MYPY = False
if MYPY:   # pragma: no cover
    from mpf.core.machine import MachineController  # pylint: disable-msg=cyclic-import,unused-import

HEX_FORMAT = " 0x%02x"

class FastSerialConnector:
    """Connects to a serial port and determines which FAST board is on the other end."""

    __slots__ = ["platform", "port", "baud", "xonxoff", "machine", "log", "debug", "is_retro", "is_legacy", "reader",
                 "writer", "remote_model", "remote_firmware", "remote_processor"]

    def __init__(self, platform, port, baud):

        self.platform = platform
        self.port = port
        self.baud = baud
        self.xonxoff = False
        self.machine = platform.machine
        self.log = platform.log
        self.debug = platform.debug
        self.is_retro = False  # FAST Retro Controller (System 11, WPC-89, WPC-95)
        self.is_legacy = False  # FAST NET v1 (Nano)

    def __repr__(self):
        return f'<FastSerialConnector: {self.port}>'

    async def connect(self):
        """Connect to the serial port."""
        self.log.info("Connecting to %s at %sbps", self.port, self.baud)
        while True:
            try:
                connector = self.machine.clock.open_serial_connection(
                    url=self.port, baudrate=self.baud, limit=0, xonxoff=False,
                    bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE)
                self.reader, self.writer = await connector
            except SerialException:
                if not self.machine.options["production"]:
                    raise

                # if we are in production mode retry
                await asyncio.sleep(.1)
                self.log.debug("Connection to %s failed. Will retry.", self.port)
            else:
                # we got a connection
                break

        serial = self.writer.transport.serial
        if hasattr(serial, "set_low_latency_mode"):
            try:
                serial.set_low_latency_mode(True)
            except (NotImplementedError, ValueError) as e:
                self.log.info("Could not set %s to low latency mode: %s", self.port, e)

        # defaults are slightly high for our use case
        self.writer.transport.set_write_buffer_limits(2048, 1024)

        # read everything which is sitting in the serial
        self.writer.transport.serial.reset_input_buffer()
        # clear buffer
        # pylint: disable-msg=protected-access
        self.reader._buffer = bytearray()

        msg = ''

        # send enough dummy commands to clear out any buffers on the FAST
        # board that might be waiting for more commands
        self.writer.write(((' ' * 256 * 4) + '\r').encode())

        while True:
            self.platform.debug_log(f"Sending 'ID:' command to {self.port}")
            self.writer.write('ID:\r'.encode())
            msg = await self._read_with_timeout(.5)

            # ignore XX replies here.
            while msg.startswith('XX:'):
                msg = await self._read_with_timeout(.5)

            if msg.startswith('ID:'):
                break

            await asyncio.sleep(.5)

        try:
            self.remote_processor, self.remote_model, self.remote_firmware = msg[3:].split()
        except ValueError:
            # Some boards (e.g. FP-CPU-2000) do not include a processor type, default to NET
            self.remote_model, self.remote_firmware = msg[3:].split()
            self.remote_processor = 'NET'

        if self.remote_model.startswith(RETRO_ID):
            self.is_retro = True
        elif self.platform.machine_type not in fast_defines.HARDWARE_KEY:
            self.is_legacy = True

        self.platform.log.info("Connected! Processor: %s, "
                               "Board Type: %s, Firmware: %s",
                               self.remote_processor, self.remote_model,
                               self.remote_firmware)

        # Transfer connection over to serial communicator

        if self.remote_processor == 'SEG':
            self.is_legacy = False
            from mpf.platforms.fast.communicators.seg import FastSegCommunicator
            return FastSegCommunicator(self.platform, self.remote_processor,
                                      self.remote_model, self.remote_firmware,
                                      self.is_legacy, self.is_retro,
                                      self.reader, self.writer)
        elif self.remote_processor in ['EXP', 'LED']:
            self.is_legacy = False
            from mpf.platforms.fast.communicators.exp import FastExpCommunicator
            return FastExpCommunicator(self.platform, self.reader, self.writer)
        else:
            return FastSerialCommunicator(self.platform, self.remote_processor,
                                        self.remote_model, self.remote_firmware,
                                        self.is_legacy, self.is_retro,
                                        self.reader, self.writer)

    async def _read_with_timeout(self, timeout):
        try:
            msg_raw = await asyncio.wait_for(self.readuntil(b'\r'), timeout=timeout)
        except asyncio.TimeoutError:
            return ""
        return msg_raw.decode()

    # pylint: disable-msg=inconsistent-return-statements
    async def readuntil(self, separator, min_chars: int = 0):
        """Read until separator.

        Args:
        ----
            separator: Read until this separator byte.
            min_chars: Minimum message length before separator
        """
        assert self.reader is not None
        # asyncio StreamReader only supports this from python 3.5.2 on
        buffer = b''
        while True:
            char = await self.reader.readexactly(1)
            buffer += char
            if char == separator and len(buffer) > min_chars:
                if self.debug:
                    self.log.debug("%s received: %s (%s)", self, buffer, "".join(HEX_FORMAT % b for b in buffer))
                return buffer

# pylint: disable-msg=too-many-instance-attributes
class FastSerialCommunicator:

    """Handles the serial communication to the FAST platform."""

    ignored_messages = ['RX:P',  # RGB Pass
                        'SN:P',  # Network Switch pass
                        'SL:P',  # Local Switch pass
                        'LX:P',  # Lamp pass
                        'PX:P',  # Segment pass
                        'DN:P',  # Network driver pass
                        'DL:P',  # Local driver pass
                        'XX:F',  # Unrecognized command?
                        'R1:F',
                        'L1:P',
                        'GI:P',
                        'TL:P',
                        'TN:P',
                        'XO:P',  # Servo/Daughterboard Pass
                        'XX:U',
                        'XX:N'
                        ]

    __slots__ = ["dmd", "remote_processor", "remote_model", "remote_firmware", "max_messages_in_flight",
                 "messages_in_flight", "ignored_messages_in_flight", "send_ready", "write_task", "received_msg",
                 "send_queue", "is_retro", "is_legacy", "machine", "platform", "log", "debug", "read_task",
                 "reader", "writer"]

    def __init__(self, platform, remote_processor, remote_model, remote_firmware,
                 is_legacy, is_retro, reader, writer):
        """Initialize communicator.

        Args:
        ----
            platform(mpf.platforms.fast.fast.HardwarePlatform): the fast hardware platform
            port: serial port
            baud: baud rate
        """
        self.dmd = False
        self.platform = platform
        self.remote_processor = remote_processor
        self.remote_model = remote_model
        self.remote_firmware = remote_firmware
        self.is_retro = is_retro
        self.is_legacy = is_legacy
        self.max_messages_in_flight = 10
        self.messages_in_flight = 0
        self.ignored_messages_in_flight = {b'-N', b'/N', b'/L', b'-L'}

        self.send_ready = asyncio.Event()
        self.send_ready.set()
        self.write_task = None

        self.received_msg = b''

        self.send_queue = asyncio.Queue()

        self.machine = platform.machine     # type: MachineController

        self.log = self.platform.log
        self.debug = self.platform.config['debug']


        self.reader = reader      # type: Optional[asyncio.StreamReader]
        self.writer = writer      # type: Optional[asyncio.StreamWriter]
        self.read_task = None

    async def init(self):

        self.machine.variables.set_machine_var("fast_{}_firmware".format(self.remote_processor.lower()),
                                               self.remote_firmware)
        '''machine_var: fast_(x)_firmware

        desc: Holds the version number of the firmware for the processor on
        the FAST Pinball controller that's connected. The "x" is replaced with
        either "dmd", "net", or "rgb", one for each processor that's attached.
        '''

        self.machine.variables.set_machine_var("fast_{}_model".format(self.remote_processor.lower()), self.remote_model)

        '''machine_var: fast_(x)_model

        desc: Holds the model number of the board for the processor on
        the FAST Pinball controller that's connected. The "x" is replaced with
        either "dmd", "net", or "rgb", one for each processor that's attached.
        '''

        if self.remote_processor == 'DMD':
            min_version = DMD_MIN_FW
            # latest_version = DMD_LATEST_FW
            self.dmd = True
            self.max_messages_in_flight = self.platform.config['dmd_buffer']
            self.platform.debug_log("Setting DMD buffer size: %s",
                                    self.max_messages_in_flight)
        elif self.remote_processor == 'NET':
            min_version = NET_LEGACY_MIN_FW if self.remote_model.startswith(LEGACY_ID) else NET_MIN_FW
            # latest_version = NET_LATEST_FW
            self.max_messages_in_flight = self.platform.config['net_buffer']
            self.platform.debug_log("Setting NET buffer size: %s",
                                    self.max_messages_in_flight)
        elif self.remote_processor == 'RGB':
            min_version = RGB_LEGACY_MIN_FW if self.remote_model.startswith(LEGACY_ID) else RGB_MIN_FW
            # latest_version = RGB_LATEST_FW
            self.max_messages_in_flight = self.platform.config['rgb_buffer']
            self.platform.debug_log("Setting RGB buffer size: %s",
                                    self.max_messages_in_flight)
        else:
            raise AttributeError(f"Unrecognized FAST processor type: {self.remote_processor}")

        if version.parse(self.remote_firmware) < min_version:
            raise AssertionError(f'Firmware version mismatch. MPF requires the {self.remote_processor} processor '
                                 f'to be firmware {min_version}, but yours is {self.remote_firmware}')

        # Register the connection so when we query the boards we know what responses to expect
        self.platform.register_processor_connection(self.remote_processor, self)

        if self.remote_processor == 'NET':
            await self.query_fast_io_boards()

        self.write_task = self.machine.clock.loop.create_task(self._socket_writer())
        self.write_task.add_done_callback(Util.raise_exceptions)

        return self

    # Duplicated from FastSerialConnector for now
    # pylint: disable-msg=inconsistent-return-statements
    async def readuntil(self, separator, min_chars: int = 0):
        """Read until separator.

        Args:
        ----
            separator: Read until this separator byte.
            min_chars: Minimum message length before separator
        """
        assert self.reader is not None
        # asyncio StreamReader only supports this from python 3.5.2 on
        buffer = b''
        while True:
            char = await self.reader.readexactly(1)
            buffer += char
            if char == separator and len(buffer) > min_chars:
                if self.debug:
                    self.log.debug("%s received: %s (%s)", self, buffer, "".join(HEX_FORMAT % b for b in buffer))
                return buffer

    def stop(self):
        """Stop and shut down this serial connection."""
        if self.write_task:
            self.write_task.cancel()
            self.write_task = None
        self.log.error("Stop called on serial connection %s", self.remote_processor)
        if self.read_task:
            self.read_task.cancel()
            self.read_task = None
        if self.writer:
            self.writer.close()
            if hasattr(self.writer, "wait_closed"):
                # Python 3.7+ only
                self.machine.clock.loop.run_until_complete(self.writer.wait_closed())
            self.writer = None

    async def reset_net_cpu(self):
        """Reset the NET CPU."""
        self.platform.debug_log('Resetting NET CPU.')
        self.writer.write('BR:\r'.encode())
        msg = ''
        while msg != 'BR:P\r' and not msg.endswith('!B:02\r'):
            msg = (await self.readuntil(b'\r')).decode()
            self.platform.debug_log("Got: %s", msg)

    async def configure_hardware(self):
        """Verify Retro board type."""
        # For Retro boards, send the CPU configuration
        hardware_key = fast_defines.HARDWARE_KEY[self.platform.machine_type]
        self.platform.debug_log("Writing FAST hardware key %s from machine type %s",
                                hardware_key, self.platform.machine_type)
        self.writer.write(f'CH:{hardware_key},FF\r'.encode())

        msg = ''
        while msg != 'CH:P\r':
            msg = (await self.readuntil(b'\r')).decode()
            if msg == '\x00CH:P\r':  # workaround as the -5 Neurons send a null byte after the final boot message
                msg = 'CH:P\r'
            self.platform.debug_log("Got: %s", msg)

    async def query_fast_io_boards(self):
        """Query the NET processor to see if any FAST IO boards are connected.

        If so, queries the IO boards to log them and make sure they're the  proper firmware version.
        """
        # reset CPU early
        try:
            # Wait a moment for any previous message cache to clear
            await asyncio.sleep(.2)
            await asyncio.wait_for(self.reset_net_cpu(), 10)
        except asyncio.TimeoutError:
            self.platform.warning_log("Reset of NET CPU failed.")
        else:
            self.platform.debug_log("Reset successful")

        if not self.is_legacy:
            await asyncio.sleep(.2)
            try:
                await asyncio.wait_for(self.configure_hardware(), 15)
            except asyncio.TimeoutError:
                self.platform.warning_log("Configuring FAST hardware timed out.")
            else:
                self.platform.debug_log("FAST hardware configuration accepted.")

        await asyncio.sleep(.5)

        self.platform.debug_log('Reading all switches.')
        self.writer.write('SA:\r'.encode())
        msg = ''
        while not msg.startswith('SA:'):
            msg = (await self.readuntil(b'\r')).decode()
            if not msg.startswith('SA:'):
                self.platform.log.warning("Got unexpected message from FAST while awaiting SA: %s", msg)

        self.platform.process_received_message(msg, "NET")
        self.platform.debug_log('Querying FAST IO boards (legacy %s, retro %s)...', self.is_legacy, self.is_retro)

        firmware_ok = True

        if self.is_retro:
            # TODO: [Retro] Move the config defines to the Retro's firmware and retrieve via serial query
            # In the meantime, hard-code values large enough to account for the biggest machines
            node_id, drivers, switches = ['00', '40', '80']  # in HEX, aka DEC values 0, 64, 128
            self.platform.register_io_board(FastIoBoard(
                int(node_id, 16),
                self.remote_model,
                self.remote_firmware,
                int(switches, 16),
                int(drivers, 16))
            )

            self.platform.debug_log('Fast Retro Board %s: Model: %s, Firmware: %s, Switches: %s, Drivers: %s',
                                    node_id, self.remote_model, self.remote_firmware,
                                    int(switches, 16), int(drivers, 16))

            return

        for board_id in range(128):
            self.writer.write('NN:{:02X}\r'.format(board_id).encode())
            msg = ''
            while not msg.startswith('NN:'):
                msg = (await self.readuntil(b'\r')).decode()
                if not msg.startswith('NN:'):
                    self.platform.debug_log("Got unexpected message from FAST while querying IO Boards: %s", msg)

            if msg == 'NN:F\r':
                break

            node_id, model, fw, dr, sw, _, _, _, _, _, _ = msg.split(',')
            node_id = node_id[3:]

            model = model.strip('\x00')

            # Iterate as many boards as possible
            if not model or model == '!Node Not Found!':
                break

            self.platform.register_io_board(FastIoBoard(int(node_id, 16), model, fw, int(sw, 16), int(dr, 16)))

            self.platform.debug_log('Fast IO Board %s: Model: %s, Firmware: %s, Switches: %s, Drivers: %s',
                                    node_id, model, fw, int(sw, 16), int(dr, 16))

            min_fw = IO_LEGACY_MIN_FW if self.is_legacy else IO_MIN_FW
            if min_fw > version.parse(fw):
                self.platform.log.critical("Firmware version mismatch. MPF requires the IO boards "
                                           "to be firmware %s, but your Board %s (%s) is firmware %s",
                                           min_fw, node_id, model, fw)
                firmware_ok = False

        if not firmware_ok:
            raise AssertionError("Exiting due to IO board firmware mismatch")

    def send(self, msg):
        """Send a message to the remote processor over the serial connection.

        Args:
        ----
            msg: String of the message you want to send. THe <CR> character will
                be added automatically.

        """
        self.send_queue.put_nowait(msg)

    def _send(self, msg):
        debug = self.platform.config['debug']
        if self.dmd:
            self.writer.write(b'BM:' + msg)
            # Don't log W(atchdog), they are noisy
            if debug and msg[0] != "W":
                self.platform.log.debug("Send: %s", "".join(" 0x%02x" % b for b in msg))

        elif not self.max_messages_in_flight:  # For processors that don't use this
            self.writer.write(msg.encode() + b'\r')
            self.platform.log.debug("Sending without message flight tracking: %s", msg)
        else:
            self.messages_in_flight += 1
            if self.messages_in_flight > self.max_messages_in_flight:
                self.send_ready.clear()

                self.log.debug("Enabling Flow Control for %s connection. "
                               "Messages in flight: %s, Max setting: %s",
                               self.remote_processor,
                               self.messages_in_flight,
                               self.max_messages_in_flight)

            self.writer.write(msg.encode() + b'\r')
            # Don't log W(atchdog) or L(ight) messages, they are noisy
            if debug and msg[0] != "W" and msg[0] != "L":
                self.platform.log.debug("Send: %s", msg)

    async def _socket_writer(self):
        while True:
            msg = await self.send_queue.get()
            try:
                await asyncio.wait_for(self.send_ready.wait(), 1.0)
            except asyncio.TimeoutError:
                self.log.warning("Port %s was blocked for more than 1s. Resetting send queue! If this happens "
                                 "frequently report a bug!", self.port)
                self.messages_in_flight = 0
                self.send_ready.set()

            self._send(msg)

    def __repr__(self):
        """Return str representation."""
        return f"{self.remote_processor} Communicator"

    def _parse_msg(self, msg):
        self.received_msg += msg

        while True:
            pos = self.received_msg.find(b'\r')

            # no more complete messages
            if pos == -1:
                break

            msg = self.received_msg[:pos]
            self.received_msg = self.received_msg[pos + 1:]

            if msg[:2] not in self.ignored_messages_in_flight:

                self.messages_in_flight -= 1
                if self.messages_in_flight <= self.max_messages_in_flight or not self.read_task:
                    self.send_ready.set()
                if self.messages_in_flight < 0:
                    self.log.warning("Port %s received more messages than "
                                     "were sent! Resetting!",
                                     self.remote_processor)
                    self.messages_in_flight = 0

            if not msg:
                continue

            if msg.decode() not in self.ignored_messages:
                self.platform.process_received_message(msg.decode(), self.remote_processor)

    async def read(self, n=-1):
        """Read up to `n` bytes from the stream and log the result if debug is true.

        See :func:`StreamReader.read` for details about read and the `n` parameter.
        """
        try:
            resp = await self.reader.read(n)
        except asyncio.CancelledError:  # pylint: disable-msg=try-except-raise
            raise
        except Exception as e:  # pylint: disable-msg=broad-except
            self.log.warning("Serial error: {}".format(e))
            return None

        # we either got empty response (-> socket closed) or and error
        if not resp:
            self.log.warning("Serial closed.")
            self.machine.stop("Serial {} closed.".format(self.port))
            return None

        if self.debug:
            self.log.debug("%s received: %s (%s)", self, resp, "".join(HEX_FORMAT % b for b in resp))
        return resp

    async def start_read_loop(self):
        """Start the read loop."""
        self.read_task = self.machine.clock.loop.create_task(self._socket_reader())
        self.read_task.add_done_callback(Util.raise_exceptions)

    async def _socket_reader(self):
        while True:
            resp = await self.read(128)
            if resp is None:
                return
            self._parse_msg(resp)
