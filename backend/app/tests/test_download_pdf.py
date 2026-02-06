import asyncio
import pytest

@pytest.mark.anyio
async def test_download_pdf(client):
    fake_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    files = {"resume": ("test.pdf", fake_pdf, "application/pdf")}
    data = {"job_description": "AWS Terraform Kubernetes GitHub Actions"}

    r = await client.post("/api/analyze", files=files, data=data)
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    # wait until done
    for _ in range(30):
        s = await client.get(f"/api/status/{job_id}")
        if s.json()["state"] == "done":
            break
        await asyncio.sleep(0.3)

    d = await client.get(f"/api/download/{job_id}")
    assert d.status_code == 200
    assert d.headers["content-type"].startswith("application/pdf")
    assert len(d.content) > 50
