import cv2 as cv
import numpy as np


class Frame():
    '''
    Generate frames of ball bouncing across the screen
    '''
    def __init__(self, velocity: int = 5, radius: int = 40, width = 640, height = 480):
        '''
        param radius:       ball radius
        param width:        frame width
        param height:       frame height
        param x_position:   position of ball on x-axis
        param y_position:   position of ball on y-axis
        param x_velocity:   velocity of ball on x-axis
        param x_velocity:   velocity of ball on y-axis
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
    
    def ball_move(self):
        '''
        move ball and modify positional parameters
        '''
        # bounce when collision with frame edge happens
        if self.x_position < self.radius or self.x_position > self.width - self.radius:
            self.x_velocity *= -1
        if self.y_position < self.radius or self.y_position > self.height - self.radius:
            self.y_velocity *= -1

        # modify position
        self.x_position += self.x_velocity
        self.y_position += self.y_velocity
