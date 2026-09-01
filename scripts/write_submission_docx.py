"""Create a .docx without python-docx (zip + Word XML)."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "Cloud Care Health - Reviewer Notes.docx"

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""


def p(text: str, *, heading: int | None = None, bold: bool = False) -> str:
    run_props = "<w:b/>" if bold or heading else ""
    size = {1: "36", 2: "28", 3: "24"}.get(heading, "22")
    color = "0B3D4A" if heading else "1A1A1A"
    space = "240" if heading == 1 else "120"
    return (
        f'<w:p><w:pPr><w:spacing w:after="{space}"/></w:pPr>'
        f"<w:r><w:rPr>{run_props}<w:sz w:val=\"{size}\"/><w:szCs w:val=\"{size}\"/>"
        f'<w:color w:val="{color}"/></w:rPr>'
        f"<w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r></w:p>"
    )


def document_xml() -> str:
    blocks = [
        p("Cloud Care Health — Voice AI Patient Registration", heading=1),
        p("Take-home technical assessment — reviewer pack", heading=2),
        p(
            "Reviewers do not need to install anything. Call the US number and open the links below. "
            "Please use fictional patient data only (not real PHI)."
        ),
        p("What to send / what to use", heading=2),
        p("Repository URL", heading=3),
        p("https://github.com/saadmasoodd22/voice-ai-patient-agent"),
        p("US phone number to call", heading=3),
        p("+1 (860) 410-8127"),
        p("API base URL", heading=3),
        p("https://saadmasoodd22.pythonanywhere.com"),
        p("Dashboard", heading=3),
        p("https://saadmasoodd22.pythonanywhere.com"),
        p("Same host as the API. Open in a browser. No login."),
        p("Credentials", heading=3),
        p("None. The dashboard and REST API are open for this demo. No login, no API key, no VPN."),
        p("How to test (about 5 minutes)", heading=2),
        p("1. From a US phone, call +1 (860) 410-8127. The agent is Saad, Cloud Care Health intake."),
        p("2. Register a fake patient in natural speech. The agent will confirm details before saving."),
        p("3. Open the dashboard URL and confirm the new row appears in Patients (and on the charts)."),
        p("4. Optional API checks (browser or curl):"),
        p("   GET https://saadmasoodd22.pythonanywhere.com/health"),
        p("   GET https://saadmasoodd22.pythonanywhere.com/patients"),
        p("   GET https://saadmasoodd22.pythonanywhere.com/patients?last_name=Doe"),
        p("   GET https://saadmasoodd22.pythonanywhere.com/stats"),
        p("Notes for reviewers", heading=2),
        p(
            "I am based in Pakistan, so I cannot place a normal outbound call to a US number from here. "
            "I verified the portal, REST API, and database locally. If you call from a US number to "
            "+1 (860) 410-8127, you can test the live voice path end-to-end."
        ),
        p(
            "Please keep using fake demographics (for example Jane Doe, 04/12/1988, 415-555-0198). "
            "This is not a HIPAA production system."
        ),
        p(
            "JSON responses use the envelope { \"data\": ..., \"error\": null }. "
            "DELETE /patients/{id} is a soft delete (deleted_at), not a hard delete."
        ),
        p(
            "Seed data: the dashboard already shows demo patients so charts are populated before the first live call."
        ),
        p("What you should NOT need to do", heading=2),
        p("Do not clone the repo unless you want to read the code."),
        p("Do not install Python, MySQL, Docker, or any tunnel."),
        p("Do not create cloud accounts or set environment variables."),
        p("Candidate note (not a reviewer task)", heading=2),
        p(
            "The public URL is hosted on PythonAnywhere so the dashboard and voice tools stay up without this laptop. "
            "Live storage is SQLite (free PythonAnywhere accounts do not include MySQL). "
            "Local MySQL on my machine is only for development."
        ),
        p("Stack (for context)", heading=2),
        p("Voice: Vapi US number + Groq LLM. Live API: Python WSGI on PythonAnywhere. Local API: FastAPI + MySQL 8. Dashboard: Chart.js portal served by the same API."),
        p("Agent name: Saad. Clinic name: Cloud Care Health. The PDF did not require a clinic or agent name."),
    ]
    inner = "".join(blocks)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{inner}<w:sectPr/></w:body></w:document>"
    )


def main() -> None:
    out = OUT
    try:
        out.unlink(missing_ok=True)
    except PermissionError:
        out = OUT.with_name("Cloud Care Health - Reviewer Notes - live.docx")
        print("original docx is open; writing", out)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", RELS)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS)
        zf.writestr("word/document.xml", document_xml())
    print(out)


if __name__ == "__main__":
    main()
