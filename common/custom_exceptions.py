class IncompatibleProtocolVersion(Exception):
    def __init__(self, message="Server and client have incompatible protocol versions"):
        self.message = message
        super().__init__(self.message)


class IncompatibleFirmwareVersion(Exception):
    def __init__(self, message="Server does not have latest firmware version"):
        self.message = message
        super().__init__(self.message)
