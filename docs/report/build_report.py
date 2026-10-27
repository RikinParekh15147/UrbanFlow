"""Build the illustrated UrbanFlow report from portable, inspectable sources."""

import hashlib
import html
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIGURES = HERE / "figures"
EVIDENCE = HERE / "evidence"
OUTPUT = HERE / "UrbanFlow-Project-Report.pdf"
GREEN = "#193d35"
INK = "#21352f"
MUTED = "#596b64"
LIME = "#d1eb7e"
PAPER = "#f5f6f0"
WIDTH, HEIGHT = A4
BODY_WIDTH = WIDTH - 100


def fonts():
    """Use embedded, locally available fonts without redistributing font files."""
    candidates = [
        (Path("C:/Windows/Fonts"), "calibri.ttf", "calibrib.ttf", "calibrii.ttf"),
        (
            Path("/usr/share/fonts/truetype/liberation2"),
            "LiberationSans-Regular.ttf",
            "LiberationSans-Bold.ttf",
            "LiberationSans-Italic.ttf",
        ),
        (
            Path("/usr/share/fonts/truetype/dejavu"),
            "DejaVuSans.ttf",
            "DejaVuSans-Bold.ttf",
            "DejaVuSans-Oblique.ttf",
        ),
    ]
    for base, regular, bold, italic in candidates:
        if (base / regular).exists():
            for name, file in [("UF", regular), ("UF-Bold", bold), ("UF-Italic", italic)]:
                pdfmetrics.registerFont(TTFont(name, str(base / file)))
            pdfmetrics.registerFontFamily(
                "UF", normal="UF", bold="UF-Bold", italic="UF-Italic", boldItalic="UF-Bold"
            )
            return base / regular, base / bold
    raise RuntimeError("Install Calibri, Liberation Sans or DejaVu Sans before rebuilding")


REGULAR, BOLD = fonts()


def png_font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else REGULAR), size)


def wrap(draw, text, font, max_width):
    result, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) > max_width and line:
            result.append(line)
            line = word
        else:
            line = trial
    return result + [line]


def box(draw, rect, title, detail, fill=GREEN):
    draw.rounded_rectangle(rect, radius=22, fill=fill)
    x0, y0, x1, _ = rect
    draw.text((x0 + 24, y0 + 18), title, fill="white", font=png_font(29, True))
    for i, line in enumerate(wrap(draw, detail, png_font(23), x1 - x0 - 46)):
        draw.text((x0 + 24, y0 + 63 + 29 * i), line, fill="#e8efe7", font=png_font(23))


def arrow(draw, a, b):
    draw.line([a, b], fill=MUTED, width=6)
    x, y = b
    if b[0] == a[0]:
        draw.polygon([(x, y), (x - 12, y - 18), (x + 12, y - 18)], fill=MUTED)
    else:
        draw.polygon([(x, y), (x - 18, y - 12), (x - 18, y + 12)], fill=MUTED)


