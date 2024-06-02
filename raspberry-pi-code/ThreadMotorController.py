import threading
from copy import deepcopy
from time import sleep, time
from typing import Dict, TextIO
from timeit import default_timer as timer
from RPi import GPIO  # type: ignore

from Data import Command, Instruction

# use broadcom pin numbering
GPIO.setmode(GPIO.BCM)


class MotorLeds:
    def __init__(self):
        # setup io pins
        self.__greenPin = 5
        self.__redPin = 6
        self.__yellowPin = 13
        self.__pins = {
            Command.Up.name: self.__greenPin,
            Command.Stop.name: self.__redPin,
            Command.Down.name: self.__yellowPin
        }

        # begin by having LEDs in the red "stopped" state
        for _commandName, _pin in self.__pins.items():
            brightness = GPIO.HIGH if _commandName == Command.Stop.name else GPIO.LOW
            GPIO.setup(_pin, GPIO.OUT)
            GPIO.output(_pin, brightness)

    # update pin status
    def command(self, _command: Command):
        # identify LED to light
        pinForUpdate = self.__pins[_command.name]

        # turn off other LEDS
        for _commandName, _pin in self.__pins.items():
            if _commandName != _command.name:
                GPIO.output(_pin, GPIO.LOW)

        # light identified LED
        GPIO.output(pinForUpdate, GPIO.HIGH)

    def cleanup(self):
        # tidy up LEDs
        for _keyCommand, pin in self.__pins.items():
            GPIO.output(pin, GPIO.LOW)

        GPIO.cleanup()


