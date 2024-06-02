import pdu
from pdu import Datagram
from quic import QuicConnection, QuicStreamEvent


class ServerState:
    def __init__(self, server: "ServerContext"):
        self.server = server

    async def handle_incoming_event(self, event: QuicStreamEvent):
        pass


class IdleState(ServerState):
    async def handle_incoming_event(self, event: QuicStreamEvent):
        dgram_in = Datagram.from_bytes(event.data)
        stream_id = event.stream_id

        if dgram_in.mtype == pdu.MSG_TYPE_REQUEST_UPDATE:
            # Set the state to SendingState
            self.server.set_state(SendingState(self.server))
            await self._send_firmware(
                stream_id, firmware_path="firmware_send/firmware.bin"
            )

    async def _send_firmware(
        self, stream_id: int, firmware_path: str = "firmware_send/firmware.bin"
    ) -> None:

        # load data as bytes
        with open(firmware_path, "rb") as f:
            data = f.read()

        # Create segments of data
        segments = []
        for i in range(0, len(data), 2):
            segments.append(data[i : i + 2])

        # Send the first n-1 segments
        for segment_data in segments[:-1]:
            dgram_out = Datagram(pdu.MSG_TYPE_START_SND_DATA, data)
            response_event = QuicStreamEvent(stream_id, dgram_out.to_bytes(), False)
            print("Sending segment: " + segment_data)
            await self.server.conn.send(response_event)

        # send last segment
        dgram_out = Datagram(pdu.MSG_TYPE_FINISH_SND_DATA, data)
        response_event = QuicStreamEvent(stream_id, dgram_out.to_bytes(), True)
        print("Sending segment: " + segments[-1])
        await self.server.conn.send(response_event)
        # Set the state to AwaitingAckState
        self.server.set_state(AwaitingAckState(self.server))


class SendingState(ServerState):
    """
    Sending state for the server.
    It does not handle any incoming events.
    it transitions to AwaitingAckState after sending the firmware.
    """

    pass


class AwaitingAckState(ServerState):
    async def handle_incoming_event(self, event: QuicStreamEvent):
        dgram_in = Datagram.from_bytes(event.data)
        stream_id = event.stream_id

        if dgram_in.mtype == pdu.MSG_TYPE_RECEIVE_ACK:
            print("Received ACK from client")
            self.server.set_state(IdleState(self.server))


class ServerContext:
    def __init__(self, conn: QuicConnection):
        self.conn = conn
        self.state = IdleState(self)

    def set_state(self, state: ServerState):
        self.state = state

    async def handle_incoming_event(self, event: QuicStreamEvent):
        await self.state.handle_incoming_event(event)
