# UrbanFlow detailed project report

`UrbanFlow-Project-Report.pdf` is the illustrated project report. Its editable narrative is `UrbanFlow-Project-Report.md`; `build_report.py` creates the PDF, charts and screenshot crops from repository evidence. Screenshots are real application captures, not mockups.

The report distinguishes the completed descriptive analytical model from a trained machine-learning model. It records the measured Q1 result and benchmark limitations, local MongoDB verification, offline snapshot delivery, and outstanding Atlas / clean-machine / signing work.

To rebuild from the repository root:

```powershell
uv pip install --python .venv/Scripts/python.exe -r docs/report/requirements.txt
.venv/Scripts/python.exe docs/report/build_report.py
```

The generator uses existing screenshots in `.impeccable/review/` when available, and retains portable copies in `docs/report/figures/`. Result evidence is copied into `docs/report/evidence/` so the published report can be rebuilt without an active API. Fonts use Windows Calibri when available and Liberation Sans or DejaVu Sans on Linux.

Rendering and extraction checks are recorded in `quality-check.json`. Generated page previews belong in ignored `artifacts/report-qa/`, not source control.
