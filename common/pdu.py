import base64
import json

# Message types
MSG_TYPE_VERSION_EXCHANGE = 0x00
MSG_TYPE_VERSION_ACK = 0x01
MSG_TYPE_REQUEST_UPDATE = 0x02
MSG_TYPE_START_RCV_DATA = 0x03
MSG_TYPE_FINISH_RCV_DATA = 0x04
MSG_TYPE_SEND_ACK = 0x05
MSG_TYPE_START_SND_DATA = 0x06
MSG_TYPE_FINISH_SND_DATA = 0x07
MSG_TYPE_RECEIVE_ACK = 0x08
MSG_TYPE_ERROR = 0x09


class Datagram:
    """
    Represents a datagram object used in network communication.
    """

    def __init__(
        self,
        mtype: int,
        payload: bytes = b"",
        protocol_ver: str = "",
        firmware_ver: str = "",
        size: int = 0,
    ):
        self.mtype = mtype
        self.payload = base64.b64encode(payload).decode("utf-8")
        self.protocol_ver = protocol_ver
        self.firmware_ver = firmware_ver
        self.size = len(self.payload)

    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_str):
        return Datagram(**json.loads(json_str))

    def to_bytes(self):
        return json.dumps(self.__dict__).encode("utf-8")

    @staticmethod
    def from_bytes(json_bytes: bytes) -> "Datagram":
        input_dict = json.loads(json_bytes.decode("utf-8"))
        input_dict["payload"] = base64.b64decode(input_dict["payload"])
        return Datagram(**input_dict)
