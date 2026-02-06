from __future__ import annotations
from typing import Dict, Any
from datetime import datetime

def render_html_report(payload: Dict[str, Any]) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    scores = payload["scores"]
    kw = payload["keyword_analysis"]
    fmt = payload["formatting_flags"]
    sugg = payload["suggestions"]["items"]

    missing = kw.get("missing", [])
    present = kw.get("present", [])

    def li(items):
        return "".join([f"<li>{x}</li>" for x in items]) if items else "<li>—</li>"

    cards = ""
    for s in sugg:
        cards += f"""
        <div class="card">
          <div class="tag">{s["type"].upper()}</div>
          <div class="title">{s["title"]}</div>
          <div class="detail">{s["detail"]}</div>
        </div>
        """

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>ATS Report</title>
  <style>
    body {{
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      background: #070A12;
      color: #E7E9EE;
      margin: 0; padding: 24px;
    }}
    .wrap {{ max-width: 980px; margin: 0 auto; }}
    .hero {{
      background: radial-gradient(900px 300px at 10% 0%, rgba(212,175,55,0.18), transparent 60%),
                  radial-gradient(900px 300px at 90% 0%, rgba(0,208,132,0.16), transparent 60%),
                  #0B0F1A;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 18px;
      padding: 18px 18px;
    }}
    .row {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 14px; margin-top: 14px; }}
    .panel {{
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 16px;
      padding: 14px;
    }}
    .kpi {{ font-size: 34px; font-weight: 800; letter-spacing: -0.02em; }}
    .muted {{ color: rgba(231,233,238,0.7); font-size: 13px; }}
    .gold {{ color: #D4AF37; }}
    .emerald {{ color: #00D084; }}
    .grid3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }}
    .pill {{ padding: 8px 10px; border-radius: 999px; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.15); font-size: 13px; }}
    .card {{
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 16px;
      padding: 12px;
      margin-bottom: 10px;
    }}
    .tag {{
      display: inline-block;
      font-size: 11px;
      padding: 4px 8px;
      border-radius: 999px;
      border: 1px solid rgba(212,175,55,0.35);
      color: #D4AF37;
      background: rgba(212,175,55,0.08);
      margin-bottom: 6px;
    }}
    .title {{ font-weight: 700; margin-bottom: 4px; }}
    .detail {{ color: rgba(231,233,238,0.75); font-size: 13px; line-height: 1.4; }}
    ul {{ margin: 8px 0 0 18px; }}
    a {{ color: #D4AF37; }}
    @media (max-width: 820px) {{
      .row {{ grid-template-columns: 1fr; }}
      .grid3 {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div class="muted">Generated: {now}</div>
      <h1 style="margin:8px 0 0; font-size: 22px;">ATS Compatibility Report</h1>
      <div class="muted">Filename: {payload["filename"]}</div>
    </div>

    <div class="row">
      <div class="panel">
        <div class="muted">Overall ATS Score</div>
        <div class="kpi"><span class="gold">{scores["total"]}</span><span class="muted"> / 100</span></div>
        <div class="grid3">
          <div class="pill">Keywords: <span class="gold">{scores["breakdown"]["keywords"]}</span>/45</div>
          <div class="pill">Formatting: <span class="gold">{scores["breakdown"]["formatting"]}</span>/25</div>
          <div class="pill">Content: <span class="gold">{scores["breakdown"]["content"]}</span>/30</div>
        </div>
      </div>

      <div class="panel">
        <div class="muted">Quick Flags</div>
        <ul>
          <li>Possible multi-column layout: <span class="emerald">{str(fmt["possible_multi_column_layout"])}</span></li>
          <li>Missing core sections: <span class="emerald">{", ".join(fmt["section_presence"]["missing_core_sections"]) or "none"}</span></li>
          <li>Email detected: <span class="emerald">{str(fmt["contact_info"]["email_detected"])}</span></li>
          <li>Phone detected: <span class="emerald">{str(fmt["contact_info"]["phone_detected"])}</span></li>
        </ul>
      </div>
    </div>

    <div class="row" style="margin-top:14px;">
      <div class="panel">
        <div class="muted">Keywords Present</div>
        <ul>{li(present[:25])}</ul>
      </div>
      <div class="panel">
        <div class="muted">Keywords Missing</div>
        <ul>{li(missing[:25])}</ul>
      </div>
    </div>

    <div class="panel" style="margin-top:14px;">
      <div class="muted">Suggestions</div>
      <div style="margin-top:10px;">{cards or "<div class='muted'>—</div>"}</div>
    </div>
  </div>
</body>
</html>
"""
    return html
