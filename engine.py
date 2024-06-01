import asyncio
import json
from typing import Callable, Dict, Optional

from aioquic.asyncio import connect, serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived
from aioquic.tls import SessionTicket

import rsu_client
import rsu_server
from quic import QuicConnection, QuicStreamEvent

# ALPN_PROTOCOL: A string representing the ALPN (Application-Layer Protocol Negotiation) protocol used by the QUIC connections.
# SERVER_MODE: An integer constant representing the server mode.
# CLIENT_MODE: An integer constant representing the client mode.
ALPN_PROTOCOL = "echo-protocol"
SERVER_MODE = 0
CLIENT_MODE = 1


def build_server_quic_config(cert_file, key_file) -> QuicConfiguration:
    """
    Build the QuicConfiguration for the server.

    Args:
        cert_file (str): The path to the certificate file.
        key_file (str): The path to the private key file.

    Returns:
        QuicConfiguration: The QuicConfiguration object.
    """
    configuration = QuicConfiguration(alpn_protocols=[ALPN_PROTOCOL], is_client=False)
    configuration.load_cert_chain(cert_file, key_file)

    return configuration


def build_client_quic_config(cert_file=None):
    """
    Build the QuicConfiguration for the client.

    Args:
        cert_file (str, optional): The path to the certificate file. Defaults to None.

    Returns:
        QuicConfiguration: The QuicConfiguration object.
    """
    configuration = QuicConfiguration(alpn_protocols=[ALPN_PROTOCOL], is_client=True)
    if cert_file:
        configuration.load_verify_locations(cert_file)

    return configuration


def create_msg_payload(msg) -> bytes:
    """
    Create a message payload.

    Args:
        msg: The message to be encoded.

    Returns:
        bytes: The encoded message payload.
    """
    return json.dumps(msg).encode("utf-8")


async def run_server(server: str, server_port: int, configuration: QuicConfiguration):
    """
    Run the QUIC server.

    Args:
        server (str): The server address.
        server_port (int): The server port.
        configuration (QuicConfiguration): The server configuration.
    """
    print("[svr] Server starting...")
    await serve(
        host=server,
        port=server_port,
        configuration=configuration,
        create_protocol=AsyncQuicServer,
        session_ticket_fetcher=SessionTicketStore().pop,
        session_ticket_handler=SessionTicketStore().add,
    )
    await asyncio.Future()  # Runs the server indefinitely


async def run_client(server, server_port, configuration):
    """
    Run the QUIC client.

    Args:
        server (str): The server address.
        server_port (int): The server port.
        configuration (QuicConfiguration): The client configuration.
    """
    async with connect(
        host=server,
        port=server_port,
        configuration=configuration,
        create_protocol=AsyncQuicServer,
    ) as client:
        await asyncio.ensure_future(client._client_handler.launch())


class SessionTicketStore:
    """
    Simple in-memory store for session tickets.
    """

    def __init__(self) -> None:
        self.tickets: Dict[bytes, SessionTicket] = {}

    def add(self, ticket: SessionTicket) -> None:
        """
        Add a session ticket to the store.

        Args:
            ticket (SessionTicket): The session ticket.
        """
        self.tickets[ticket.ticket] = ticket

    def pop(self, label: bytes) -> Optional[SessionTicket]:
        """
        Pop a session ticket from the store.

        Args:
            label (bytes): The label of the session ticket.

        Returns:
            Optional[SessionTicket]: The session ticket, or None if not found.
        """
        return self.tickets.pop(label, None)


