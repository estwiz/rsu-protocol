import asyncio
import json
from typing import Coroutine, Dict

import pdu
from quic import QuicConnection, QuicStreamEvent


async def server_proto(scope: Dict, conn: QuicConnection):
    """
    Echo server protocol implementation.

    This function handles the logic for receiving a message from the client,
    processing it, and sending a response back to the client.

    Args:
            scope (Dict): The scope of the connection.
            conn (EchoQuicConnection): The QUIC connection object.

    Returns:
            None
    """
    message: QuicStreamEvent = await conn.receive()

    # Convert the received data into a Datagram object
    dgram_in = pdu.Datagram.from_bytes(message.data)
    print("[svr] received message: ", dgram_in.msg)

    # Get the stream ID from the received message
    stream_id = message.stream_id

    # Modify the Datagram object to include an ACK and a response message
    dgram_out = dgram_in
    dgram_out.mtype |= pdu.MSG_TYPE_DATA_ACK
    dgram_out.msg = "SVR-ACK: " + dgram_out.msg

    # Convert the modified Datagram object back into bytes
    rsp_msg = dgram_out.to_bytes()

    # Create a new QuicStreamEvent with the modified response message
    rsp_evnt = QuicStreamEvent(stream_id, rsp_msg, False)

    # Send the response event back to the client
    await conn.send(rsp_evnt)
