import asyncio
import json
from typing import Coroutine, Dict

import pdu
from dfa_server import ServerContext
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
    event: QuicStreamEvent = await conn.receive()

    server: ServerContext = ServerContext(conn=conn)

    await server.handle_incoming_event(event=event)

    # # Convert the received data into a Datagram object
    # dgram_in = pdu.Datagram.from_bytes(message.data)
    # stream_id = message.stream_id

    # if message and dgram_in.mtype == pdu.MSG_TYPE_REQUEST_UPDATE:
    #     print("Request for software update received")

    #     # Create a new datagram with a test message
    #     for x in range(3):
    #         dgram_out = pdu.Datagram(
    #             pdu.MSG_TYPE_START_SND_DATA, "Software update sent segement " + str(x)
    #         )
    #         rsp_event = QuicStreamEvent(message.stream_id, dgram_out.to_bytes(), False)
    #         print("Sending segment " + str(x))
    #         await conn.send(rsp_event)

    #     dgram_out = pdu.Datagram(
    #         pdu.MSG_TYPE_FINISH_SND_DATA, "Software update sent segment " + str(x + 1)
    #     )
    #     print("Sending segment " + str(x + 1))
    #     rsp_event = QuicStreamEvent(message.stream_id, dgram_out.to_bytes(), True)
    #     await conn.send(rsp_event)
