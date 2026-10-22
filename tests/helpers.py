import time


def download_request(**overrides) -> dict:
    body = {
        "url": "https://youtu.be/x",
        "format": "mp4",
        "resolution": "720",
        "accepted": True,
    }
    body.update(overrides)
    return body


def wait_for(client, job_id: str) -> dict:
    for _ in range(100):
        state = client.get(f"/api/progress/{job_id}").get_json()
        if state["status"] in ("completato", "errore"):
            return state
        time.sleep(0.03)
    return state
