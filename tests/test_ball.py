import numpy as np
import cv2
import pytest
from client.ball_detection import *
import multiprocessing as mp
from unittest import mock
from server.frame import *

@pytest.fixture
def frame():
    frame = Frame(5, 40, 100, 100)
    return frame

@pytest.mark.server
def test_frame_initialization(frame):
    assert frame.x_position == 40
    assert frame.y_position == 40
    assert frame.x_velocity == 5
    assert frame.y_velocity == 5

@pytest.mark.server
def test_ball_move(frame):
    frame.ball_move()
    assert frame.x_velocity == 5
    assert frame.y_velocity == 5
    assert frame.x_position == 45
    assert frame.y_position == 45

@pytest.mark.server
def test_ball_move_bounce_wall(frame):
    for _ in range(10):
        frame.ball_move()
    assert frame.x_velocity == -5
    assert frame.y_velocity == -5
    assert frame.x_position == 40
    assert frame.y_position == 40

@pytest.mark.client
def test_detect_center():

    '''
        Tests whether or not find center returns coordinates within 10 euclidean distance pixels from the actual center
    '''
    center = (400, 250)
    frame = np.zeros((480,640,3), dtype='uint8')
    frame = cv2.circle(frame, center, 20, (0,0,255))
    detected_circle = detect_center(frame)[0:2]
    error = np.linalg.norm(np.array(center) - np.array(detected_circle))
    assert error < 3

@pytest.fixture
def mp_params():
    que = mp.Queue()
    que.qsize = mock.Mock(return_value=1)
    que.get = mock.Mock(return_value=(1,1))
    val = mp.Value(POINT)
    val.x = 1
    val.y = 1
    val.time_stamp = -1
    cond = mp.Value(ctypes.c_int)
    cond.value = 0
    return (que, val, cond)

@pytest.mark.client
def test_update_center_values_return_none(mp_params):
    '''
        Tests that the detect_center_proc()
    '''
    que, val, cond = mp_params
    x = val.x
    y = val.y
    
    # test that values stay the same when detect_center returns None
    with mock.patch('client.ball_detection.detect_center', return_value = None, autospec=True):
        update_center_values(que, val, cond)
    
    assert val.x == x
    assert val.y == y
    assert val.time_stamp == 1
    assert cond.value == 1

@pytest.mark.client
def test_update_center_values_return_values(mp_params):
    # test that values get updated when detect_center returns a tuple
    que, val, cond = mp_params
    x = 5
    y = 5
    with mock.patch('client.ball_detection.detect_center', return_value = (x,y,1), autospec=True):
        update_center_values(que, val, cond)
    
    assert val.x == x
    assert val.y == y
    assert val.time_stamp == 1
    assert cond.value == 1

@pytest.mark.client
def test_update_center_values_no_update(mp_params):
    que, val, cond = mp_params
    x = val.x
    y = val.y
    cond.val = 1
    # test that nothing gets updated because cond value==1
    with mock.patch('client.ball_detection.detect_center', return_value = (1,1,1), autospec=True):
        update_center_values(que, val, cond)
    
    assert val.x == x
    assert val.y == y
    assert val.time_stamp == 1
    assert cond.value == 1