def diagrams():
    image = PILImage.new("RGB", (1700, 1100), "white")
    d = ImageDraw.Draw(image)
    d.text((45, 30), "BATCH COMPUTATION", fill=GREEN, font=png_font(32, True))
    d.text((610, 583), "APPLICATION SERVING", fill=GREEN, font=png_font(32, True))
    box(
        d,
        (45, 100, 520, 265),
        "Official TLC inputs",
        "Monthly Parquet + zone lookup + official geometry",
    )
    box(
        d,
        (610, 100, 1090, 265),
        "Colab / Spark SQL",
        "Prepare, flag, aggregate and validate the selected period",
    )
    box(
        d,
        (1180, 100, 1655, 265),
        "Drive archives",
        "Raw + curated + aggregate Parquet; hashes and executed source",
    )
    arrow(d, (520, 182), (610, 182))
    arrow(d, (1090, 182), (1180, 182))
    box(
        d,
        (610, 350, 1090, 515),
        "Versioned publisher",
        "Deterministic keys; stage and validate before pointer switch",
    )
    arrow(d, (850, 265), (850, 350))
    box(
        d,
        (45, 655, 520, 820),
        "Serving sources",
        "MongoDB OR explicitly selected real-data snapshot",
    )
    box(
        d,
        (610, 655, 1090, 820),
        "FastAPI",
        "Validated filters, weighted metrics and OpenAPI contracts",
    )
    box(
        d,
        (1180, 655, 1655, 820),
        "React + Electron",
        "Seven sections, filters, charts, maps and desktop lifecycle",
    )
    d.line([(610, 435), (285, 435), (285, 655)], fill=MUTED, width=6)
    arrow(d, (285, 580), (285, 655))
    arrow(d, (520, 737), (610, 737))
    arrow(d, (1090, 737), (1180, 737))
    d.rounded_rectangle((45, 920, 1655, 1040), radius=20, fill=PAPER)
    d.text((75, 942), "Dashboard requests never start Spark.", fill=GREEN, font=png_font(34, True))
    d.text(
        (75, 990),
        "Colab can stop after verified outputs persist outside the runtime.",
        fill=MUTED,
        font=png_font(26),
    )
    image.save(FIGURES / "architecture.png", optimize=True)

    image = PILImage.new("RGB", (1700, 1080), "white")
    d = ImageDraw.Draw(image)
    box(
        d,
        (560, 30, 1140, 185),
        "dataset_publications/current",
        "Single atomic reader-visible run pointer",
    )
    box(
        d,
        (560, 260, 1140, 420),
        "dataset_runs",
        "Run ID, hashes, status, quality, period and machine evidence",
    )
    arrow(d, (850, 185), (850, 260))
    groups = [
        (45, "Demand + efficiency", "Date / hour / pickup-zone grain; additive sums and counts"),
        (610, "Fares + routes", "Daily zone fares; retained daily top-100 OD route counts"),
        (1175, "Zones + benchmarks", "Geometry stored once per run; whole-run experiment records"),
    ]
    for x, title, detail in groups:
        d.line([(850, 420), (850, 495), (x + 240, 495)], fill=MUTED, width=6)
        arrow(d, (x + 240, 495), (x + 240, 565))
        box(d, (x, 565, x + 480, 770), title, detail)
    d.rounded_rectangle((45, 860, 1655, 1010), radius=20, fill=PAPER)
    d.text(
        (75, 880),
        "Every analytical query is scoped to one immutable run identity.",
        fill=GREEN,
        font=png_font(31, True),
    )
    d.text(
        (75, 935),
        "Raw and full curated trips remain outside MongoDB. "
        "Earlier published runs can be retained.",
        fill=MUTED,
        font=png_font(25),
    )
    image.save(FIGURES / "data-model.png", optimize=True)


def gather_assets():
    FIGURES.mkdir(exist_ok=True)
    EVIDENCE.mkdir(exist_ok=True)
    for file in [
        "q1-run.json",
        "q1-drive-export.json",
        "release-verification.json",
        "validation.md",
    ]:
        shutil.copy2(ROOT / "docs" / file, EVIDENCE / file)
    bench = ROOT / "data/serving/benchmarks.jsonl"
    if bench.exists():
        shutil.copy2(bench, EVIDENCE / bench.name)
    overview = EVIDENCE / "overview.json"
    if not overview.exists():
        with urlopen("http://127.0.0.1:8000/api/v1/overview", timeout=30) as response:
            overview.write_text(json.dumps(json.load(response), indent=2) + "\n", encoding="utf-8")
    names = ["overview", "demand", "geography", "trips", "fares", "lab", "dataset-model"]
    for name in names:
        source = ROOT / ".impeccable/review" / f"report-{name}.png"
        target = FIGURES / f"{name}-source.png"
        if source.exists():
            shutil.copy2(source, target)
        if not target.exists():
            raise FileNotFoundError(f"Missing actual application capture: {source}")
        with PILImage.open(target) as image:
            # Remove navigation/sidebar only; keep real heading, units and plotted content.
            top = 170 if name in {"dataset-model", "lab"} else 150
            image.crop((250, top, 1420, 990)).save(FIGURES / f"{name}.png", optimize=True)
    diagrams()


def benchmark_chart():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [json.loads(line) for line in (EVIDENCE / "benchmarks.jsonl").read_text().splitlines()]
    sizes = sorted({r["input_rows"] for r in rows})
    fig, ax = plt.subplots(figsize=(10.5, 4.9))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for i, engine in enumerate(["Pandas", "Spark SQL"]):
        values = [
            next(r["elapsed_ms"] for r in rows if r["engine"] == engine and r["input_rows"] == n)
            for n in sizes
        ]
        positions = [j + (-0.18 if i == 0 else 0.18) for j in range(len(sizes))]
        bars = ax.barh(
            positions, values, height=0.3, label=engine, color=GREEN if i == 0 else "#87a44c"
        )
        for bar, value in zip(bars, values):
            ax.text(
                value * 1.075,
                bar.get_y() + bar.get_height() / 2,
                f"{value:,.3f}",
                va="center",
                fontsize=10,
                color=INK,
            )
    ax.set_yticks(range(len(sizes)), [f"{n:,} rows" for n in sizes])
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlim(5, 3000)
    ax.set_xlabel("Median elapsed milliseconds (log scale); lower is faster", labelpad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=0.15)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.025), ncol=2, frameon=False)
    fig.tight_layout(pad=1.8)
    fig.savefig(FIGURES / "benchmark.png", dpi=220)
    fig.savefig(FIGURES / "benchmark.pdf")
    plt.close(fig)


