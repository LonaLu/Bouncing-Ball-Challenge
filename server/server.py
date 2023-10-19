import asyncio
from rtc_server import RTCServer

async def main():
    '''
    Build and run server
    '''
    while True:
        server = RTCServer(host='localhost', port='12345', velocity=5, radius=17, width=300, height=200)
        await server.run()
        await server.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
