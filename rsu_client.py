import json
from typing import Dict

import pdu
from quic import QuicConnection, QuicStreamEvent


async def client_proto(scope: Dict, conn: QuicConnection):
    """
    This function represents the client-side logic for the QUIC echo client.

    Args:
        scope (Dict): The scope of the client connection.
        conn (EchoQuicConnection): The QUIC connection object.

    Returns:
        None
    """

    # START CLIENT HERE
    # Print a message indicating that the client is starting
    print("[cli] starting client")

    # Create a new datagram with a test message
    datagram = pdu.Datagram(pdu.MSG_TYPE_REQUEST_UPDATE, "This is a request for software update")

    # Start a new stream and get its id
    new_stream_id = conn.new_stream()

    # Create a QuicStreamEvent with the stream id and the datagram data in bytes
    qs = QuicStreamEvent(
        stream_id=new_stream_id, data=datagram.to_bytes(), end_stream=False
    )
    await conn.send(qs)
    print("[cli] sent message: ", datagram.msg)
    
    while True:
        # Receive a message from the connection
        message: QuicStreamEvent = await conn.receive()

        # Convert the received data back to a Datagram object
        dgram_resp = pdu.Datagram.from_bytes(message.data)

        # Print the received message and its JSON representation
        print("[cli] got message: ", dgram_resp.msg)
        print("[cli] msg as json: ", dgram_resp.to_json())
        
        if dgram_resp.mtype == pdu.MSG_TYPE_FINISH_SND_DATA:
            break
        # END CLIENT HERE
        
    
    # Send ack
    ack_datagram = pdu.Datagram(pdu.MSG_TYPE_SEND_ACK, "All data received")
    qs = QuicStreamEvent(
        stream_id=new_stream_id, data=ack_datagram.to_bytes(), end_stream=True
    )
    await conn.send(qs)