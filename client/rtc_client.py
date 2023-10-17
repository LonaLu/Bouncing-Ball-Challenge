import cv2
import numpy as np
import aiortc
from aiortc.contrib.signaling import TcpSocketSignaling, BYE
import ctypes
import multiprocessing as mp
from ball_detection import POINT, detect_center_proc

class RTCClient():
    '''
        An RTCClient meant to consume a BallVideoStreamTrack (defined in server), process the frame, and
        eventually send back an estimated center of the ball from the consumed frame.
    '''
    def __init__(self, host: str, port: str, display: bool = False, dp: float= 6, minDist: float = 5):
        '''
            Initializes values needed and also starts _frame_proc process for analyzing frames.
           _proc_value.x represents the extimated x coordinate of the circle from the last analyzed frame
           _proc_value.y is the same as x but for the y coordinate
           _proc_que is used to send frames _frame_proc 
        '''
        self.signal: TcpSocketSignaling = TcpSocketSignaling(host, port)
        self.pc = aiortc.RTCPeerConnection()
        self.channel: aiortc.RTCDataChannel = None
        self.track: aiortc.MediaStreamTrack = None
        self._m = mp.Manager()
        self._proc_que = self._m.Queue()
        self._proc_value = mp.Value(POINT, lock=False)   # don't need a lock because there's only 1 writer and 1 reader. read/writes are synced as well
        self._proc_cond = mp.Value(ctypes.c_int, lock=True)
        self._proc_value.x = -1
        self._proc_value.y = -1
        self._proc_value.time_stamp = -1
        self._proc_cond.value = 0
        self._frame_proc = mp.Process(target=detect_center_proc, args=(
            self._proc_que,
            self._proc_value,
            self._proc_cond,
            dp,
            minDist
        ))
        self._frame_proc.start()
        self.display = display


    async def register_on_callbacks(self):
        '''
            Register callbacks when an RTC event happens.
            This client handles two events:
                1) on track event - set track to self.track
                2) on datachannel event - set channel to self.channel
                3) on connectionstatechange event - exit if connection is dropped
        '''
        @self.pc.on("datachannel")
        def on_datachannel(chan: aiortc.RTCDataChannel):
            '''
                When a data channel is connected, set self.channel to this channel
            '''
            print("channel connected")
            self.channel = chan
            chan.send("hi")
        
        @self.pc.on("track")
        def on_track(track: aiortc.MediaStreamTrack):
            '''
                When a track is connected, set self.track to track
            '''
            print("track connected")
            self.track = track

        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            '''
                Log details about connection state. If connection fails, just exit program
            '''
            print(f"connection state is {self.pc.connectionState}")
            if self.pc.connectionState == "failed":
                await self.pc.close()
                exit(-1)

     
    def show_frame(self, ndarr_frame: np.ndarray):
        '''
            print aframe in bgr format if self.display is set to True.
        '''
        if self.display:
            cv2.imshow('client', ndarr_frame)
            cv2.waitKey(1)


    async def _run_track(self) -> bool:
        '''
            Attempts to get the next frame from the track
        '''
        try:
            frame = await self.track.recv()
        except aiortc.mediastreams.MediaStreamError as e:
            print(e)
            print("run track returning false")
            return False
        
        time_stamp = frame.pts
        ndarr_frame = frame.to_ndarray()
        ndarr_frame = cv2.cvtColor(ndarr_frame, cv2.COLOR_YUV2BGR_I420)
        self._proc_que.put((ndarr_frame, time_stamp))
        self.show_frame(ndarr_frame)
        
        with self._proc_cond.get_lock():
            if self._proc_cond.value == 1:
                # deal with processed frame aka send it over to server
                # send server the estimated values of the center of circle with the timestamp for it as well
                self.channel.send(f'{self._proc_value.x}\t{self._proc_value.y}\t{self._proc_value.time_stamp}')
                self._proc_cond.value = 0
            else:
                # continue processing stream
                pass
        return True
    
    
    async def run(self):
        '''
            Method to run server.
            
            Registers callbacks, then calls consume signal. Once WebRTC has done its thing and there's a peer 
            to peer connection, the track being served starts to get consumed and keeps getting consumed.
            When consumption stops due to connection ending, call shutdown and end the client process
        '''

        await self.register_on_callbacks()
        while await self.consume_signal():
            print("still consuming")
            if self.track is not None:
                while await self._run_track():
                    pass
        await self.shutdown()
    

    async def shutdown(self):
        '''
            Method to shut down client. Makes sure frame analysis process is killed
        '''
        self._frame_proc.kill()
    

    def __del__(self):
        '''
            make sure frame analysis process gets killed when destructor is called
        '''
        self._frame_proc.kill()

    async def consume_signal(self) ->bool:
        '''
            waits for a signal response through a tcp connection.

            If the data recieved through the signal is an ICE Candidate or and SDP offer/answer,
            handle that case and return True. If signal was an sdp offer, create an answer and send it

            If not Returns False
        '''
        obj = None
        while True:
            # wait for a connection to the server. If the server is not running, 
            # receive will result in an exception, so keep eating the
            try:
                obj = await self.signal.receive()
                break
            except (FileNotFoundError, OSError):
                pass

        if isinstance(obj, aiortc.RTCSessionDescription):
            await self.pc.setRemoteDescription(obj)
            if obj.type == "offer":
                print("received offer")
                await self.pc.setLocalDescription(await self.pc.createAnswer())
                await self.signal.send(self.pc.localDescription)
            return True
        elif isinstance(obj, aiortc.RTCIceCandidate):
            print("got ICE candidate")
            await self.pc.addIceCandidate(obj)
            return True
        if obj is BYE:
            print("goodbye")
        
        return False