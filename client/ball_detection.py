import ctypes
import multiprocessing as mp
import numpy as np
import cv2 

class POINT(ctypes.Structure):
    '''
        ctypes structure for use in detect_center_proc. stores an x and y point
        for a circle that has been identified. For use in the val ctypes field
        for communicating between main client process and the detect_center_proc
        process.

        To create, use the following code:
        point = POINT(int, int)
    '''
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("time_stamp", ctypes.c_int)
    ]

def detect_center_proc(que: mp.Queue, val: mp.Value, cond: mp.Value):
    '''
        Coroutine to run detect_center function within a process.
        Updates val with estimated center of circle in the frame that was popped from que during the same iteration.
        Waits until main thread has dealt with val to pop another frome from que and start analyzing it 

        inputs:
            que = used to pass frames and timestamps to process
            val = used to pass image center coordinates and corresponding timestamp back to main thread
            cond = condition for whether or not the main thread has dealt with the value in val. 0 nor no it hasn't
    '''
    try:
        while True:
            update_center_values(que, val, cond)
    except Exception as e:
        print("Detect Center Error:", e)
        return
    
def update_center_values(que: mp.Queue, val: mp.Value, cond: mp.Value):
    '''
        This should only be called in detect_center_proc. This was pulled out of the process loop
        in order to write a unit test for it.
        updates values when appropriate
    '''
    if que.qsize() > 0 and cond.value==0:
        with cond.get_lock():
            frame, timestamp = que.get() # get bgr frame from the que
            circles = detect_center(frame)
            if circles is None:
                # if algorithm cant find center of circle, use last estimated position
                val.time_stamp = timestamp
                cond.value = 1
            else:
                # print(circles)
                val.x = int(circles[0])
                val.y = int(circles[1])
                val.time_stamp = timestamp
                cond.value = 1

def detect_center(frame: np.ndarray, dp: float = 6, minDist: float = 8) -> list[int, int, int]:
    '''
        This function estimates the center of a circle in an image using the Hough Transformation
        input:
            frame = ndarray in BGR24 format representing picture
            dp = accumulator matrix scale factor
            minDist = minimum distance between estimated circle centers
        returns:
            list[x,y, r] = (x_coord, y_coord, radius)
        Note: this function needs to be tuned
    '''
    # convert to grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # normally the image would be blurred to reduce noise and make the circles more distinct
    # however, this is a bright circle on a black background, so the circle is as crisp as it
    # gets, no need to blur here

    # apply hough circle tranform to get the estimated center of the circle
    circles = cv2.HoughCircles(gray_frame, cv2.HOUGH_GRADIENT, dp, minDist)
    if circles is not None:
        return circles[0][0]
    return None