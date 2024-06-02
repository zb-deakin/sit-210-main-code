import socket
from time import sleep
import serial
from Data import Command


class SerialLightSensorListener:
    # track trigger boundaries for closing the blind
    __tooBright: float = 700
    __tooDark: float = 100

    # USB serial connection
    __serialDevice: serial.Serial = None

    # network connection for talking to MotorListener
    __port = 5000
    __host: str = None

    def __init__(
            self,
            _closeBlindWhenBrighterThan=700,
            _closeBlindWhenDarkerThan=100,
            _usbDevicePort: str = '/dev/ttyACM0',
            _baud: int = 9600, _timeout: int = 1
    ):
        # track trigger boundaries for closing the blind
        self.__tooBright = _closeBlindWhenBrighterThan
        self.__tooDark = _closeBlindWhenDarkerThan

        # receive serial light sensor data from arduino via USB
        self.__serialDevice: serial.Serial = serial.Serial(_usbDevicePort, _baud, timeout=_timeout)
        self.__serialDevice.reset_input_buffer()

        # prepare network connection
        self.__host = socket.gethostname()
        self.__connection = socket.socket()
        self.__connection.connect((self.__host, self.__port))

    def run(self):
        # track the latest state of the blind
        tooDark_blindIsClosed = False
        tooBright_blindIsClosed = False

        try:
            while True:
                # wait between readings
                sleep(1)

                # some data is being received
                if self.__serialDevice.in_waiting > 0:
                    try:
                        # read serial data and check that it's usable
                        lightReading = self.__serialDevice.readline().decode('utf-8').rstrip()
                        self.__serialDevice.reset_input_buffer()
                        print(f'> Raw {lightReading=}')
                        lightReading = float(lightReading)
                    except Exception as error:
                        # data was not usable, ump to next loop
                        print(f'<<<< Light reading error: {error=} >>>>')
                        continue

                    # figure out what state the blind should be in now
                    blindShouldBeOpen = self.__tooDark < lightReading < self.__tooBright

                    # figure out the current state of the blind
                    blindIsClosed = tooDark_blindIsClosed or tooBright_blindIsClosed

                    # standard amount of daylight - open the blinds
                    if blindShouldBeOpen and blindIsClosed:
                        print("> Open blind in normal light range")
                        # send message to motor listener over network
                        self.__sendInstructionsToMotorListener(Command.Up.value)
                        tooDark_blindIsClosed = False
                        tooBright_blindIsClosed = False
                        continue

                    # nighttime - close the blinds
                    if lightReading < self.__tooDark and not tooDark_blindIsClosed:
                        print("> Close blind - too dark")
                        self.__sendInstructionsToMotorListener(Command.Down.value)
                        tooDark_blindIsClosed = True
                        continue

                    # too bright - close the blinds
                    if lightReading > self.__tooBright and not tooBright_blindIsClosed:
                        print("> Close blind - too bright")
                        self.__sendInstructionsToMotorListener(Command.Down.value)
                        tooBright_blindIsClosed = True
                        continue

        except Exception as error:
            print()
            print(f'SERIAL ERROR: {error=}')
            print('<<< ENDING SERIAL READING >>>')
            print()

    def __sendInstructionsToMotorListener(self, message: str):
        print(f"LIGHT SENSOR SENDING MESSAGE: '{message}'")

        # create a new connection when needed because the motor listener
        # closes connections after instructions are received
        try:
            self.__connection = socket.socket()
            self.__connection.connect((self.__host, self.__port))
        except Exception as error:
            print(f'Socket was already open {error=}')

        # send new instruction to motor listener over local network
        self.__connection.sendall(message.encode())

        # take note of the response received
        data = self.__connection.recv(1024).decode()
        print(f'LIGHT SENSOR: Response from MotorListener: "{data}"')
        self.__connection.close()


if __name__ == "__main__":
    listener = SerialLightSensorListener()
    listener.run()
