import asyncio
import httpx

async def test_speed(host: str, timeout=10) -> float:
    """
    Measure host latency using check-host.net API.
    Returns average ping in seconds or infinity if unreachable.
    """
    if not host:
        return float('inf')

    base_url = "https://check-host.net"
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            # 1️⃣ Start ping test
            r = await client.get(f"{base_url}/check-ping", params={"host": host}, headers={"Accept": "application/json"})
            r.raise_for_status()
            data = r.json()
            request_id = data.get("request_id")
            if not request_id:
                return float('inf')

            # 2️⃣ Wait a few seconds for nodes to finish
            await asyncio.sleep(10)

            # 3️⃣ Get results
            r2 = await client.get(f"{base_url}/check-result/{request_id}", headers={"Accept": "application/json"})
            r2.raise_for_status()
            results = r2.json()

            # 4️⃣ Parse results and calculate average latency
            latencies = []
            for node, node_results in results.items():
                if not node_results:
                    continue
                # node_results is a list of lists, take first inner list
                try:
                    node_results_list = node_results[0]
                    for entry in node_results_list:
                        # entry format: ["OK", 0.044, "94.242.206.94"]
                        if entry and entry[0] == "OK":
                            latencies.append(entry[1])
                except Exception:
                    continue

            if not latencies:
                return float('inf')

            return sum(latencies) / len(latencies)

        except Exception:
            return float('inf')
