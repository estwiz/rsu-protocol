from typing import Optional, Union

import common.pdu as pdu
from common.data_processor import DataAssembler
from common.quic import QuicStreamEvent


class ClientState:
    def __init__(self, client: "ClientContext"):
        self.client = client

    async def handle_incoming_event(self, event: Optional[QuicStreamEvent]):
        raise NotImplementedError("handle_incoming_event not implemented")


class IdleState(ClientState):

    async def handle_incoming_event(self, event: Optional[QuicStreamEvent]):
        await self._send_request()

    async def _send_request(self):
        # Create a new datagram with a test message
        datagram = pdu.Datagram(mtype=pdu.MSG_TYPE_REQUEST_UPDATE, payload=b"")

        # Start a new stream and get its id
        new_stream_id = self.client.conn.new_stream()

        # Create a QuicStreamEvent with the stream id and the datagram data in bytes
        qs = QuicStreamEvent(
            stream_id=new_stream_id, data=datagram.to_bytes(), end_stream=False
        )
        await self.client.conn.send(qs)
        print("Request for firmware sent")
        self.client.set_state(RequestingState(self.client))


class RequestingState(ClientState):

    async def handle_incoming_event(self, event: Optional[QuicStreamEvent]):
        await self._receive_data()

    async def _receive_data(self, save_path: str = "./client/firmware/firmware.bin"):
        firmware_received = b""
        assembler = DataAssembler()

        # Receive multiple segments of data from server
        while True:
            event = await self.client.conn.receive()
            self.client.set_state(RecievingState(self.client))
            dgram_in = pdu.Datagram.from_bytes(event.data)

            # firmware_received += base64.b64decode(dgram_in.payload)
            assembler.add_segment(dgram_in.payload)

            if dgram_in.mtype == pdu.MSG_TYPE_FINISH_SND_DATA:
                self.client.set_state(SendingAckState(self.client))
                break

        if dgram_in.mtype == pdu.MSG_TYPE_FINISH_SND_DATA:
            print("Last segment received, sending ACK")
            # Send ack
            ack_datagram = pdu.Datagram(pdu.MSG_TYPE_SEND_ACK, b"All data received")
            qs = QuicStreamEvent(
                stream_id=event.stream_id, data=ack_datagram.to_bytes(), end_stream=True
            )
            await self.client.conn.send(qs)
            self.client.set_state(IdleState(self.client))

        # Save firmware as a binary file
        firmware_received = assembler.assemble()
        with open(save_path, "wb") as firmware_file:
            firmware_file.write(firmware_received)
            print(f"Firmware received and saved at {save_path}")


class RecievingState(ClientState):
    pass


class SendingAckState(ClientState):
    pass


class ClientContext:
    def __init__(self, conn):
        self.conn = conn
        self.state = IdleState(self)

    def set_state(self, state: ClientState):
        self.state = state

    async def handle_incoming_event(self, event: Optional[QuicStreamEvent]):
        await self.state.handle_incoming_event(event)