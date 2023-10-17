import asyncio
from rtcserver import BallVideoRTCServer

async def main():
    '''
        Entry point into server.py. Gets parameters to run script from command line arguments or environment variables.
        Then it builds a BallVideoRTCServer and runs it.
    '''
    # Server can only have one connection at a time, but the while loop spins up a new server if a disconnection happens
    while True:
        server = BallVideoRTCServer(host='localhost', port='50051', velocity=3, radius=20, width=640, height=480)
        await server.run()
        await server.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