class AsyncQuicServer(QuicConnectionProtocol):
    """
    Asynchronous QUIC server implementation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._handlers: Dict[int, ServerRequestHandler] = {}
        self._client_handler: Optional[ClientRequestHandler] = None
        self._is_client: bool = self._quic.configuration.is_client
        self._mode: int = SERVER_MODE if not self._is_client else CLIENT_MODE
        if self._mode == CLIENT_MODE:
            self._attach_client_handler()

    def _attach_client_handler(self):
        """
        Attach the client request handler if the server is running in client mode.
        """
        if self._mode == CLIENT_MODE:
            self._client_handler = ClientRequestHandler(
                authority=self._quic.configuration.server_name,
                connection=self._quic,
                protocol=self,
                scope={},
                stream_ended=False,
                stream_id=None,
                transmit=self.transmit,
            )

    def remove_handler(self, stream_id):
        """
        Remove a request handler for a specific stream ID.

        Args:
            stream_id (int): The stream ID.
        """
        self._handlers.pop(stream_id)

    def _quic_client_event_dispatch(self, event):
        """
        Dispatch QUIC events for the client mode.

        Args:
            event: The QUIC event.
        """
        if isinstance(event, StreamDataReceived):
            self._client_handler.quic_event_received(event)

    def _quic_server_event_dispatch(self, event):
        """
        Dispatch QUIC events for the server mode.

        Args:
            event: The QUIC event.
        """
        handler = None
        if isinstance(event, StreamDataReceived):
            # new stream
            if event.stream_id not in self._handlers:
                handler = ServerRequestHandler(
                    authority=self._quic.configuration.server_name,
                    connection=self._quic,
                    protocol=self,
                    scope={},
                    stream_ended=False,
                    stream_id=event.stream_id,
                    transmit=self.transmit,
                )
                self._handlers[event.stream_id] = handler
                handler.quic_event_received(event)
                asyncio.ensure_future(handler.launch())
            # existing stream
            else:
                handler = self._handlers[event.stream_id]
                handler.quic_event_received(event)

    def quic_event_received(self, event):
        """
        Handle a QUIC event.

        Args:
            event: The QUIC event.
        """
        if self._mode == SERVER_MODE:
            self._quic_server_event_dispatch(event)
        else:
            self._quic_client_event_dispatch(event)

    def is_client(self) -> bool:
        """
        Check if the protocol is running in client mode.

        Returns:
            bool: True if the protocol is running in client mode, False otherwise.
        """
        return self._quic.configuration.is_client


class ServerRequestHandler:
    """
    Request handler for the QUIC server.
    """

    def __init__(
        self,
        *,
        authority: bytes,
        connection: AsyncQuicServer,
        protocol: QuicConnectionProtocol,
        scope: Dict,
        stream_ended: bool,
        stream_id: int,
        transmit: Callable[[], None],
    ) -> None:
        self.authority = authority
        self.connection = connection
        self.protocol = protocol
        self.queue: asyncio.Queue[QuicStreamEvent] = asyncio.Queue()
        self.scope = scope
        self.stream_id = stream_id
        self.transmit = transmit

        if stream_ended:
            self.queue.put_nowait({"type": "quic.stream_end"})

    def quic_event_received(self, event: StreamDataReceived) -> None:
        """
        Handle a QUIC event.

        Args:
            event (StreamDataReceived): The QUIC event.
        """
        self.queue.put_nowait(
            QuicStreamEvent(event.stream_id, event.data, event.end_stream)
        )

    async def receive(self) -> QuicStreamEvent:
        """
        Receive a QUIC stream event.

        Returns:
            QuicStreamEvent: The QUIC stream event.
        """
        queue_item = await self.queue.get()
        return queue_item

    async def send(self, message: QuicStreamEvent) -> None:
        """
        Send a QUIC stream event.

        Args:
            message (QuicStreamEvent): The QUIC stream event to send.
        """
        self.connection.send_stream_data(
            stream_id=message.stream_id,
            data=message.data,
            end_stream=message.end_stream,
        )

        self.transmit()

    def close(self) -> None:
        """
        Close the request handler.
        """
        self.protocol.remove_handler(self.stream_id)
        self.connection.close()

    async def launch(self):
        """
        Launch the echo server.
        """
        quic_conn = QuicConnection(self.send, self.receive, self.close, None)
        await rsu_server.server_proto(self.scope, quic_conn)


class ClientRequestHandler(ServerRequestHandler):
    """
    Request handler for the QUIC client.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_next_stream_id(self) -> int:
        """
        Get the next available stream ID.

        Returns:
            int: The next available stream ID.
        """
        return self.connection.get_next_available_stream_id()

    async def launch(self):
        """
        Launch the echo client.
        """
        quic_conn = QuicConnection(
            self.send, self.receive, self.close, self.get_next_stream_id
        )
        await rsu_client.client_proto(self.scope, quic_conn)
