# Bouncing Ball Project
Code for Nimble Programming Chanllenge by Lona Lu

## Setting Up the Environment
```pip install -r requirements.txt```

## How to Run Project
Run following commands from the root directory
1. ```python client/client.py```  
2. ```python server/server.py```  

## How to Run Tests
Run following commands from the root directory:
```pytest``` 

Run tests for client:
```pytest -m client``` 

Run tests for server:
```pytest -m server``` 

## Build Docker Images
For client and server: <br />
```docker build -f client/Dockerfile -t client .```
```docker build -f server/Dockerfile -t server .```

## Requirements Pointer
1. Run ```python server/server.py```
2. Run ```python client/client.py```
3. client/rtc_client.py and server/rtc_server.py<br />
    a. ```RTCServer.run()```<br />
    b.```RTCClient.consume_signal()```
4. Video displayed when running project (source code: server/rtc_server.py)
5. server/ball_bouncing_track.py
6. ```RTCClient.show_frame()```
7. ```RTCClient.__init__()```
8. client/ball_dectection.update_center_values
9. client/ball_dectection.detect_center
10. client/ball_dectection.update_center_values
11. ```RTCClient._run_track()```
12. ```RTCServer.display_frame()``` and ```RTCServer.calculate_error```, see server side log for numerical error
13. See comments in files
14. test/test_ball.py, see pytest instructions above 
15. README
16. See video in zip file
17. See zip file
18. See docker instructions above 
19. Don't have time for that, sorry :(