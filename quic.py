from typing import Callable, Coroutine, Optional


class QuicStreamEvent:
    """
    Represents a QUIC stream event.

    Attributes:
        stream_id (int): The ID of the stream.
        data (bytes): The data associated with the event.
        end_stream (bool): Indicates whether the stream has ended.
    """

    def __init__(self, stream_id: int, data: bytes, end_stream: bool):
        self.stream_id = stream_id
        self.data = data
        self.end_stream = end_stream


class QuicConnection:
    """
    Represents a QUIC connection for echoing messages.

    Args:
        send (Coroutine[QuicStreamEvent, None, None]): A coroutine function used for sending messages.
        receive (Coroutine[None, None, QuicStreamEvent]): A coroutine function used for receiving messages.
        close (Optional[Callable[[], None]]): An optional callable function used for closing the connection.
        new_stream (Optional[Callable[[], int]]): An optional callable function used for creating a new stream.

    Attributes:
        send (Coroutine[QuicStreamEvent, None, None]): A coroutine function used for sending messages.
        receive (Coroutine[None, None, QuicStreamEvent]): A coroutine function used for receiving messages.
        close (Optional[Callable[[], None]]): An optional callable function used for closing the connection.
        new_stream (Optional[Callable[[], int]]): An optional callable function used for creating a new stream.
    """

    def __init__(
        self,
        send: Coroutine[QuicStreamEvent, None, None],
        receive: Coroutine[None, None, QuicStreamEvent],
        close: Optional[Callable[[], None]],
        new_stream: Optional[Callable[[], int]],
    ):
        self.send = send
        self.receive = receive
        self.close = close
        self.new_stream = new_stream
