"""
asyncio utilities
"""
import asyncio


def async_partial(f, *args):
    """
    https://stackoverflow.com/questions/52422860/
    partial-asynchronous-functions-are-not-detected-as-asynchronous
    """
    async def f2(*args2):
        result = f(*args, *args2)
        if asyncio.iscoroutinefunction(f):
            result = await result
        return result

    return f2
