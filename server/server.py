import asyncio
from rtc_server import RTCServer

async def main():
    '''
    Build and run server
    '''
    # Server can only have one connection at a time, but the while loop spins up a new server if a disconnection happens
    while True:
        server = RTCServer(host='localhost', port='50051', velocity=3, radius=20, width=640, height=480)
        await server.run()
        await server.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
