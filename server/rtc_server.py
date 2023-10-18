import aiortc
from aiortc.contrib.signaling import TcpSocketSignaling, BYE
from ball_bouncing_track import BallBouncingTrack
from typing import Tuple
import cv2
import numpy as np
class RTCServer():
    '''
        Class for an RTCServer that serves a video of a ball bouncing across the screen. If the client sends back
        coordinates, the server will calculate the error in the coordinates and attempt to draw the error using
        cv.imshow().
    '''
    def __init__(self, host: str, port: str, velocity: int, radius: int, width: int, height: int):
        self.ball_position = {}
        self.signal = TcpSocketSignaling(host, port)
        self.pc = aiortc.RTCPeerConnection()
        self.channel = self.pc.createDataChannel("RTCchannel")
        self.stream_track = BallBouncingTrack(velocity, radius, width, height, self.ball_position)
        self.pc.addTrack(self.stream_track)

    def calculate_error(self, actual: Tuple[int, int], estimated: Tuple[int, int]):
        '''
            Calculates Euclidean Distance as Error for an actual point and an estimated point from the client
        '''
        return np.linalg.norm(np.asarray(actual) - np.asarray(estimated))


    def display_frame(self, server_loc: Tuple[int, int], client_estimated_loc: Tuple[int, int]):
        '''
            Draws original ball frame in green with client's estimate on top with
            a red center and outline.
        '''
        radius = self.stream_track.radius
        frame_server = np.zeros((self.stream_track.height, self.stream_track.width, 3), dtype='uint8')
        frame_client_estimated = np.zeros((self.stream_track.height, self.stream_track.width, 3), dtype='uint8')
        cv2.circle(frame_server, server_loc, radius=radius, color=(0,255,0), thickness=-1)
        cv2.circle(frame_client_estimated, client_estimated_loc, radius=radius, color=(0,0,255), thickness=-1)
        frame = cv2.addWeighted(frame_server, 0.5, frame_client_estimated, 0.5, 0)
        cv2.imshow("server", frame)
        cv2.waitKey(1)

    async def register_on_callbacks(self):
        '''
            Define event callback functions here
        '''
        channel = self.channel
        @channel.on("message")
        def on_message(message):
            '''
                When a message comes over the datachannel, this function gets called
                This function parses the message and then attempts to calculate
                RMS Error and draw the received ball coordinates from the client.
            '''
            values = message.split('\t') # for returned estimated coordinates, server expects a string with format: "{x_pos}\t{y_pos}\t{timestamp}"

            try:
                ball_location_dict = self.stream_track.ball_location_dict
                timestamp = int(values[2])
                server_loc = ball_location_dict[timestamp]
                client_estimated_loc = (int(values[0]), int(values[1]))
                self.display_frame(server_loc, client_estimated_loc)
                error = self.calculate_error(server_loc, client_estimated_loc)
                #print timestamp and corresponding values every few seconds
                if timestamp % 50000 == 0:
                    print(f"=====timestamp {timestamp}=====\n\tserver ball location: "
                        f"{server_loc}\n\tclient estimated location: {client_estimated_loc}\n\tError(euclidean distance): {round(error,2)}")
                del ball_location_dict[int(values[2])]
            except Exception as e:
                print("Error:", e)
        
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            '''
                Log details about connection state. if connection fails, just exit program
            '''
            print(f"connection state is {self.pc.connectionState}")
            if self.pc.connectionState == "failed":
                await self.pc.close()
                exit(-1)


    async def run(self):
        '''
            Event loop for running the server
        '''
        await self.register_on_callbacks()

        # creates SDP offer to send to client over tcp
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        # sends offer to a client that connects with the server
        await self.signal.send(self.pc.localDescription)

        print("offer received")

        while await self.consume_signal():
            print("signal consumed")
            continue
        await self.shutdown()
        return True
    

    async def shutdown(self):
        '''
            Method to shutdown server
            Attempts to close all connections
        '''
        await self.signal.close()
        try:
            await self.channel.close()
        except TypeError:
            pass
        try:
            await self.pc.close()
        except TypeError:
            pass

    async def consume_signal(self) -> bool:
        '''
            waits for a signal response through a tcp connection.

            If the data recieved through the signal is an ICE Candidate or and SDP offer/answer,
            handle that case and return True

            If not Returns False
        '''
        obj = await self.signal.receive()
        if isinstance(obj, aiortc.RTCSessionDescription):
            await self.pc.setRemoteDescription(obj)
            return True
        elif isinstance(obj, aiortc.RTCIceCandidate):
            await self.pc.addIceCandidate(obj)
            return True
        if obj is BYE:
            print("goodbye")
        return False