import base64
import json
from typing import Dict

import common.pdu as pdu
from client.dfa import ClientContext
from common.data_processor import DataAssembler
from common.quic import QuicConnection, QuicStreamEvent


async def run(scope: Dict, conn: QuicConnection):
    """
    This function represents the client-side logic for the QUIC rsu client.

    Args:
        scope (Dict): The scope of the client connection.
        conn (QuicConnection): The QUIC connection object.

    Returns: None
    """

    client: ClientContext = ClientContext(conn=conn)
    # Start client and send version exchange
    await client.handle_incoming_event(event=None)

    # Receive the version acknowledgment and send firmware update request
    event_ver_ack = await conn.receive()
    await client.handle_incoming_event(event=event_ver_ack)

    # Receive the firmware update and send the firmware update acknowledgment
    await client.handle_incoming_event(event=None)