def styles():
    sheet = StyleSheet1()
    definitions = {
        "body": dict(fontSize=10.5, leading=15.6, spaceAfter=9, textColor=colors.HexColor(INK)),
        "h1": dict(
            fontName="UF-Bold",
            fontSize=23,
            leading=29,
            spaceAfter=19,
            textColor=colors.HexColor(GREEN),
            keepWithNext=True,
        ),
        "h2": dict(
            fontName="UF-Bold",
            fontSize=14,
            leading=19,
            spaceBefore=12,
            spaceAfter=8,
            keepWithNext=True,
            textColor=colors.HexColor(GREEN),
        ),
        "caption": dict(
            fontSize=9.4, leading=13, spaceBefore=8, spaceAfter=16, textColor=colors.HexColor(MUTED)
        ),
        "table": dict(fontSize=9.2, leading=12.6, textColor=colors.HexColor(INK)),
        "th": dict(fontName="UF-Bold", fontSize=9.3, leading=12.5, textColor=colors.white),
        "bullet": dict(
            fontSize=10.5,
            leading=15,
            leftIndent=13,
            firstLineIndent=-10,
            spaceAfter=6,
            textColor=colors.HexColor(INK),
        ),
        "quote": dict(
            fontSize=10.5,
            leading=16,
            borderPadding=13,
            backColor=colors.HexColor(PAPER),
            spaceBefore=8,
            spaceAfter=14,
            textColor=colors.HexColor(GREEN),
        ),
        "code": dict(
            fontName="Courier",
            fontSize=8,
            leading=11,
            borderPadding=11,
            backColor=colors.HexColor(PAPER),
            spaceAfter=13,
        ),
        "toc": dict(
            fontSize=10.5, leading=14, spaceBefore=3, spaceAfter=3, textColor=colors.HexColor(INK)
        ),
        "reference": dict(fontSize=9.4, leading=13, spaceAfter=6, textColor=colors.HexColor(INK)),
    }
    for name, options in definitions.items():
        sheet.add(
            ParagraphStyle(name, fontName="UF", alignment=TA_LEFT, splitLongWords=True, **options)
        ) if "fontName" not in options else sheet.add(
            ParagraphStyle(name, alignment=TA_LEFT, splitLongWords=True, **options)
        )
    return sheet


STYLES = styles()


def inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    return text


def para(text, kind="body"):
    return Paragraph(inline(text), STYLES[kind])


