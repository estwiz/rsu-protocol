import json

MSG_TYPE_DATA = 0x00
MSG_TYPE_ACK = 0x01
MSG_TYPE_DATA_ACK = MSG_TYPE_DATA | MSG_TYPE_ACK  # Both types


class Datagram:
    """
    Represents a datagram object used in network communication.

    Attributes:
        mtype (int): The message type of the datagram.
        msg (str): The message content of the datagram.
        sz (int): The size of the message content in bytes.

    Methods:
        to_json(): Converts the datagram object to a JSON string.
        from_json(json_str): Creates a datagram object from a JSON string.
        to_bytes(): Converts the datagram object to a byte string.
        from_bytes(json_bytes): Creates a datagram object from a byte string.
    """

    def __init__(self, mtype: int, msg: str, sz: int = 0):
        """
        Initializes a PDU (Protocol Data Unit) object.

        Args:
            mtype (int): The message type.
            msg (str): The message content.
            sz (int, optional): The size of the message. Defaults to 0.
        """
        self.mtype = mtype
        self.msg = msg
        self.sz = len(self.msg)

    def to_json(self):
        """
        Converts the datagram object to a JSON string.

        Returns:
            str: The JSON representation of the datagram object.
        """
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_str):
        """
        Creates a datagram object from a JSON string.

        Args:
            json_str (str): The JSON string representing the datagram object.

        Returns:
            Datagram: The created datagram object.
        """
        return Datagram(**json.loads(json_str))

    def to_bytes(self):
        """
        Converts the datagram object to a byte string.

        Returns:
            bytes: The byte representation of the datagram object.
        """
        return json.dumps(self.__dict__).encode("utf-8")

    @staticmethod
    def from_bytes(json_bytes):
        """
        Creates a datagram object from a byte string.

        Args:
            json_bytes (bytes): The byte string representing the datagram object.

        Returns:
            Datagram: The created datagram object.
        """
        return Datagram(**json.loads(json_bytes.decode("utf-8")))