class ThreadMotorController(threading.Thread):
    """
    Control the motor with this class running as background thread
    - send instructions to the motor via the `instruct()` method
    - caller can continue doing other work while this thread is running
      such as listening for network connections
    """

    # h bridge input-1 pin
    __bridgeInput1Pin = 26
    # h bridge input-2 pin
    __bridgeInput2Pin = 4
    # logical speed control pin
    __bridgePwmPin = 22

    # blind settings
    __blindExtensionLength: float = None
    __blindHeightInCm: float = None
    __blindSpeedInCmPerSecond: float = None

    # motor speeds
    __lowPowerForLoweringBlind: int = 90
    __highPowerForRaisingBlind: int = 100
    __stoppedNoPower: int = 0

    # pulse width modulation for motor speed control
    __pwm: GPIO.PWM = None
    __pwmFrequency = 50
    __presentDutyCycle: float = 0

    # h-bridge rotation direction setting
    __hBridgeRotateUpward = True

    # the current command that is running e.g. up/down/stop etc
    __instruction: Dict = None

    # allow this thread to be stopped as part of the cleanup
    __stop_event: threading.Event = None

    # save latest state to disk after motor runs
    __file: TextIO = None

    # light up LEDs with current motor status
    __leds: MotorLeds = None

    def __init__(
            self,
            _file: TextIO,
            _initialBlindExtensionLength: float = 0,
            _blindHeightInCm: float = 200,
            _blindSpeedInCmPerSecond: float = 8
    ):
        super().__init__()
        # setup file to write new states to
        self.__file = _file

        # handle stopping of threads
        self.__stop_event = threading.Event()

        # setup blind data
        self.__instruction = deepcopy(self.__getStopInstruction())
        self.__blindHeightInCm = _blindHeightInCm
        self.__blindSpeedInCmPerSecond = _blindSpeedInCmPerSecond

        # make it possible to pause this thread
        self.paused = True
        self.state = threading.Condition()

        # register what length the blind is extended to currently
        self.__blindExtensionLength = _initialBlindExtensionLength

        # enable pins for h-bridge
        GPIO.setup(self.__bridgeInput1Pin, GPIO.OUT)
        GPIO.setup(self.__bridgeInput2Pin, GPIO.OUT)
        GPIO.setup(self.__bridgePwmPin, GPIO.OUT)

        # prepare pwm for controlling of motor's speed
        self.__pwm: GPIO.PWM = GPIO.PWM(self.__bridgePwmPin, self.__pwmFrequency)
        self.__pwm.start(self.__presentDutyCycle)

        # initialise LED lights
        self.__leds: MotorLeds = MotorLeds()

    @staticmethod
    def __getStopInstruction():
        # simple helper for common instruction
        return {
            "value": Command.Stop.value,
            "timestamp": time()
        }

    def currentInstruction(self) -> str:
        # simple helper that caller can use for getting latest blind state
        return self.__instruction['value']

    def instruct(self, instruction) -> bool:
        """
        Caller uses this public method to send new instruction for the motor
        """
        print()
        print(".................... INSTRUCTION ......................")
        print(instruction)
        print(".................... INSTRUCTION ......................")
        print()

        self.__instruction = {
            "value": instruction,
            "timestamp": time()
        }

        return True

    def __setDirectionOfRotation(self, _upward: bool):
        """
        reverse the direction of the motor by inverting states of input pins
        """
        input1, input2 = (GPIO.HIGH, GPIO.LOW) if _upward else (GPIO.LOW, GPIO.HIGH)
        print(f'{input1=}')
        print(f'{input2=}')
        GPIO.output(self.__bridgePwmPin, False)
        GPIO.output(self.__bridgeInput1Pin, input1)
        GPIO.output(self.__bridgeInput2Pin, input2)
        GPIO.output(self.__bridgePwmPin, True)

    def __getDutyCycle(self, _upward: bool) -> float:
        """
        Rolling the blind up takes more power than rolling it down
        - send the correct duty cycle for the requested direction
        """
        return self.__highPowerForRaisingBlind if _upward else self.__lowPowerForLoweringBlind

    def __actOnNewInstruction(self) -> Instruction:
        """
        Motor is controlled here
        """

        # stop blind: nothing to do because motor was stopped above
        if self.__instruction["value"] == Command.Stop.value:
            self.__handleStopInstruction()

            print(")) stop - nothing to do")

            # send back with same blind length
            return Instruction(
                _shouldMoveUpward=False,
                _newRequestedLength=self.__blindExtensionLength
            )

        # begin pulling blind all the way UP
        if self.__instruction["value"] == Command.Up.value:
            print(")) DO UP")
            print(f'{self.__blindExtensionLength=}')

            # nothing to do, blind is already up, finish here
            if self.__blindExtensionLength <= 0:
                print(F"ERROR: BLIND IS ALREADY AT MINIMUM '{self.__blindExtensionLength}'")
                return Instruction(
                    # _totalTimeToRunMotorInSeconds=0,
                    _shouldMoveUpward=False,
                    _newRequestedLength=self.__blindExtensionLength
                )

            # DO retracting of blind to zero length from current length
            # prepare motor
            self.__setDirectionOfRotation(_upward=True)
            self.__presentDutyCycle = self.__getDutyCycle(_upward=True)
            print(f"{self.__presentDutyCycle=}")

            # get motor running, then change to correct duty cycle
            self.__pwm.start(100)
            sleep(0.25)
            self.__pwm.ChangeDutyCycle(self.__presentDutyCycle)

            # update status-light
            self.__leds.command(Command.Up)

            # return latest state
            print(")) running motor upward now")
            return Instruction(
                _shouldMoveUpward=True,
                _newRequestedLength=0
            )

        # begin pulling blind all the way DOWN
        if self.__instruction["value"] == Command.Down.value:
            print(")) DO DOWN")

            # nothing to do, blind is already down, finish here
            if self.__blindExtensionLength >= self.__blindHeightInCm:
                print(F"ERROR: BLIND IS ALREADY AT MAXIMUM '{self.__blindExtensionLength}'")
                return Instruction(
                    _shouldMoveUpward=False,
                    _newRequestedLength=self.__blindHeightInCm
                )

            # DO extending of blind to maximum length
            # prepare motor
            self.__setDirectionOfRotation(_upward=False)
            self.__presentDutyCycle = self.__getDutyCycle(_upward=False)
            print(f"{self.__presentDutyCycle=}")

            # get motor running, then change to correct duty cycle
            print(")) running motor downward now")
            self.__pwm.start(100)
            sleep(0.25)
            self.__pwm.ChangeDutyCycle(self.__presentDutyCycle)

            # update status-light
            self.__leds.command(Command.Down)

            # return latest state
            return Instruction(
                _shouldMoveUpward=False,
                _newRequestedLength=self.__blindHeightInCm
            )

        # open blind to a custom amount if valid number is received
        try:
            _newExtensionLength = float(self.__instruction["value"])
        except ValueError:
            print(f'ERROR: "{self.__instruction["value"]}" is not an valid number')
            return Instruction(
                _shouldMoveUpward=False,
                _newRequestedLength=self.__blindExtensionLength
            )

        # calculate how much to move the blind
        shouldMoveBlindUpward = _newExtensionLength < self.__blindExtensionLength
        difference = abs(self.__blindExtensionLength - _newExtensionLength)
        print(f'{shouldMoveBlindUpward=}')
        print(f'{difference=}')

        # prepare motor
        self.__setDirectionOfRotation(_upward=shouldMoveBlindUpward)
        self.__presentDutyCycle = self.__getDutyCycle(_upward=shouldMoveBlindUpward)

        # start rolling the blind in the required direction
        self.__pwm.ChangeDutyCycle(self.__presentDutyCycle)
        print(f"))NOTICE: running motor {shouldMoveBlindUpward=}")
        print(f"{self.__presentDutyCycle=}")

        # update status-light
        if shouldMoveBlindUpward:
            self.__leds.command(Command.Up)
        else:
            self.__leds.command(Command.Down)

        # return latest state
        return Instruction(
            _shouldMoveUpward=shouldMoveBlindUpward,
            _newRequestedLength=_newExtensionLength
        )

    def __calculateNewBlindPosition(self, loopCheckPointTime, shouldMoveUpward) -> float:
        """
        Calculate new length of blind after it has moved
        """
        amountBlindMoved = (timer() - loopCheckPointTime) * self.__blindSpeedInCmPerSecond

        updatedLength = (
            # when OPENING the blind, the extension length is getting shorter
            self.__blindExtensionLength - amountBlindMoved if shouldMoveUpward
            # when CLOSING blind, the extension length is getting longer
            else self.__blindExtensionLength + amountBlindMoved
        )

        return updatedLength

    def __writeNewLengthToDisk(self):
        """
        Overwrite file with the newest blind-length state
        """
        self.__file.seek(0)
        self.__file.write(str(self.__blindExtensionLength))
        self.__file.truncate()
        self.__file.flush()

    def __ensureValuesAreWithinConstraints(self, write: bool = False):
        """
        The Pi and the motor are not precise,
        i.e. correct for over/under runs of the blind
        """

        # correct for under-runs
        if self.__blindExtensionLength < 0:
            print("WARNING: UNDER-RUN")
            self.__blindExtensionLength = 0

            if write:
                self.__writeNewLengthToDisk()

        # correct for overrun of the blind
        if self.__blindExtensionLength > self.__blindHeightInCm:
            self.__blindExtensionLength = self.__blindHeightInCm
            print("WARNING: OVER-RUN")
            if write:
                self.__writeNewLengthToDisk()

    def __hasBlindHasFinishedRolling(self, _shouldMoveUpward: bool, _newRequestedLength: float):
        """
        Figure out if goal has been reached
        """
        if _shouldMoveUpward:
            return (
                    self.__blindExtensionLength <= _newRequestedLength or
                    self.__blindExtensionLength <= 0
            )
        else:
            return (
                    self.__blindExtensionLength >= _newRequestedLength or
                    self.__blindExtensionLength >= self.__blindHeightInCm
            )

    def __handleStopInstruction(self):
        """
        Helper for stopping the motor and doing all related tasks
        """
        self.__presentDutyCycle = self.__stoppedNoPower
        self.__pwm.ChangeDutyCycle(self.__presentDutyCycle)
        self.__leds.command(Command.Stop)

    def run(self):
        """
        MAIN
        - called when thread is started
        - handles new instructions in this thread
        """

        print(" $$$$$$$$ RUNNING THREADED $$$$$$$$")

        # get default instruction
        currentCommand = deepcopy(self.__instruction)

        # prepare tracker variables for use
        loopCheckPointTime = timer()
        shouldMoveUpward = False
        newRequestedLength = 0
        counterCheckpointTime = timer()

        # run in a loop until the thread is killed
        while not self.__stop_event.is_set():
            # avoid trying to re-run current command
            # - e.g. user pressed the same button on the remote twice
            newInstructionReceived = currentCommand != self.__instruction

            # prepare to run new instructions
            if newInstructionReceived:
                print()
                print("==================")
                print(">> NEW INSTRUCTION")
                print(f">> BLIND EXTENSION LENGTH '{self.__blindExtensionLength}'")
                print(f">> BLIND SPEED CM PER SECOND '{self.__blindSpeedInCmPerSecond}'")

                # if motor was running when new instruction was received
                if currentCommand["value"] != Command.Stop.value:
                    # update tracking data
                    self.__blindExtensionLength = self.__calculateNewBlindPosition(
                        loopCheckPointTime=loopCheckPointTime, shouldMoveUpward=shouldMoveUpward
                    )
                    self.__ensureValuesAreWithinConstraints()
                    self.__writeNewLengthToDisk()

                # prepare to run new instruction
                currentCommand = deepcopy(self.__instruction)
                print(f'{currentCommand=}')

                # trigger motor and get updates for trackers
                shouldMoveUpward, newRequestedLength = (
                    self.__actOnNewInstruction().getValues()
                )
                print(f'{shouldMoveUpward=}')

                # start tracking time elapsed since last loop ran
                loopCheckPointTime = timer()

            # motor is already stopped, there is nothing to do
            if self.__instruction["value"] == Command.Stop.value:
                # run loop until new instructions received
                continue

            # new instructions running
            # use loop time tracker to calculate the latest blind length
            self.__blindExtensionLength = self.__calculateNewBlindPosition(
                loopCheckPointTime=loopCheckPointTime, shouldMoveUpward=shouldMoveUpward
            )
            self.__ensureValuesAreWithinConstraints()
            now = timer()

            # only print latest state every second to lessen strain on Pi
            if now - counterCheckpointTime > 1:
                print()
                print(f'{self.__presentDutyCycle=}')
                print(f' NEW LENGTH {round(self.__blindExtensionLength, 2)=}')
                counterCheckpointTime = now

            # reset the loop time tracker
            loopCheckPointTime = now

            # check of goal state was achieved
            blindHasFinishedRolling = self.__hasBlindHasFinishedRolling(
                _shouldMoveUpward=shouldMoveUpward,
                _newRequestedLength=newRequestedLength
            )

            # goal was reached for instruction, reset everything
            if blindHasFinishedRolling:
                print(">> DONE")
                print(f">> BLIND EXTENSION LENGTH '{self.__blindExtensionLength}'")

                # stop the motor and update file on disk
                self.__handleStopInstruction()
                self.__ensureValuesAreWithinConstraints()
                self.__writeNewLengthToDisk()

                # reset the instruction to a stopped state
                self.__instruction = deepcopy(self.__getStopInstruction())
                currentCommand = deepcopy(self.__instruction)

                # print to terminal
                print(f'{self.__instruction=}')
                print(f"{currentCommand=}")
                print(";;;;;;;;;;;;;;;;;;;;")
                print()

    def cleanup(self):
        """
        Tidy up when error occurs, or thread is ended
        """
        print("CLEANUP REQUESTED: Start motor controller cleanup")

        # make sure latest state was flush to disk
        self.__writeNewLengthToDisk()

        # tidy board
        self.__pwm.stop()
        self.__leds.cleanup()
        GPIO.cleanup()

        # stop this thread
        print("Stop thread")
        self.__stop_event.set()
        sleep(1)
        print("\n---> THREAD MOTOR CONTROLLER CLEANUP COMPLETE :)\n")
