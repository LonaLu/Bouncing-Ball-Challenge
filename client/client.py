import cv2 as cv
import numpy as np
import asyncio
import ctypes
import multiprocessing as multi
from rtc_client import RTCClient

########################################################################################################################
# code for detecting where ball is
########################################################################################################################

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

def detect_center(frame: np.ndarray, dp: float = 6, minDist: float = 5) -> list[int, int, int]:
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
    gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    # normally the image would be blurred to reduce noise and make the circles more distinct
    # however, this is a bright circle on a black background, so the circle is as crisp as it
    # gets, no need to blur here

    # apply hough circle tranform to get the estimated center of the circle
    num_rows = gray_frame.shape[0]
    circles = cv.HoughCircles(gray_frame, cv.HOUGH_GRADIENT, dp=dp, minDist=minDist)
    if circles is not None:
        return circles[0][0]
    return None


def update_center_values(que: multi.Queue, val: multi.Value, cond: multi.Value, dp: float = 6, minDist: float = 5):
    '''
        This should only be called in detect_center_proc. This was pulled out of the process loop
        in order to write a unit test for it.
        updates values when appropriate
    '''
    if que.qsize() > 0 and cond.value==0:
        with cond.get_lock():
            frame, timestamp = que.get() # get bgr frame from the que
            circles = detect_center(frame, dp, minDist)
            if circles is None:
                # if algorithm cant find center of circle, use last estimated position
                print(f"skipped frame at timestamp {timestamp}")
                val.time_stamp = timestamp
                cond.value = 1
            else:
                # print(circles)
                val.x = int(circles[0])
                val.y = int(circles[1])
                val.time_stamp = timestamp
                cond.value = 1

def detect_center_proc(que: multi.Queue, val: multi.Value, cond: multi.Value, dp: float = 6, minDist: float = 5):
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
            update_center_values(que, val, cond, dp, minDist)
    except Exception as e:
        return


########################################################################################################################
# code for rtc client
########################################################################################################################


async def main():
    '''
        Entry point into client.py. Gets arguments to run script from command line or environment variables.
        Then it builds a client and runs it
    '''
    dp = 6
    minDist = 8
    host = 'localhost'
    port = 50051
    display = 'display'

    print(f"connecting to: {host}:{port}")
    # build client and run it
    client = RTCClient(host, port, display=display, dp=dp, minDist=minDist)
    await client.run()


if __name__ == "__main__":
    # run client in an event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Key interrupt")
