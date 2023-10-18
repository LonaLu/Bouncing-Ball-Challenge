import aiortc
from frame import Frame
import av

class BallBouncingTrack(aiortc.VideoStreamTrack):
    '''
        New stream track that will create a video of a ball bouncing across the screen
    '''
    def __init__(self, velocity: int, radius: int, width: int, height: int, ball_location_dict: dict = {}):
        '''
            Initialize variables needed for the stream track. This includes instatiating the grame generator and keeping
            a dictionary for ball location.
        '''
        super().__init__()
        self.velocity = velocity
        self.radius = radius
        self.width = width
        self.height = height
        self.frame_generator = Frame(velocity, radius, width, height)
        self.ball_location_dict = ball_location_dict # key will be frame timestamp, value will be (x,y) tuple

    async def recv(self):
        '''
            Generate and return the next frame in the stream
        '''
        pts, time_base = await self.next_timestamp()
        frame = self.frame_generator.get_frame()
        self.frame_generator.ball_move()
        self.ball_location_dict[pts] = (self.frame_generator.x_position, self.frame_generator.y_position)
        frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
        frame.pts = pts
        frame.time_base = time_base
        return frame
    