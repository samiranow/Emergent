import asyncio
import httpx

async def get_nodes_by_country() -> dict[str, list[str]]:
    url = "https://check-host.net/nodes/hosts"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
    country_nodes = {}
    for node, info in data.items():
        country_code = info[0]
        country_nodes.setdefault(country_code.lower(), []).append(node)
    return country_nodes

async def test_speed_country(host: str, country_code: str, country_nodes: dict[str, list[str]], timeout=10) -> float:
    if not host or country_code.lower() not in country_nodes:
        return float('inf')

    nodes_to_use = country_nodes[country_code.lower()]
    base_url = "https://check-host.net"

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(f"{base_url}/check-ping", params={"host": host}, headers={"Accept": "application/json"})
            r.raise_for_status()
            request_id = r.json().get("request_id")
            if not request_id:
                return float('inf')

            await asyncio.sleep(10)

            r2 = await client.get(f"{base_url}/check-result/{request_id}", headers={"Accept": "application/json"})
            r2.raise_for_status()
            results = r2.json()

            latencies = []
            for node in nodes_to_use:
                node_results = results.get(node)
                if not node_results:
                    continue
                try:
                    node_results_list = node_results[0]
                    for entry in node_results_list:
                        if entry and entry[0] == "OK":
                            latencies.append(entry[1])
                except Exception:
                    continue

            if not latencies:
                return float('inf')
            return sum(latencies) / len(latencies)

        except Exception:
            return float('inf')
