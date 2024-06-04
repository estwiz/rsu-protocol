from typing import Optional, Union

import common.pdu as pdu
from client.version import ClientVer
from common.data_processor import DataAssembler
from common.quic import QuicStreamEvent


class ClientState:
    """Base class for client state"""

    def __init__(self, client: "ClientContext"):
        self.client = client

    async def handle_incoming_event(self, event: Optional[QuicStreamEvent]):
        raise NotImplementedError("handle_incoming_event not implemented")


class IdleState(ClientState):
    """
    Initial state for the client.
    Waits for the server to send a version exchange request.
    """

    async def handle_incoming_event(self, event: Optional[QuicStreamEvent]):
        await self._send_ver_exchange_request()

    async def _send_ver_exchange_request(self):
        # Create a new datagram for version exchange
        datagram = pdu.Datagram(
            mtype=pdu.MSG_TYPE_VERSION_EXCHANGE,
            protocol_ver=ClientVer.protocol,
            firmware_ver=ClientVer.firmware,
        )

        # Start a new stream and get its id
        new_stream_id = self.client.conn.new_stream()

        # Create a QuicStreamEvent with the stream id and the datagram data in bytes
        qs = QuicStreamEvent(
            stream_id=new_stream_id, data=datagram.to_bytes(), end_stream=False
        )
        await self.client.conn.send(qs)
        print("Request for version exchange sent")
        self.client.set_state(RequestVersionExchangeState(self.client))


class RequestVersionExchangeState(ClientState):
    """State for the client to wait for the server to send a version ack."""

    async def handle_incoming_event(self, event: Optional[QuicStreamEvent]):
        # Check if version are compatible
        dgram_in = pdu.Datagram.from_bytes(event.data)
        if dgram_in.mtype == pdu.MSG_TYPE_VERSION_ACK:
            await self._firmware_request(event)

    async def _firmware_request(self, event):
        # Create a new datagram with a test message
        datagram = pdu.Datagram(mtype=pdu.MSG_TYPE_REQUEST_UPDATE, payload=b"")

        # Create a QuicStreamEvent with the stream id and the datagram data in bytes
        qs = QuicStreamEvent(
            stream_id=event.stream_id, data=datagram.to_bytes(), end_stream=True
        )
        await self.client.conn.send(qs)
        print("Request for firmware sent")
        self.client.set_state(ReceivingFirmwareState(self.client))


class ReceivingFirmwareState(ClientState):
    """State for the client to receive firmware from the server."""

    async def handle_incoming_event(self, event: Optional[QuicStreamEvent]):
        await self._receive_data()

    async def _receive_data(self, save_path: str = "./client/firmware/firmware.bin"):
        firmware_received = b""
        assembler = DataAssembler()

        # Receive multiple segments of data from server
        while True:
            event = await self.client.conn.receive()
            self.client.set_state(ReceivingFirmwareState(self.client))
            dgram_in = pdu.Datagram.from_bytes(event.data)

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

        # Save firmware as a binary file
        firmware_received = assembler.assemble()
        with open(save_path, "wb") as firmware_file:
            firmware_file.write(firmware_received)
            print(f"Firmware received and saved at {save_path}")

        self.client.set_state(IdleState(self.client))


class SendingAckState(ClientState):
    """
    State for the client to send an ACK to the server.
    No implementation here because logic is in ReceivingFirmwareState.
    """

    pass


class ClientContext:
    """Context for the client state machine."""

    def __init__(self, conn):
        self.conn = conn
        self.state = IdleState(self)

    def set_state(self, state: ClientState):
        self.state = state

    async def handle_incoming_event(self, event: Optional[QuicStreamEvent]):
        await self.state.handle_incoming_event(event)
