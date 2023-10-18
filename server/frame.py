import cv2 as cv
import numpy as np

class Frame():
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
        cv.circle(frame, (self.x_position, self.y_position), radius = self.radius, thickness = -1, color = (0, 0, 255)) 
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
