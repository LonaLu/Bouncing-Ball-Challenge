import aiortc
from frame import Frame
import av


class BallBouncingTrack(aiortc.VideoStreamTrack):
    '''
    Ball Bouncing Video Stream Track
    '''
    def __init__(self, velocity: int, radius: int, width: int, height: int, ball_location_dict: dict = {}):
        '''
        param velocity:             ball moving velocity in both x and y axis
        param radius:               ball radius
        param width:                frame width
        param height:               frame height
        param frame_generator:      generator of ball bouncing video frames
        param ball_location_dict:   dictionary to store ball locations {timestamp: (x_position, y_position)}
        '''
        super().__init__()
        self.velocity = velocity
        self.radius = radius
        self.width = width
        self.height = height
        self.frame_generator = Frame(velocity, radius, width, height)
        self.ball_location_dict = ball_location_dict

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
    