class Report(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            str(filename),
            pagesize=A4,
            leftMargin=50,
            rightMargin=50,
            topMargin=65,
            bottomMargin=55,
            title="UrbanFlow: Big Data Urban Mobility Analytics Platform",
            author="UrbanFlow Project",
            subject="Detailed architecture, methods, implementation, results and reproducibility",
            pageCompression=1,
        )
        frame = Frame(
            50,
            55,
            BODY_WIDTH,
            HEIGHT - 120,
            leftPadding=0,
            bottomPadding=0,
            rightPadding=0,
            topPadding=0,
        )
        self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self.page_chrome)])
        self.heading_counter = 0

    def page_chrome(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d6dfd4"))
        canvas.line(50, HEIGHT - 40, WIDTH - 50, HEIGHT - 40)
        canvas.setFont("UF-Bold", 9)
        canvas.setFillColor(colors.HexColor(GREEN))
        canvas.drawString(50, HEIGHT - 30, "URBANFLOW")
        canvas.setFont("UF", 8.5)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawRightString(WIDTH - 50, HEIGHT - 30, "PROJECT REPORT  /  Q1 2025 DATA")
        canvas.line(50, 39, WIDTH - 50, 39)
        canvas.drawString(50, 25, "Historical analytics  |  Real data  |  Reproducible evidence")
        canvas.drawRightString(WIDTH - 50, 25, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "h1":
            self.heading_counter += 1
            text = flowable.getPlainText()
            key = "section-" + hashlib.sha1(text.encode()).hexdigest()[:12]
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, 0, closed=False)
            if text != "Contents":
                self.notify("TOCEntry", (0, text, self.page, key))


class Cover:
    @staticmethod
    def content():
        cover_title = ParagraphStyle(
            "cover-title",
            fontName="UF-Bold",
            fontSize=57,
            leading=62,
            textColor=colors.HexColor(GREEN),
        )
        cover_sub = ParagraphStyle(
            "cover-sub", fontName="UF", fontSize=25, leading=32, textColor=colors.HexColor(GREEN)
        )
        cover_meta = ParagraphStyle(
            "cover-meta", fontName="UF", fontSize=11, leading=17, textColor=colors.HexColor(MUTED)
        )
        story = [
            Spacer(1, 10),
            para("DETAILED PROJECT DOCUMENTATION", "caption"),
            Spacer(1, 14),
            Paragraph("UrbanFlow", cover_title),
            Spacer(1, 8),
            Paragraph("Big Data Urban Mobility<br/>Analytics Platform", cover_sub),
            Spacer(1, 20),
        ]
        with PILImage.open(FIGURES / "overview.png") as image:
            width, height = image.size
        story += [
            Image(
                str(FIGURES / "overview.png"), width=BODY_WIDTH, height=BODY_WIDTH * height / width
            ),
            Spacer(1, 15),
            Paragraph(
                "Architecture, theory, implementation, analytical results,<br/>"
                "verification and reproducibility",
                cover_meta,
            ),
            Spacer(1, 10),
            Paragraph(
                "11.2 million real source records  |  January-March 2025<br/>"
                "Spark SQL + MongoDB + FastAPI + React + Electron<br/>"
                "Report prepared: 26 October 2026",
                cover_meta,
            ),
            PageBreak(),
        ]
        return story


def parse_markdown(text):
    story, lines, index = [], text.splitlines(), 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            if story:
                story.append(PageBreak())
            story.append(para(line[2:], "h1"))
            index += 1
        elif line.startswith("## "):
            if line[3:] == "Suggested demonstration sequence":
                story.append(PageBreak())
            story.append(para(line[3:], "h2"))
            index += 1
        elif line.startswith("!["):
            match = re.fullmatch(r"!\[(.*)\]\((.*)\)", line)
            if not match:
                raise ValueError(line)
            caption, filename = match.groups()
            path = HERE / filename
            with PILImage.open(path) as image:
                width, height = image.size
            display_height = BODY_WIDTH * height / width
            story.append(
                KeepTogether(
                    [
                        Spacer(1, 7),
                        Image(str(path), width=BODY_WIDTH, height=display_height),
                        para(caption, "caption"),
                    ]
                )
            )
            index += 1
        elif line.startswith("```"):
            code = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            story.append(
                KeepTogether([Preformatted("\n".join(code), STYLES["code"], maxLineLength=88)])
            )
            index += 1
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                raw = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", cell) for cell in raw):
                    rows.append(raw)
                index += 1
            n = len(rows[0])
            # Widths follow content: measured value columns stay compact.
            proportions = {2: [0.36, 0.64], 3: [0.29, 0.29, 0.42], 4: [0.24, 0.23, 0.24, 0.29]}[n]
            cells = [
                [para(cell, "th" if r == 0 else "table") for cell in row]
                for r, row in enumerate(rows)
            ]
            table = Table(
                cells,
                colWidths=[BODY_WIDTH * p for p in proportions],
                repeatRows=1,
                hAlign="LEFT",
                spaceAfter=15,
                spaceBefore=5,
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(GREEN)),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor(PAPER)],
                        ),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 9),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor(GREEN)),
                    ]
                )
            )
            story.append(table)
        elif line.startswith("> "):
            story.append(para(line[2:], "quote"))
            index += 1
        elif line.startswith("- ") or re.match(r"^\d+\. ", line):
            group = []
            while index < len(lines):
                item = lines[index].strip()
                if not (item.startswith("- ") or re.match(r"^\d+\. ", item)):
                    break
                group.append(para(item, "bullet"))
                index += 1
            story.append(KeepTogether(group))
        else:
            paragraph = [line]
            index += 1
            while (
                index < len(lines)
                and lines[index].strip()
                and not lines[index].startswith(("#", "|", "![", "```", "> ", "- "))
            ):
                paragraph.append(lines[index].strip())
                index += 1
            kind = "reference" if re.match(r"^\[R\d+\]", paragraph[0]) else "body"
            story.append(para(" ".join(paragraph), kind))
    return story


def main():
    gather_assets()
    benchmark_chart()
    content = (HERE / "UrbanFlow-Project-Report.md").read_text(encoding="utf-8")
    story = Cover.content()
    story += [
        para("Contents", "h1"),
        para(
            "A complete technical and analytical account of the implemented project. "
            "Figure captions and references identify actual evidence and its limits."
        ),
        Spacer(1, 10),
    ]
    toc = TableOfContents()
    toc.levelStyles = [STYLES["toc"]]
    toc.tableStyle = TableStyle(
        [
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]
    )
    toc.dotsMinLevel = 0
    story += [toc, PageBreak()]
    story += parse_markdown(content)
    Report(OUTPUT).multiBuild(story)
    metadata = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_words": len(content.split()),
        "pdf": OUTPUT.name,
        "bytes": OUTPUT.stat().st_size,
        "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "figures": 10,
        "source": "UrbanFlow-Project-Report.md",
    }
    (HERE / "build-manifest.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
