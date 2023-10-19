import cv2
import numpy as np
import aiortc
from aiortc.contrib.signaling import TcpSocketSignaling, BYE
import ctypes
import multiprocessing as mp
from ball_detection import POINT, detect_center_proc


class RTCClient():
    '''
    RTCClient receives frames from the server, determines location of the ball, and sends location back to server
    '''

    def __init__(self, host: str, port: str):
        '''
        Initialze values and start process for analyzing frames

        param _proc_value:  estimated ball center location 
        param _proc_que:    queue for sending frames
        param _proc_cond:   whether value is processed
        '''
        self.signal: TcpSocketSignaling = TcpSocketSignaling(host, port)
        self.pc = aiortc.RTCPeerConnection()
        self.channel = None
        self.track = None
        self._m = mp.Manager()
        self._proc_que = self._m.Queue()
        self._proc_value = mp.Value(POINT, lock=False) 
        self._proc_cond = mp.Value(ctypes.c_int, lock=True)
        self._proc_value.x = -1
        self._proc_value.y = -1
        self._proc_value.time_stamp = -1
        self._proc_cond.value = 0
        self._frame_proc = mp.Process(target=detect_center_proc, args=(
            self._proc_que,
            self._proc_value,
            self._proc_cond
        ))
        self._frame_proc.start()

    async def register_on_callbacks(self):
        '''
        Register callbacks when an RTC event happens.
        '''
        @self.pc.on("datachannel")
        def on_datachannel(chan: aiortc.RTCDataChannel):
            #When a data channel is connected, set self.channel to this channel
            print("channel connected")
            self.channel = chan
        
        @self.pc.on("track")
        def on_track(track: aiortc.MediaStreamTrack):
            # When a track is connected, set self.track to track
            print("track connected")
            self.track = track

        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            # Log details about connection state. If connection fails, just exit program
            print(f"connection state is {self.pc.connectionState}")
            if self.pc.connectionState == "failed":
                await self.pc.close()
                exit(-1)
     
    def show_frame(self, ndarr_frame: np.ndarray):
        '''
        print frame in bgr format
        '''
        cv2.imshow('client', ndarr_frame)
        cv2.waitKey(1)

    async def _run_track(self) -> bool:
        '''
        Get the next frame from the track
        '''
        try:
            frame = await self.track.recv()
        except aiortc.mediastreams.MediaStreamError as e:
            print("Run Track Error:", e)
            return False
        
        time_stamp = frame.pts
        ndarr_frame = frame.to_ndarray()
        ndarr_frame = cv2.cvtColor(ndarr_frame, cv2.COLOR_YUV2BGR_I420)
        self._proc_que.put((ndarr_frame, time_stamp))
        self.show_frame(ndarr_frame)
        
        with self._proc_cond.get_lock():
            if self._proc_cond.value == 1:
                self.channel.send(f'{self._proc_value.x}\t{self._proc_value.y}\t{self._proc_value.time_stamp}')
                self._proc_cond.value = 0
        return True
    
    async def run(self):
        '''
        Run client
        '''
        await self.register_on_callbacks()
        while await self.consume_signal():
            if self.track is not None:
                while await self._run_track():
                    pass
        #When connection stops, end client process
        await self.shutdown()
    
    async def shutdown(self):
        '''
        Shut down client, kill process
        '''
        self._frame_proc.kill()
    
    def __del__(self):
        '''
        Kill process when destructor is called
        '''
        self._frame_proc.kill()

    async def consume_signal(self) ->bool:
        '''
        Wait for a signal response through a tcp connection.

        If the data recieved through the signal is an ICE Candidate or and SDP offer/answer,
        handle that case and return True. 
        If signal was an sdp offer, create an answer and send it
        '''
        obj = None
        while True:
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