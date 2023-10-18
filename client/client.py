import asyncio
from rtc_client import RTCClient

async def main():
    '''
    Build and run client
    '''
    client = RTCClient(host='localhost', port=50051)
    await client.run()

if __name__ == "__main__":
    # run client in an event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Key interrupt")
