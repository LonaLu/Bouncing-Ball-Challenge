from typing import Tuple
import cv2 as cv
import numpy as np
import asyncio
import aiortc
from aiortc.contrib.signaling import TcpSocketSignaling, BYE
import av


########################################################################################################################
# code for generating video of ball bouncing
########################################################################################################################

class FrameGenerator():
    '''
        Class used to generate frames of a ball bouncing across the screen
    '''
    def __init__(self, velocity: int = 5, radius: int = 40, width = 640, height = 480):
        '''
            Initialize variables to start generating frames
                resolution = resolution    # resolution of the frames (width, height)
                velocity = velocity        # pixels per frame that ball will move in both x and y directions
                radius = radius            # radius of ball that will be drawn
                x_pos = self.radius        # current x position for center of ball
                y_pos = self.radius        # current y position for center of ball
                x_sense = 1                # direction of x velocity. Positive is to the right.
                y_sense = 1                # direction of y velocity. Positive is down.
        '''
        self.radius = radius
        self.width = width
        self.height = height            
        self.x_position = radius       
        self.y_position = radius
        self.x_velocity = velocity
        self.y_velocity = velocity             
    
    def get_frame(self):
        '''
            Generate the next frame
        '''
        # draw frame with ball in current position and add ball position to location queue
        frame = np.zeros((self.height, self.width, 3), dtype='uint8') # image will be in bgr representation
        cv.circle(frame, (self.x_position, self.y_position), radius = self.radius, thickness = -1, color = (110, 0, 255)) 
        return frame
    
    def increment_position(self):
        '''
            Increment the position of the ball by the velocity mulitplied by the sense.
            If ball is out of bounds, reverse the sense and increment in the other direction
        '''
        # boundary check and move position in other direction if out of bounds
        if self.x_position < self.radius or self.x_position > self.width - self.radius:
            self.x_velocity *= -1
        if self.y_position < self.radius or self.y_position > self.height - self.radius:
            self.y_velocity *= -1

        # increment position
        self.x_position += self.x_velocity
        self.y_position += self.y_velocity

class BallVideoStreamTrack(aiortc.VideoStreamTrack):
    '''
        New stream track that will create a video of a ball bouncing across the screen
    '''
    def __init__(self, velocity: int, radius: int, width, height, ball_location_dict: dict = {}):
        '''
            Initialize variables needed for the stream track. This includes instatiating the grame generator and keeping
            a dictionary for ball location.
        '''
        super().__init__()
        self.velocity = velocity
        self.radius = radius
        self.resolution = (width, height)
        self.frame_generator = FrameGenerator(velocity, radius, width, height)
        self.ball_location_dict = ball_location_dict # key will be frame timestamp, value will be (x,y) tuple
        self.count = 0

    async def recv(self):
        '''
            Generate and return the next frame in the stream
        '''
        pts, time_base = await self.next_timestamp()
        frame = self.frame_generator.get_frame()
        self.frame_generator.increment_position()
        frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
        frame.pts = pts
        frame.time_base = time_base
        self.ball_location_dict[pts] = (self.frame_generator.x_position, self.frame_generator.y_position)
        self.count += 1
        return frame
    

########################################################################################################################
# code for rtc server
# Note, the server will be the offerer
# for callbacks, register using the peer connection object with @pc.on("attribute")
########################################################################################################################

class RTCServer():
    '''
        Base class of an RTCServer that offers a datachannel and a mediastream to a client.
    '''
    def __init__(self, host: str, port: str, stream_track: aiortc.MediaStreamTrack):
        '''
            Initialize host and port that the server will listen on. Also create RTCPeer connection
            and adds a track and a Datachannel.

            args:
                host: host IP address to listen on ex. Host IP, 127.0.0.1 (localhost), or 0.0.0.0 (listen on all addresses)
                port: TCP port to listen to
                stream_track: content that will be served when connected to

            usage order:
                1) create instance of the class
                2) register callback functions
                3) prepare the offer
                4) send the offer
                5) consume signals
        '''
        # initialize what the RTC Server will send and initialize a data channel
        self.host = host
        self.port = port
        self.signal = TcpSocketSignaling(self.host, self.port)
        self.pc = aiortc.RTCPeerConnection()
        self.channel = self.pc.createDataChannel("RTCchannel")
        self.stream_track = stream_track
        self.pc.addTrack(self.stream_track)
        
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
        

class BallVideoRTCServer(RTCServer):
    '''
        Class for an RTCServer that serves a video of a ball bouncing across the screen. If the client sends back
        coordinates, the server will calculate the error in the coordinates and attempt to draw the error using
        cv.imshow().
    '''
    def __init__(self, host: str, port: str, velocity: int, radius: int, width, height):
        self.ball_position = {}
        st = BallVideoStreamTrack(velocity, radius, width, height, self.ball_position)
        super().__init__(host, port, st)

    def calc_rms_error(self, actual: Tuple[int, int], estimated: Tuple[int, int]):
        '''
            Calculates Root Mean Squared Error for an actual point and an estimated point from the client
        '''
        diff = np.array(estimated) - np.array(actual)
        return float(np.sqrt(np.mean(np.square(diff))))

    def show_error_frame(self, actual: Tuple[int, int], estimated: Tuple[int, int]):
        '''
            Draws original ball frame in green with client's estimate on top with
            a red center and outline.
        '''
        resolution = self.stream_track.resolution
        radius = self.stream_track.radius
        frame = np.zeros((resolution[1], resolution[0], 3), dtype='uint8')
        cv.circle(frame, actual, radius=radius, color=(0,255,0), thickness=-1)
        cv.circle(frame, actual, radius=1, color=(255,0,0), thickness=5)
        cv.circle(frame, estimated, radius=1, color=(0,0,255), thickness=5)
        cv.circle(frame, estimated, radius=radius, color=(0,0,255), thickness=3)
        cv.imshow("server", frame)
        cv.waitKey(1)


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
                actual_loc = ball_location_dict[int(values[2])]
                estimated_loc = (int(values[0]), int(values[1]))
                self.show_error_frame(actual_loc, estimated_loc)
                error = self.calc_rms_error(actual_loc, estimated_loc)
                # print(f"time stamp {values[2]}:\n\tactual location: "
                #       f"{actual_loc}\n\testimated location: {estimated_loc}\n\tRMSE: {error}")
                del ball_location_dict[int(values[2])]
            except Exception as e:
                print(e)
        
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

async def main():
    '''
        Entry point into server.py. Gets parameters to run script from command line arguments or environment variables.
        Then it builds a BallVideoRTCServer and runs it.
    '''
    # Server can only have one connection at a time, but the while loop spins up a new server if a disconnection happens
    while True:
        server = BallVideoRTCServer(host='localhost', port='50051', velocity=3, radius=20, width=640, height=480)
        await server.run()
        await server.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
