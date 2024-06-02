from typing import Callable
import pigpio
import irreceiver
import socket

"""
!!! PiPulseCollector IS NOT MY CODE, IT IS FROM:
!!! https://github.com/computersarecool/irreceiver
"""


class PiPulseCollector:
    """
    This class collects the timing between IR pulses
    """

    def __init__(
            self,
            pi: pigpio.pi,
            receive_pin: int,
            done_callback: Callable,
            max_time: int,
            decoder: irreceiver.NecDecoder,
    ):
        self.pi = pi
        self.receive_pin = receive_pin
        self.done_callback = done_callback
        self.max_time = max_time
        self.decoder = decoder

        self.t1 = None
        self.t2 = None
        self.pulse_times = []
        self.collecting = False

    def collect_pulses(self, _, level: int, tick: int):
        """
        This function adds a pulse to self.pulse_times
        Once the allowed time has elapsed the decode callback is called and then (if valid) the done_callback

        Args:
            _: (unused) The pin number is automatically passed by the pigpio callback
            level: pigpo denotes a falling edge with 0, a rising edge with 1 and a timeout by pigpo.TIMEOUT
            tick: The number of microseconds between boot and this event
        """

        if level != pigpio.TIMEOUT:
            if not self.collecting:
                self.pulse_times = []
                self.collecting = True
                self.pi.set_watchdog(self.receive_pin, self.max_time)
                self.t1 = None
                self.t2 = tick

            else:
                self.t1 = self.t2
                self.t2 = tick

                if self.t1 is not None:
                    pulse_time = pigpio.tickDiff(self.t1, self.t2)
                    self.pulse_times.append(pulse_time)

        # Receive time is done
        else:
            if self.collecting:
                self.collecting = False
                self.pi.set_watchdog(self.receive_pin, 0)
                self.done_callback(self.decoder.decode(self.pulse_times))


class InfraRedListener:
    """
    THIS IS MY OWN CODE
    """

    # button codes received via IR (transformed from hex to int)
    __arduinoRemoteIdentifier = 210
    __upButtonCode = 50
    __stopButtonCode = 40
    __downButtonCode = 30
    __buttons = {
        __upButtonCode: "up",
        __stopButtonCode: "stop",
        __downButtonCode: "down",
    }

    # network connection for talking to MotorListener
    __host: str = None
    __port = 5000
    __connection: socket.socket = None

    def __init__(self):
        # prepare network connection
        self.__host = socket.gethostname()
        self.__connection = socket.socket()
        self.__connection.connect((self.__host, self.__port))

        # setup board
        ir_pin = 17
        pi = pigpio.pi()
        pi.set_mode(ir_pin, pigpio.INPUT)

        # setup decoding of received IR signal
        decoder = irreceiver.NecDecoder()
        collector: PiPulseCollector = PiPulseCollector(
            pi,
            ir_pin,
            self.handleNewCommandCallback,  # callback to run when new command received
            irreceiver.FRAME_TIME_MS + irreceiver.TIMING_TOLERANCE,
            decoder,
        )
        _ = pi.callback(ir_pin, pigpio.EITHER_EDGE, collector.collect_pulses)

    @staticmethod
    def __decodeIrHex(integer):
        return divmod(integer, 0x100)

    # send instruction to motor listener
    def __sendToMotorListener(self, message: str):
        print("Send message")

        # create a new connection when needed because the motor listener
        # closes connections after instructions are received
        try:
            self.__connection = socket.socket()
            self.__connection.connect((self.__host, self.__port))
        except Exception as error:
            print(f'Socket was already open {error=}')

        # send new instruction to motor listener over local network
        self.__connection.send(message.encode())
        data = self.__connection.recv(1024).decode()
        print(f'Response from MotorListenerL: "{data}"')
        self.__connection.close()

    def handleNewCommandCallback(self, code: int):
        # nothing to do
        if code is None:
            print("IR ERROR: No code")
            return

        # invalid IR data received - do nothing
        if code == irreceiver.INVALID_FRAME:
            print(f"IR ERROR: Invalid code '{code}'")
            return

        # decode IR message
        remoteIdentifier, buttonPressed = self.__decodeIrHex(code)
        print(f"DECODED IR: id '{remoteIdentifier}' button '{buttonPressed}")

        # received an errant IR pulse from some other remote control
        if remoteIdentifier != self.__arduinoRemoteIdentifier:
            print(f'ERROR: received errant IR signal from sender "{remoteIdentifier}"')
            print("=== STOP HERE ===")
            print()
            return

        _commandToSend = ""

        # try to turn code into a usable command
        try:
            _commandToSend = self.__buttons[buttonPressed]
            print(f'IR SUCCESS: Identified command to send "{_commandToSend}"')
            print()
        except KeyError:
            print(f'ERROR: Invalid button received from IR "{buttonPressed}"')
            print("=== STOP HERE ===")
            print()
            return

        # send message to motor listener over network
        print(">>>> CONTACTING MOTOR LISTENER <<<<")
        self.__sendToMotorListener(_commandToSend)
        print("Command sent. Finishing callback....")
        print()

    def cleanup(self):
        print("IR CLEANUP: Close connection")
        self.__connection.close()


if __name__ == "__main__":
    irListener = InfraRedListener()
    try:
        while True:
            pass
    except Exception as error:
        irListener.cleanup()

        print()
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print("====== FINISHED COLLECTING IR PULSES =======")
        print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
        print(f'{error=}')
        print()
