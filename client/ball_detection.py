import ctypes
import multiprocessing as mp
import numpy as np
import cv2 

class POINT(ctypes.Structure):
    '''
    Stores the position of ball and the corresponding timestamp.

    param x:            position on x-axis of the ball
    param y:            position on y-axis of the ball
    param time_stamp:   corresponding timestamp
    '''
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("time_stamp", ctypes.c_int)
    ]

def detect_center_proc(que: mp.Queue, val: mp.Value, cond: mp.Value):
    '''
    Run detect_center function in a process. Continously update estimated ball center for frames in que

    param que:  used to pass frames and timestamps to process
    param val:  used to pass image center coordinates and corresponding timestamp back to main thread
    param cond: whether main thread has dealt with the value in val.
    '''
    try:
        while True:
            update_center_values(que, val, cond)
    except Exception as e:
        print("Detect Center Error:", e)
        return
    
def update_center_values(que: mp.Queue, val: mp.Value, cond: mp.Value):
    '''
    Update estimated ball center for frames

    param que:  used to pass frames and timestamps to process
    param val:  used to pass image center coordinates and corresponding timestamp back to main thread
    param cond: whether main thread has dealt with the value in val.
    '''
    if que.qsize() > 0 and cond.value==0:
        with cond.get_lock():
            frame, timestamp = que.get()
            circles = detect_center(frame)

             # if detection fails, use last estimated position
            if circles is None:
                val.time_stamp = timestamp
                cond.value = 1
            else:
                val.x = int(circles[0])
                val.y = int(circles[1])
                val.time_stamp = timestamp
                cond.value = 1

def detect_center(frame: np.ndarray, dp: float = 6, minDist: float = 8) -> list[int, int, int]:
    '''
    Detect and esitimate the center of a ball in an image using the Hough Transformation.

    return:         list [x_position, y_position, radius]
    param frame:    ndarray in BGR24 format representing picture
    param dp:       accumulator matrix scale factor
    param minDist:  minimum distance between estimated ball centers
    '''
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray_frame, cv2.HOUGH_GRADIENT, dp, minDist)
    if circles is not None:
        return circles[0][0]
    return None