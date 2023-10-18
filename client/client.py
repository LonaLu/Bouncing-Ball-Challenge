import asyncio
from rtc_client import RTCClient

async def main():
    '''
        Entry point into client.py. Gets arguments to run script from command line or environment variables.
        Then it builds a client and runs it
    '''
    # build client and run it
    client = RTCClient(host='localhost', port=50051)
    await client.run()

if __name__ == "__main__":
    # run client in an event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Key interrupt")
