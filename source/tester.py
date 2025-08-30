import asyncio
import httpx
import logging

async def run_ping_once(host: str, timeout=10) -> dict:
    """Send a single ping request and return full results."""
    if not host:
        return {}

    base_url = "https://check-host.net"
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(f"{base_url}/check-ping", params={"host": host}, headers={"Accept": "application/json"})
            r.raise_for_status()
            request_id = r.json().get("request_id")
            if not request_id:
                return {}

            for _ in range(10):
                await asyncio.sleep(2)
                r2 = await client.get(f"{base_url}/check-result/{request_id}", headers={"Accept": "application/json"})
                if r2.status_code == 200:
                    results = r2.json()
                    if results:
                        return results
            return {}
        except Exception as e:
            logging.error(f"Ping error for {host}: {e}")
            return {}

def extract_latency_by_country(results: dict, country_nodes: dict[str, list[str]]) -> dict[str, float]:
    """Extract average latency per country from ping results."""
    country_latencies = {}
    for country, nodes in country_nodes.items():
        latencies = []
        for node in nodes:
            node_results = results.get(node)
            if not node_results:
                continue
            try:
                for entry in node_results[0]:
                    if entry and entry[0] == "OK":
                        latencies.append(entry[1])
            except Exception:
                continue
        country_latencies[country] = sum(latencies) / len(latencies) if latencies else float('inf')
    return country_latencies

async def get_nodes_by_country() -> dict[str, list[str]]:
    """Returns a dictionary mapping country codes to list of hostnames (nodes) in that country."""
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
