"""
Why are websockets not connecting over WAN
this is highly distressing
"""
import asyncio
import websockets


async def main():
    ws = await websockets.connect('ws://18.191.184.86:8000/ping')
    print('I connected *shrug*')


if __name__ == "__main__":
    asyncio.run(main())
