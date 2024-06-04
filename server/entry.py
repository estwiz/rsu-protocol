import asyncio
import json
from typing import Coroutine, Dict

import common.pdu as pdu
from common.quic import QuicConnection, QuicStreamEvent
from server.dfa import ServerContext


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

    server: ServerContext = ServerContext(conn=conn)

    # Start the server and wait for the version exchange
    event_ver_ex: QuicStreamEvent = await conn.receive()
    await server.handle_incoming_event(event=event_ver_ex)

    # Wait for the request for the firmware update and send data
    event_fw_update: QuicStreamEvent = await conn.receive()
    await server.handle_incoming_event(event=event_fw_update)
