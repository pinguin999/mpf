import serial


class CommunicationError(Exception):
    pass


class Controller:  # (ABC):
    def __init__(self, port: str, baud_rate=38400):
        self._ser = serial.Serial(port, baud_rate)  # timeout=.1
        self.connected = True

    # @abc.abstractmethod
    def connect(self): pass

    # @abc.abstractmethod
    def disconnect(self):
        self._ser.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.disconnect()
