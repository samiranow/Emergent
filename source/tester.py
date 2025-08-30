# tester.py
import asyncio
import httpx
import logging

async def test_speed(host: str, country_nodes: list[str] = None, timeout=10) -> float:
    """
    Measure host latency using check-host.net API.
    If country_nodes is provided, filter results to those nodes.
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

            # 2️⃣ Wait with loop check
            for _ in range(10):  # Max 20 seconds
                await asyncio.sleep(2)
                r2 = await client.get(f"{base_url}/check-result/{request_id}", headers={"Accept": "application/json"})
                if r2.status_code == 200:
                    results = r2.json()
                    if results:  # If results are available
                        break
            else:
                return float('inf')

            # 3️⃣ Parse results and calculate average latency, filtered by country_nodes
            latencies = []
            for node, node_results in results.items():
                if country_nodes and node not in country_nodes:
                    continue
                if not node_results:
                    continue
                try:
                    node_results_list = node_results[0]  # first inner list
                    for entry in node_results_list:
                        if entry and entry[0] == "OK":
                            latencies.append(entry[1])
                except Exception:
                    continue

            if not latencies:
                return float('inf')

            return sum(latencies) / len(latencies)

        except Exception as e:
            logging.error(f"Ping test error for {host}: {e}")
            return float('inf')

async def get_nodes_by_country() -> dict[str, list[str]]:
    """
    Returns a dictionary mapping country codes to list of hostnames (nodes) in that country.
    """
    url = "https://check-host.net/nodes/hosts"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logging.error(f"Error fetching nodes: {e}")
            return {}

    country_nodes = {}
    nodes = data.get("nodes", {})
    for node, info in nodes.items():
        try:
            location = info.get("location", [])
            if isinstance(location, list) and len(location) >= 1:
                country_code = str(location[0]).lower()
                country_nodes.setdefault(country_code, []).append(node)
        except Exception:
            continue
    return country_nodes
