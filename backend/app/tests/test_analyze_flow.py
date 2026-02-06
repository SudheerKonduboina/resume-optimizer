import asyncio
import pytest

@pytest.mark.anyio
async def test_analyze_status_result_flow(client):
    # Use a tiny DOCX-free test by sending a fake PDF bytes.
    # Your parser may fail if it's not a real PDF. So we make a minimal PDF header.
    fake_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

    files = {"resume": ("test.pdf", fake_pdf, "application/pdf")}
    data = {"job_description": "Looking for AWS Terraform Kubernetes GitHub Actions DevOps"}

    r = await client.post("/api/analyze", files=files, data=data)
    # If your parser needs a real PDF, this might 400/500.
    # In that case, replace fake_pdf with a real sample PDF in tests/assets.
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]
    assert job_id

    # poll until done (max ~10s)
    for _ in range(30):
        s = await client.get(f"/api/status/{job_id}")
        assert s.status_code == 200
        state = s.json()["state"]
        if state == "done":
            break
        if state == "error":
            pytest.fail(f"Job failed: {s.json()}")
        await asyncio.sleep(0.3)

    res = await client.get(f"/api/result/{job_id}")
    assert res.status_code == 200
    payload = res.json()

    assert payload["job_id"] == job_id
    assert "scores" in payload
    assert "keyword_analysis" in payload
    assert "formatting_flags" in payload
    assert "suggestions" in payload
