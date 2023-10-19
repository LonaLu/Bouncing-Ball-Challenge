import numpy as np
import multiprocessing as mp
import cv2
import pytest
from client.ball_detection import *
from unittest import mock
from server.frame import *


@pytest.fixture
def frame():
    '''
    fixture for initialzing frame server side
    '''
    frame = Frame(5, 40, 100, 100)
    return frame


@pytest.mark.server
def test_frame_initialization(frame):
    '''
    test initial position and velocity of ball
    '''
    assert frame.x_position == 40
    assert frame.y_position == 40
    assert frame.x_velocity == 5
    assert frame.y_velocity == 5

@pytest.mark.server
def test_ball_move(frame):
    '''
    test position and velocity of ball after movement
    '''
    frame.ball_move()
    assert frame.x_velocity == 5
    assert frame.y_velocity == 5
    assert frame.x_position == 45
    assert frame.y_position == 45

@pytest.mark.server
def test_ball_move_bounce_wall(frame):
    '''
    test position and velocity of ball after bouncing from frame edge
    '''
    for _ in range(10):
        frame.ball_move()
    assert frame.x_velocity == -5
    assert frame.y_velocity == -5
    assert frame.x_position == 40
    assert frame.y_position == 40

@pytest.mark.client
def test_detect_center():
    '''
    Test detect center returns a result with an error smaller than 3
    '''
    center = (400, 250)
    frame = np.zeros((480,640,3), dtype='uint8')
    frame = cv2.circle(frame, center, 20, (0,0,255))
    detected_circle = detect_center(frame)[0:2]
    error = np.linalg.norm(np.array(center) - np.array(detected_circle))
    assert error < 3

@pytest.fixture
def mp_params():
    '''
    fixture for initialzing params from process on client side
    '''
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
    Test values stay the same when detect_center returns None
    '''
    que, val, cond = mp_params
    x = val.x
    y = val.y
    with mock.patch('client.ball_detection.detect_center', return_value = None, autospec=True):
        update_center_values(que, val, cond)
    
    assert val.x == x
    assert val.y == y
    assert val.time_stamp == 1
    assert cond.value == 1

@pytest.mark.client
def test_update_center_values_return_values(mp_params):
    '''
    Test values get updated when detect_center returns actual values
    '''
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
    '''
    Test values stay the same when condition equals 1
    '''
    que, val, cond = mp_params
    x = val.x
    y = val.y
    cond.val = 1
    with mock.patch('client.ball_detection.detect_center', return_value = (1,1,1), autospec=True):
        update_center_values(que, val, cond)
    
    assert val.x == x
    assert val.y == y
    assert val.time_stamp == 1
    assert cond.value == 1








