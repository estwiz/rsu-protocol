import base64
import json
from typing import Dict

import pdu
from data_processor import DataAssembler
from dfa_client import ClientContext
from quic import QuicConnection, QuicStreamEvent


async def client_proto(scope: Dict, conn: QuicConnection):
    """
    This function represents the client-side logic for the QUIC echo client.

    Args:
        scope (Dict): The scope of the client connection.
        conn (EchoQuicConnection): The QUIC connection object.

    Returns: None
    """

    client: ClientContext = ClientContext(conn=conn)
    # Start client and send request to server
    await client.handle_incoming_event(event=None)

    # Gather the response from the server
    await client.handle_incoming_event(event=None)
