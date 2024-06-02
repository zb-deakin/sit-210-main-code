# Based on: https://RandomNerdTutorials.com/raspberry-pi-dht11-dht22-python/
# Based on Adafruit_CircuitPython_DHT Library Example

import socket
from time import sleep
import board
import adafruit_dht


class TemperatureHumidity:
    # track trigger boundaries for closing the blind
    __closeBlindAtTemperature: float = None
    __closeBlindAtHumidity: float = None

    # send specific instruction heights to Motor (as opposed to just up/down)
    __up: str = "20"
    __down: str = "180"
    __lastInstruction: str = ""

    # get readings from temp/humidity module
    __DHT11 = None
    __degreesCelsius: float = 0
    __humidityPercentage: float = 0

    # network connection for talking to MotorListener
    __host: str = None
    __port = 5000

    def __init__(self, _closeBlindAtTemperature: float = 25, _closeBlindAtHumidity: float = 80):
        # setup board sensor
        self.__DHT11 = adafruit_dht.DHT11(board.D16)

        # save trigger boundaries
        self.__closeBlindAtTemperature = _closeBlindAtTemperature
        self.__closeBlindAtHumidity = _closeBlindAtHumidity

        # prepare network connection
        self.__host = socket.gethostname()
        self.__connection = socket.socket()
        self.__connection.connect((self.__host, self.__port))

    def run(self):
        """
        Main loop that triggers readings and processing of instructions for MotorListener
        """
        while True:
            # wait between readings
            sleep(1)

            # track previous readings before getting new readings
            previousDegreesCelsius = self.__degreesCelsius
            previousHumidityPercentage = self.__humidityPercentage

            # check for new readings
            self.__readSensorValues()

            # figure out if something has changed
            noChange = (
                    previousDegreesCelsius == self.__degreesCelsius and
                    previousHumidityPercentage == self.__humidityPercentage
            )

            # nothing changed, do nothing
            if noChange:
                continue

            # something changed, handle this change
            self.__handleNewInstructions()

    def __readSensorValues(self):
        """
        Get temperature and humidity reading from the DHT11 sensor
        """
        try:
            degreesCelsius = self.__DHT11.temperature
            humidityPercentage = self.__DHT11.humidity
            degreesCelsius = int(degreesCelsius)
            humidityPercentage = int(humidityPercentage)
        except RuntimeError as _error:
            # DHT11 commonly has errors, ignore them here
            print(f'DHT Sensor error: {_error.args[0]}')
            return
        except Exception as _error:
            # for every other type of error, log it and try again
            print(f'GENERAL ERROR: {_error}')
            return

        # track new temperature values
        if degreesCelsius != self.__degreesCelsius:
            self.__degreesCelsius = degreesCelsius

        # track new humidity values
        if humidityPercentage != self.__humidityPercentage:
            self.__humidityPercentage = humidityPercentage

        print(f"NEW READINGS: {self.__readingsMessage()}")

    def __handleNewInstructions(self):
        """
        INSTRUCTIONS ARE GENERATED HERE
        """
        # figure out what state the blind should be in
        closeBlind = (
                self.__degreesCelsius > self.__closeBlindAtTemperature or
                self.__humidityPercentage > self.__closeBlindAtHumidity
        )

        # avoid sending the same instructions over and over again
        blindIsUp_shouldBeDown = closeBlind and self.__lastInstruction != self.__down
        blindIsDown_shouldBeUp = not closeBlind and self.__lastInstruction != self.__up

        # pull blind UP, because it's currently down
        if blindIsUp_shouldBeDown:
            self.__lastInstruction = self.__down
            print(f"Close blind: {self.__readingsMessage()}")
            self.__sendInstructionsToMotorListener(self.__lastInstruction)
            return

        # pull blind DOWN, because it's currently up
        if blindIsDown_shouldBeUp:
            self.__lastInstruction = self.__up
            print(f"OPEN blind: {self.__readingsMessage()}")
            self.__sendInstructionsToMotorListener(self.__lastInstruction)
            return

    def __sendInstructionsToMotorListener(self, message: str):
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

    def __readingsMessage(self) -> str:
        # use a common message for printing
        return f"temperature {self.__degreesCelsius}ºc, humidity {self.__humidityPercentage}%"


if __name__ == "__main__":
    listener = TemperatureHumidity()
    listener.run()
