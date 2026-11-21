"""
build_pptx.py — Generates dukaanpulse.pptx
Requires: pip install python-pptx

Usage:
    python presentation/build_pptx.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os

# ─── DESIGN TOKENS ──────────────────────────────────
INK    = RGBColor(0x0F, 0x17, 0x2A)   # #0F172A deep navy
TEAL   = RGBColor(0x0F, 0x76, 0x6E)   # #0F766E dark teal
CANVAS = RGBColor(0xF8, 0xFA, 0xFC)   # #F8FAFC off-white
AMBER  = RGBColor(0xF5, 0x9E, 0x0B)   # #F59E0B amber
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
MUTED  = RGBColor(0x64, 0x74, 0x8B)

# Slide dimensions: 16:9 widescreen (10 × 5.625 inches)
SLIDE_W = Inches(10)
SLIDE_H = Inches(5.625)

FONT = "Inter"  # falls back to Calibri if Inter is not installed on viewer's machine

out_path = os.path.join(os.path.dirname(__file__), "dukaanpulse.pptx")


# ─── HELPERS ────────────────────────────────────────
def new_prs():
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def blank_slide(prs):
    blank_layout = prs.slide_layouts[6]  # completely blank
    return prs.slides.add_slide(blank_layout)


def bg(slide, color: RGBColor):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text(slide, text, left, top, width, height,
             font_size=18, bold=False, color=INK,
             align=PP_ALIGN.LEFT, italic=False, wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = FONT
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txBox


def add_rect(slide, left, top, width, height, fill_color, border=False, border_color=None, radius=None):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border and border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(0.75)
    else:
        shape.line.fill.background()
    return shape


def add_label(slide, text, left, top):
    """Small teal brand pill label"""
    add_text(slide, f"● {text}",
             left, top, Inches(4), Inches(0.3),
             font_size=9, bold=True, color=TEAL)


# ─── SLIDE 1: DARK OPENING ──────────────────────────
def slide1(prs):
    sl = blank_slide(prs)
    bg(sl, INK)

    add_label(sl, "DUKAANPULSE", Inches(0.5), Inches(0.35))

    # Title
    add_text(sl, "Know what to test before you spend.",
             Inches(0.5), Inches(0.75), Inches(7), Inches(1.3),
             font_size=36, bold=True, color=WHITE)

    # Subtitle
    add_text(sl, "DukaanPulse helps small café owners research an idea,\ncheck its costs, and plan a small business test.",
             Inches(0.5), Inches(2.0), Inches(5.5), Inches(0.9),
             font_size=15, color=RGBColor(0xAA, 0xBB, 0xCC))

    # Flow steps
    steps = [("❓", "Question"), ("📰", "Evidence"), ("🧮", "Cost check"), ("🧪", "Small test")]
    x_start = Inches(0.5)
    y = Inches(3.1)
    for i, (icon, label) in enumerate(steps):
        x = x_start + Inches(i * 2.1)
        add_text(sl, f"{icon}  {label}",
                 x, y, Inches(1.8), Inches(0.4),
                 font_size=12, bold=True, color=AMBER)
        if i < len(steps) - 1:
            add_text(sl, "→",
                     x + Inches(1.8), y, Inches(0.3), Inches(0.4),
                     font_size=14, color=AMBER, align=PP_ALIGN.CENTER)

    # Footer
    add_text(sl, "Live web research powered by You.com   ·   dukaanpulse-eight.vercel.app",
             Inches(0.5), Inches(5.1), Inches(9), Inches(0.3),
             font_size=9, color=MUTED)

    sl.notes_slide.notes_text_frame.text = (
        "Introduce an illustrative café owner (e.g. Priya) who wants to try a breakfast bundle. "
        "She does not know if it will make money for her specific shop. "
        "DukaanPulse walks her from question to small test with real web evidence and her own cost numbers. "
        "Priya is NOT a real customer — do not claim user validation."
    )
    return sl


# ─── SLIDE 2: THE PROBLEM ───────────────────────────
def slide2(prs):
    sl = blank_slide(prs)
    bg(sl, CANVAS)

    add_label(sl, "THE PROBLEM", Inches(0.5), Inches(0.35))
    add_text(sl, "A good offer can still be a costly guess.",
             Inches(0.5), Inches(0.7), Inches(7), Inches(0.9),
             font_size=28, bold=True, color=INK)

    # Question cards
    cards = ["What should I offer?", "Can I afford it?", "Did it work?"]
    for i, q in enumerate(cards):
        y = Inches(1.8) + Inches(i * 0.9)
        add_rect(sl, Inches(0.5), y, Inches(3.5), Inches(0.75),
                 fill_color=WHITE, border=True, border_color=RGBColor(0xE2, 0xE8, 0xF0))
        add_text(sl, f"?  {q}", Inches(0.6), y + Inches(0.1), Inches(3.3), Inches(0.6),
                 font_size=12, bold=True, color=TEAL)

    # Bullet points
    bullets = [
        "Local information is scattered across the web.",
        "Copying competitors may not fit your shop.",
        "A discount can leave too little margin.",
        "Results are not always recorded or reviewed.",
    ]
    for i, b in enumerate(bullets):
        y = Inches(1.85) + Inches(i * 0.72)
        add_text(sl, f"•  {b}", Inches(4.5), y, Inches(5), Inches(0.6),
                 font_size=12, color=INK)

    sl.notes_slide.notes_text_frame.text = (
        "These are problems the product is designed to address. "
        "They have not been formally validated with merchant interviews. "
        "Present them as the product's design hypotheses."
    )
    return sl


# ─── SLIDE 3: HOW IT WORKS ──────────────────────────
def slide3(prs):
    sl = blank_slide(prs)
    bg(sl, CANVAS)

    add_label(sl, "HOW IT WORKS", Inches(0.5), Inches(0.35))
    add_text(sl, "Ask. Check. Test.",
             Inches(0.5), Inches(0.7), Inches(7), Inches(0.75),
             font_size=32, bold=True, color=INK)

    steps = [
        ("1", "Ask your question",
         "Type a business question. The app searches live web sources and gathers findings."),
        ("2", "See sources, check costs",
         "Inspect every cited source. Enter your own costs. See if the offer makes sense."),
        ("3", "Approve a small test",
         "Approve a bounded experiment. Record daily outcomes. Build a record of what worked."),
    ]
    for i, (num, title, desc) in enumerate(steps):
        x = Inches(0.4) + Inches(i * 3.15)
        add_rect(sl, x, Inches(1.65), Inches(2.9), Inches(2.8),
                 fill_color=WHITE, border=True, border_color=RGBColor(0xE2, 0xE8, 0xF0))
        # Number circle (simulated with text)
        add_text(sl, num, x + Inches(0.1), Inches(1.75), Inches(0.4), Inches(0.4),
                 font_size=14, bold=True, color=WHITE)
        add_rect(sl, x + Inches(0.08), Inches(1.73), Inches(0.35), Inches(0.37),
                 fill_color=TEAL)
        add_text(sl, num, x + Inches(0.08), Inches(1.73), Inches(0.35), Inches(0.37),
                 font_size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(sl, title, x + Inches(0.1), Inches(2.2), Inches(2.7), Inches(0.45),
                 font_size=13, bold=True, color=INK)
        add_text(sl, desc, x + Inches(0.1), Inches(2.65), Inches(2.7), Inches(1.5),
                 font_size=10, color=MUTED)

    # Example chip
    add_text(sl, '📌  "Should I try a weekday breakfast bundle?"',
             Inches(0.5), Inches(4.65), Inches(7), Inches(0.5),
             font_size=11, bold=True, color=TEAL)

    sl.notes_slide.notes_text_frame.text = (
        "Walk through each step. You.com search is real (requires API key). "
        "AI synthesis verifies every quoted sentence against the retrieved source. "
        "Economics calculation is deterministic Python — not AI-generated."
    )
    return sl


# ─── SLIDE 4: DIFFERENTIATION ───────────────────────
def slide4(prs):
    sl = blank_slide(prs)
    bg(sl, CANVAS)

    add_label(sl, "WHAT MAKES IT DIFFERENT", Inches(0.5), Inches(0.35))
    add_text(sl, "Not just advice. A decision you can inspect.",
             Inches(0.5), Inches(0.7), Inches(7), Inches(0.75),
             font_size=28, bold=True, color=INK)

    cards = [
        ("🔗", "See the source", "Every finding links to the web page it came from."),
        ("🧮", "Use your own costs", "Enter your ingredient prices. Economics update live."),
        ("🏷️", "Know what is missing", "Gaps are labelled clearly — not hidden behind confident text."),
        ("📋", "Track the test", "Approve the experiment and record daily outcomes."),
    ]
    positions = [
        (Inches(0.4), Inches(1.65)),
        (Inches(5.1), Inches(1.65)),
        (Inches(0.4), Inches(3.4)),
        (Inches(5.1), Inches(3.4)),
    ]
    for (x, y), (icon, title, desc) in zip(positions, cards):
        add_rect(sl, x, y, Inches(4.4), Inches(1.55),
                 fill_color=WHITE, border=True, border_color=RGBColor(0xE2, 0xE8, 0xF0))
        add_text(sl, icon, x + Inches(0.15), y + Inches(0.12), Inches(0.5), Inches(0.4), font_size=16)
        add_text(sl, title, x + Inches(0.15), y + Inches(0.52), Inches(4.1), Inches(0.35),
                 font_size=13, bold=True, color=TEAL)
        add_text(sl, desc, x + Inches(0.15), y + Inches(0.9), Inches(4.1), Inches(0.55),
                 font_size=10, color=MUTED)

    sl.notes_slide.notes_text_frame.text = (
        "These four points distinguish DukaanPulse from a plain AI chatbot. "
        "Do not claim these have been confirmed by user research. "
        "They are the product's design intent."
    )
    return sl


# ─── SLIDE 5: DEMO ──────────────────────────────────
def slide5(prs):
    sl = blank_slide(prs)
    bg(sl, CANVAS)

    add_label(sl, "WORKING PROTOTYPE", Inches(0.5), Inches(0.35))
    add_text(sl, "One question. One clear next step.",
             Inches(0.5), Inches(0.7), Inches(7), Inches(0.75),
             font_size=28, bold=True, color=INK)

    demo_steps = [
        "Enter a café question in plain English.",
        "Open any source excerpt — read the original page.",
        "Change an ingredient cost — economics update instantly.",
        "Review the suggested experiment and approve it.",
    ]
    for i, step in enumerate(demo_steps):
        y = Inches(1.65) + Inches(i * 0.72)
        add_rect(sl, Inches(0.4), y + Inches(0.04), Inches(0.35), Inches(0.37),
                 fill_color=INK)
        add_text(sl, str(i + 1), Inches(0.4), y + Inches(0.04), Inches(0.35), Inches(0.37),
                 font_size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(sl, step, Inches(0.9), y, Inches(3.6), Inches(0.6),
                 font_size=11, color=INK)

    # Preview box
    add_rect(sl, Inches(5.0), Inches(1.55), Inches(4.6), Inches(3.6),
             fill_color=WHITE, border=True, border_color=RGBColor(0xE2, 0xE8, 0xF0))
    add_text(sl, "Working Prototype",
             Inches(5.4), Inches(1.75), Inches(3.8), Inches(0.4),
             font_size=10, bold=True, color=RGBColor(0x92, 0x40, 0x0E),
             align=PP_ALIGN.CENTER)
    add_text(sl, "dukaanpulse-eight.vercel.app",
             Inches(5.1), Inches(2.9), Inches(4.2), Inches(0.4),
             font_size=12, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    add_text(sl, "Live app · FastAPI + You.com search\nWorks on mobile and desktop",
             Inches(5.1), Inches(3.4), Inches(4.2), Inches(0.6),
             font_size=9, color=MUTED, align=PP_ALIGN.CENTER)

    sl.notes_slide.notes_text_frame.text = (
        "Demo sequence: open app → type question → wait for research → open citation drawer → "
        "change cost → watch economics update → approve experiment → show task checklist. "
        "If the demo fails, describe the steps verbally. "
        "Label all inputs as illustrative — not real merchant data."
    )
    return sl


# ─── SLIDE 6: CLOSING ───────────────────────────────
def slide6(prs):
    sl = blank_slide(prs)
    bg(sl, TEAL)

    add_label(sl, "WHAT'S NEXT", Inches(0.5), Inches(0.35))
    add_text(sl, "Start small.\nLearn before spending more.",
             Inches(0.5), Inches(0.7), Inches(7), Inches(1.3),
             font_size=34, bold=True, color=WHITE)

    add_text(sl, "Clear sources. Visible costs. A measurable next step.",
             Inches(0.5), Inches(2.1), Inches(7), Inches(0.5),
             font_size=15, color=RGBColor(0xCC, 0xEE, 0xEA), italic=True)

    # Loop steps
    loop = [("🔍", "Research"), ("🧮", "Check"), ("🧪", "Test"), ("📖", "Learn")]
    for i, (icon, label) in enumerate(loop):
        x = Inches(0.5) + Inches(i * 2.1)
        add_text(sl, f"{icon}  {label}", x, Inches(2.8), Inches(1.8), Inches(0.4),
                 font_size=12, bold=True, color=AMBER)
        if i < len(loop) - 1:
            add_text(sl, "→", x + Inches(1.8), Inches(2.8), Inches(0.3), Inches(0.4),
                     font_size=13, color=AMBER, align=PP_ALIGN.CENTER)

    # Next chips
    nexts = ["Test with café owners", "Improve the workflow", "Learn from real experiments"]
    for i, n in enumerate(nexts):
        x = Inches(0.5) + Inches(i * 3.1)
        add_text(sl, n, x, Inches(3.5), Inches(2.9), Inches(0.4),
                 font_size=11, color=WHITE)

    add_text(sl, "🔗  dukaanpulse-eight.vercel.app",
             Inches(0.5), Inches(4.2), Inches(5), Inches(0.4),
             font_size=12, bold=True, color=AMBER)

    add_text(sl, "DukaanPulse — from business guesswork to a considered test.",
             Inches(0.5), Inches(4.9), Inches(9), Inches(0.4),
             font_size=10, color=RGBColor(0x99, 0xBB, 0xB8), italic=True)

    sl.notes_slide.notes_text_frame.text = (
        "Do not claim merchant validation. If asked, say it is the next step. "
        "Do not fabricate revenue metrics or user counts. "
        "GitHub: https://github.com/psryogeshwar-14/dukaanpulse"
    )
    return sl


# ─── MAIN ────────────────────────────────────────────
def main():
    prs = new_prs()
    slide1(prs)
    slide2(prs)
    slide3(prs)
    slide4(prs)
    slide5(prs)
    slide6(prs)
    prs.save(out_path)
    print(f"✅  Saved → {out_path}")
    print("   Open in PowerPoint or Keynote.")
    print("   Add Fade slide transitions manually for best results.")


if __name__ == "__main__":
    main()
