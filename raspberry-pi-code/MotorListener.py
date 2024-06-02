import socket
import threading
from pathlib import Path
from typing import TextIO, List
from ThreadMotorController import ThreadMotorController


class MotorListener:
    # setup reading of latest state from file
    # useful when starting up after a power outage
    __startOfFile = 0
    __filePath: Path = None
    __fileMode: str = None
    __fileName = "blind-state.txt"
    __createReadWrite = "w+"
    __openReadWrite = "r+"

    # http state codes
    __okay = 204
    __noChange = 304
    __badRequest = 422
    __httpStatusCodes = {
        __okay: "204 No Content",
        __noChange: "304 Not Modified",
        __badRequest: "400 Bad Request",
    }

    # network data
    __host: str = None
    __motorPort: int = 5000
    __address = None
    __network: socket = None
    __connection: socket = None

    # blind data
    __fileDataSavedBlindLength: float = None

    # motor controller (runs in background with multithreading)
    __threadedMotorController: ThreadMotorController = None
    __clientThreads: List[threading.Thread] = []
    __keepRunningThreads: bool = True

    # list of network connections that get cleaned up at end
    __clients: List[tuple[socket.socket, tuple[str, int]]] = []

    def __init__(self):
        self.__prepareNetwork()
        self.__prepareFile()

    def __prepareNetwork(self):
        # prepare network listener
        self.__host: str = socket.gethostname()
        self.__network: socket.socket = socket.socket()
        self.__network.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__network.bind((self.__host, self.__motorPort))

        # accept many simultaneous network connections
        self.__network.listen(100)

    def __prepareFile(self):
        """
            - Save blind's state to file
            - useful for when starting/restarting
        """

        # open existing file or create new one if no file was found
        self.__filePath: Path = Path(f"./{self.__fileName}")
        fileExistedAtInstantiation: bool = self.__filePath.is_file()
        self.__fileMode: str = self.__openReadWrite if fileExistedAtInstantiation else self.__createReadWrite

        # open the file
        with open(self.__filePath, self.__fileMode) as _file:
            # create a default value in new state files
            if not fileExistedAtInstantiation:
                self.__writeNewLengthToDisk(_file, 0)

            # read the file
            _blindExtensionLength = _file.read()
            print("### FILE DATA ###")
            print(f"Length from file: {_blindExtensionLength}")

            # make the state usable
            try:
                _blindExtensionLength = float(_blindExtensionLength)
                print(f"Length as float: {_blindExtensionLength}")
                print()
            except ValueError:
                self.__writeNewLengthToDisk(_file, 0)
                _blindExtensionLength = 0

            # use the read data
            self.__fileDataSavedBlindLength = _blindExtensionLength
            _file.close()

    @staticmethod
    def __writeNewLengthToDisk(_file: TextIO, _blindExtensionLength: float):
        _file.seek(0)
        _file.write(str(_blindExtensionLength))
        _file.truncate()
        _file.flush()

    def listenForMotorCommands(self):
        """
        Listens on port 5000 for instructions from network clients (e.g. infra-red remote)
        """

        _file: TextIO  # annotate type before instantiation
        with open(self.__filePath, self.__fileMode) as _file:

            # run motor controller as background thread
            # allows main thread to keep listening for new network commands
            self.__threadedMotorController = ThreadMotorController(
                _file=_file,
                _initialBlindExtensionLength=self.__fileDataSavedBlindLength
            )
            self.__threadedMotorController.start()

            # listen for new connections
            try:
                while True:
                    # accept new client connections
                    print("### LISTENING ###")
                    client, address = self.__network.accept()
                    print(f"GOT NEW Client address: {address}, try to append to __clients list")
                    self.__clients.append((client, address))

                    # push new client in background thread
                    # - allows main thread to keep listening for new clients
                    print("### TRY PUSHING CLIENT TO THREAD ###")
                    newThread = threading.Thread(
                        target=lambda: self.__networkHandler(_client=client, _address=address),
                    )
                    print("### TRY STARTING THREAD ###")
                    newThread.start()
                    print("### TRY APPENDING THREAD ###")
                    self.__clientThreads.append(newThread)
                    print("### __ SUCCESS __ ###")

            except Exception as error:
                print("----> listenForMotorCommands EXCEPTION <------")
                print("----> listenForMotorCommands EXCEPTION <------")
                print("----> listenForMotorCommands EXCEPTION <------")
                print(f'{error=}')

                print()
                print("----> CLEANUP <------")

                # if script is closed (or errors out)
                # run cleanup for network and thread
                self.__cleanup()

    @staticmethod
    def __disconnectClient(_client: socket.socket):
        # cleanup connection to client
        print()
        print("### DISCONNECT CLIENT ###")
        _client.shutdown(socket.SHUT_RDWR)
        _client.close()
        print("### DISCONNECT COMPLETE ###")
        print()

    def __networkHandler(self, _client: socket.socket, _address):
        """
        MAIN WORK WITH CLIENT IS DONE HERE
        - Handle new instructions from clients
        - Pass instruction to Motor Controller
        """
        print("::: NEW CLIENT :::")
        print(f'>>> address: "{_address=}"')
        print()

        try:
            while self.__keepRunningThreads:
                # receive command and print it
                httpMessage = _client.recv(2048).decode()
                print(">>>>> PARTS")
                for httpPart in httpMessage.split("\n"):
                    print(httpPart)
                print(">>>>> END PARTS")

                # get command from message body
                _newInstruction = httpMessage.split("\n")[-1]

                # invalid message received
                if not _newInstruction:
                    # respond with error
                    print(f"Invalid instruction '{_newInstruction}'")
                    _client.sendall(self.__generateHttpResponse(self.__badRequest).encode())
                    self.__disconnectClient(_client)
                    return

                # caller just wants to know the state of the blind
                if _newInstruction == "status":
                    # get latest state from Motor Controller
                    print()
                    print(f"Status requested '{_newInstruction}'")
                    _status = self.__threadedMotorController.currentInstruction()

                    # send status back to caller
                    print(f'Sending "{_status}')
                    _client.sendall(_status.encode())
                    self.__disconnectClient(_client)
                    print(f'Sent "{_status}')
                    print()
                    return

                # if already doing what new instruction asked for
                if _newInstruction == self.__threadedMotorController.currentInstruction():
                    # no change needed, respond as done
                    print(f"No change to instruction '{_newInstruction}'")
                    _client.sendall(self.__generateHttpResponse(self.__noChange).encode())
                    self.__disconnectClient(_client)
                    return

                # valid instruction received:
                # - let the motor controller know
                # - motor controller will handle this in the background in a separate thread
                self.__threadedMotorController.instruct(_newInstruction)

                # let caller know that we will action the valid request
                _client.sendall(self.__generateHttpResponse(self.__okay).encode())
                print(f'HANDLED INSTRUCTION "{_newInstruction}", RETURNING FROM THREAD')
                self.__disconnectClient(_client)
                return

        except Exception as error:
            print("----> __networkHandler EXCEPTION <------")
            print("----> __networkHandler EXCEPTION <------")
            print("----> __networkHandler EXCEPTION <------")
            print(f'{error=}')

    def __generateHttpResponse(self, _code: int) -> str:
        return f'HTTP/1.1 "{self.__httpStatusCodes[_code]}"'

    def __cleanup(self):
        print("Start listener cleanup")

        # cleanup connection
        if self.__connection is not None:
            # clean up clients
            for client, address in self.__clients:
                client.close()

            # clean up socket
            self.__connection.close()
            print("Connection closed")
        else:
            print("NOTICE: No network found to clean")

        # join background client threads to this one
        # i.e. it closes those threads
        for _clientThread in self.__clientThreads:
            _clientThread.join()

        # clean up the Motor Controller thread
        print("Listener cleaned up")
        print()
        print("=== MOTOR CONTROLLER THREAD CLEANUP ===")
        self.__threadedMotorController.cleanup()
        print(" >> try to join thread <<")
        self.__threadedMotorController.join()
        print(" >> THREAD JOIN FINISHED <<")


if __name__ == "__main__":
    motorListener = MotorListener()
    motorListener.listenForMotorCommands()
