import httpx
import asyncio

async def test_speed(host: str, timeout=5) -> float:
    """
    Perform a simple HTTP GET request to measure server latency.
    Returns latency in seconds or infinity if the host is unreachable.
    """
    if not host:
        return float('inf')
    url = f"http://{host}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            import time
            start = time.monotonic()
            r = await client.get(url)
            if r.status_code == 200:
                end = time.monotonic()
                return end - start
            return float('inf')
    except Exception:
        return float('inf')
