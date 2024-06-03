import asyncio
import json
from typing import Coroutine, Dict

import common.pdu as pdu
from common.quic import QuicConnection, QuicStreamEvent
from server.dfa_server import ServerContext


async def run(scope: Dict, conn: QuicConnection):
    """
    Echo server protocol implementation.

    This function handles the logic for receiving a message from the client,
    processing it, and sending a response back to the client.

    Args:
            scope (Dict): The scope of the connection.
            conn (EchoQuicConnection): The QUIC connection object.

    Returns: None
    """
    event: QuicStreamEvent = await conn.receive()

    server: ServerContext = ServerContext(conn=conn)

    await server.handle_incoming_event(event=event)
