from urllib.request import Request, urlopen


def run_job(job_config: dict, api_config: dict) -> None:
    job_id = job_config["id"]
    name = job_config["name"]
    url = job_config["url"]
    method = job_config.get("method", "GET")
    timeout = api_config.get("timeout_seconds", 30)

    print(f"[{job_id}] Starting: {name}", flush=True)
    print(f"[{job_id}] {method} {url}", flush=True)

    request = Request(
        url,
        method=method,
        headers={
            "User-Agent": "time-controlled-queries-demo/1.0"
        },
    )

    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")

        print(
            f"[{job_id}] HTTP {response.status}",
            flush=True,
        )
        print(
            f"[{job_id}] Response: {body}",
            flush=True,
        )

    print(f"[{job_id}] Completed", flush=True)