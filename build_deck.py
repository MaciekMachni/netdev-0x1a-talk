#!/usr/bin/env python3
"""
Build the "Making Time Uncertainty a First-Class Concept in Linux Timing"
40-minute presentation as a .pptx.

Fresh deck, written from scratch.

Usage:
    python3 build_deck.py [output.pptx]

Default output: time-uncertainty-error-bar.pptx (next to this script)
"""
import os
import sys

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ----------------------------------------------------------------------------
# Theme
# ----------------------------------------------------------------------------
INK      = RGBColor(0x1A, 0x1D, 0x29)   # near-black text
PAPER    = RGBColor(0xFF, 0xFF, 0xFF)   # slide background
ACCENT   = RGBColor(0x2E, 0x6B, 0xE6)   # blue accent
ACCENT2  = RGBColor(0x14, 0xB8, 0xA6)   # teal
MUTED    = RGBColor(0x5B, 0x61, 0x72)   # muted gray text
LIGHT    = RGBColor(0xED, 0xF1, 0xFB)   # light panel
CODE_BG  = RGBColor(0x11, 0x16, 0x27)   # dark code panel
CODE_FG  = RGBColor(0xD6, 0xE2, 0xFF)   # code text
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)

FONT      = "Calibri"
FONT_MONO = "Consolas"

SW = Inches(13.333)   # 16:9 widescreen
SH = Inches(7.5)


# ----------------------------------------------------------------------------
# Low-level helpers
# ----------------------------------------------------------------------------
def _set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _rect(slide, x, y, w, h, color, line=None):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(1)
    shp.shadow.inherit = False
    return shp


def _text(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT,
          anchor=MSO_ANCHOR.TOP, wrap=True, space_after=6):
    """runs: list of paragraphs; each paragraph is list of (text, size, bold,
    color, font, italic)."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.space_before = Pt(0)
        for (txt, size, bold, color, font, italic) in para:
            r = p.add_run()
            r.text = txt
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.italic = italic
            r.font.name = font
            r.font.color.rgb = color
    return tb


def R(txt, size=18, bold=False, color=INK, font=FONT, italic=False):
    return (txt, size, bold, color, font, italic)


def _notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def _footer(slide, idx):
    _rect(slide, 0, SH - Inches(0.28), SW, Inches(0.28), ACCENT)
    _text(slide, Inches(0.5), SH - Inches(0.30), Inches(9), Inches(0.28),
          [[R("Time Uncertainty as a First-Class Concept", 10, False, WHITE)]],
          anchor=MSO_ANCHOR.MIDDLE)
    _text(slide, SW - Inches(1.3), SH - Inches(0.30), Inches(0.8), Inches(0.28),
          [[R(str(idx), 10, True, WHITE)]], align=PP_ALIGN.RIGHT,
          anchor=MSO_ANCHOR.MIDDLE)


# ----------------------------------------------------------------------------
# Slide templates
# ----------------------------------------------------------------------------
def title_slide(prs, title, subtitle, presenter):
    s = _blank(prs)
    _set_bg(s, INK)
    _rect(s, 0, Inches(3.55), SW, Inches(0.09), ACCENT)
    _rect(s, 0, Inches(3.64), Inches(4.2), Inches(0.09), ACCENT2)
    _text(s, Inches(0.9), Inches(1.35), Inches(11.9), Inches(2.1),
          [[R(title, 38, True, WHITE)]])
    _text(s, Inches(0.92), Inches(3.85), Inches(11.5), Inches(0.8),
          [[R(subtitle, 22, False, RGBColor(0xC7, 0xD2, 0xF0))]])
    _text(s, Inches(0.92), Inches(5.9), Inches(11.5), Inches(1.0),
          [[R(presenter, 16, False, RGBColor(0x9A, 0xA6, 0xC4))]])
    return s


def section_slide(prs, part, title, idx):
    s = _blank(prs)
    _set_bg(s, ACCENT)
    _rect(s, 0, Inches(2.7), Inches(3.5), Inches(0.10), ACCENT2)
    _text(s, Inches(0.9), Inches(2.0), Inches(11), Inches(0.6),
          [[R(part.upper(), 20, True, RGBColor(0xC7, 0xD2, 0xF0))]])
    _text(s, Inches(0.88), Inches(2.95), Inches(11.5), Inches(2.0),
          [[R(title, 40, True, WHITE)]])
    _text(s, SW - Inches(1.3), SH - Inches(0.65), Inches(0.9), Inches(0.4),
          [[R(str(idx), 12, True, WHITE)]], align=PP_ALIGN.RIGHT)
    return s


def _header(s, title, kicker=None):
    _rect(s, 0, 0, Inches(0.18), Inches(1.25), ACCENT)
    if kicker:
        _text(s, Inches(0.55), Inches(0.28), Inches(12), Inches(0.4),
              [[R(kicker.upper(), 13, True, ACCENT)]])
        _text(s, Inches(0.55), Inches(0.62), Inches(12.2), Inches(0.9),
              [[R(title, 30, True, INK)]])
    else:
        _text(s, Inches(0.55), Inches(0.42), Inches(12.2), Inches(0.9),
              [[R(title, 30, True, INK)]])


def content_slide(prs, title, bullets, idx, kicker=None, notes=""):
    """bullets: list of (text, level) where level 0/1."""
    s = _blank(prs)
    _set_bg(s, PAPER)
    _header(s, title, kicker)
    paras = []
    for txt, lvl in bullets:
        if lvl == 0:
            paras.append([R("\u25B8  ", 18, True, ACCENT), R(txt, 18, False, INK)])
        else:
            paras.append([R("        \u2013  ", 16, False, MUTED),
                          R(txt, 16, False, MUTED)])
    _text(s, Inches(0.7), Inches(1.7), Inches(12.0), Inches(5.2), paras,
          space_after=10)
    _footer(s, idx)
    if notes:
        _notes(s, notes)
    return s


def statement_slide(prs, big, sub, idx, notes=""):
    s = _blank(prs)
    _set_bg(s, LIGHT)
    _rect(s, Inches(0.9), Inches(2.55), Inches(2.6), Inches(0.10), ACCENT)
    _text(s, Inches(0.9), Inches(2.75), Inches(11.5), Inches(2.0),
          [[R(big, 34, True, INK)]])
    if sub:
        _text(s, Inches(0.92), Inches(4.6), Inches(11.5), Inches(1.2),
              [[R(sub, 20, False, MUTED, FONT, True)]])
    _footer(s, idx)
    if notes:
        _notes(s, notes)
    return s


def code_slide(prs, title, code_lines, idx, kicker=None, caption=None, notes=""):
    s = _blank(prs)
    _set_bg(s, PAPER)
    _header(s, title, kicker)
    top = Inches(1.75)
    h = Inches(4.5) if caption else Inches(4.9)
    panel = _rect(s, Inches(0.7), top, Inches(11.9), h, CODE_BG)
    tf = panel.text_frame
    tf.word_wrap = False
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.2)
    tf.margin_bottom = Inches(0.2)
    for i, line in enumerate(code_lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(2)
        r = p.add_run()
        r.text = line if line else " "
        r.font.name = FONT_MONO
        r.font.size = Pt(15)
        r.font.color.rgb = CODE_FG
    if caption:
        _text(s, Inches(0.72), top + h + Inches(0.12), Inches(11.9), Inches(0.5),
              [[R(caption, 15, False, MUTED, FONT, True)]])
    _footer(s, idx)
    if notes:
        _notes(s, notes)
    return s


def table_slide(prs, title, headers, rows, idx, kicker=None, notes=""):
    s = _blank(prs)
    _set_bg(s, PAPER)
    _header(s, title, kicker)
    ncols = len(headers)
    nrows = len(rows) + 1
    left, top = Inches(0.7), Inches(1.8)
    width, height = Inches(11.9), Inches(0.5) * nrows
    gtbl = s.shapes.add_table(nrows, ncols, left, top, width, height).table
    # header
    for c, htext in enumerate(headers):
        cell = gtbl.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT
        cell.margin_left = Inches(0.12)
        cell.margin_top = Inches(0.05)
        cell.margin_bottom = Inches(0.05)
        p = cell.text_frame.paragraphs[0]
        r = p.add_run(); r.text = htext
        r.font.bold = True; r.font.size = Pt(15); r.font.color.rgb = WHITE
        r.font.name = FONT
    # body
    for ri, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = gtbl.cell(ri, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = PAPER if ri % 2 else LIGHT
            cell.margin_left = Inches(0.12)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
            p = cell.text_frame.paragraphs[0]
            p.word_wrap = True
            r = p.add_run(); r.text = val
            r.font.size = Pt(13.5)
            r.font.color.rgb = INK if c == 0 else MUTED
            r.font.bold = (c == 0)
            r.font.name = FONT
    _footer(s, idx)
    if notes:
        _notes(s, notes)
    return s


def two_col_slide(prs, title, left_head, left_items, right_head, right_items,
                  idx, kicker=None, notes=""):
    s = _blank(prs)
    _set_bg(s, PAPER)
    _header(s, title, kicker)
    top = Inches(1.85)
    colw = Inches(5.85)
    # left panel
    _rect(s, Inches(0.7), top, colw, Inches(4.7), LIGHT)
    _text(s, Inches(0.95), top + Inches(0.18), colw - Inches(0.5), Inches(0.5),
          [[R(left_head, 18, True, ACCENT)]])
    lp = [[R("\u2022  ", 15, True, ACCENT), R(t, 15, False, INK)] for t in left_items]
    _text(s, Inches(0.95), top + Inches(0.85), colw - Inches(0.5), Inches(3.6),
          lp, space_after=9)
    # right panel
    rx = Inches(0.7) + colw + Inches(0.4)
    _rect(s, rx, top, colw, Inches(4.7), RGBColor(0xEA, 0xF7, 0xF5))
    _text(s, rx + Inches(0.25), top + Inches(0.18), colw - Inches(0.5), Inches(0.5),
          [[R(right_head, 18, True, ACCENT2)]])
    rp = [[R("\u2022  ", 15, True, ACCENT2), R(t, 15, False, INK)] for t in right_items]
    _text(s, rx + Inches(0.25), top + Inches(0.85), colw - Inches(0.5), Inches(3.6),
          rp, space_after=9)
    _footer(s, idx)
    if notes:
        _notes(s, notes)
    return s


# ----------------------------------------------------------------------------
# Build the deck
# ----------------------------------------------------------------------------
def build(path):
    prs = Presentation()
    prs.slide_width = SW
    prs.slide_height = SH

    # 1 — Title
    title_slide(
        prs,
        "Making Time Uncertainty a First-Class Concept in Linux Timing",
        "Trustworthy timestamps for distributed and AI systems",
        "Time uncertainty as a first-class property  \u00b7  built on Linux + PTP",
    )

    # 2 — Hook
    content_slide(
        prs, "We make this decision constantly",
        [("event A at T\u2081   \u2192   event B at T\u2082   \u2192   \u201cA happened before B\u201d", 0),
         ("Ordering. Causality. \u201cWhich write won?\u201d \u201cWhat caused the stall?\u201d", 1),
         ("The hidden assumption: both timestamps are exact points.", 0),
         ("Clocks disagree. Timestamps are captured at different layers.", 1),
         ("Synchronization data goes stale between updates.", 1)],
        2, kicker="Opening",
        notes="Ask the room: who has debugged a distributed trace where events "
              "looked out of order? Almost every hand goes up. That is the whole talk.")

    # 3 — Two talks
    two_col_slide(
        prs, "Two talks, one story",
        "This talk", ["What is the error bar on a timestamp?",
                      "Timestamps as intervals",
                      "Explicit correctness criteria",
                      "\u201cCan I trust this ordering?\u201d"],
        "Companion talk \u2014 AI profiling",
        ["How do we align events across nodes?",
         "PTP cluster synchronization",
         "Cross-node event correlation",
         "\u201cCan I trace this workload?\u201d"],
        3, kicker="Roadmap",
        notes="Synchronization gives alignment; uncertainty tells you the limits "
              "of that alignment. Position the AI talk as 'why time matters at "
              "scale'; this talk is 'why synchronized time alone is not enough.'")

    # ---- PART 1 ----
    section_slide(prs, "Part 1", "Precise is not the same as correct", 4)

    # 5
    content_slide(
        prs, "We spent a decade chasing precision",
        [("Sub-microsecond PTP is now common on data-center and AI fabrics", 0),
         ("Hardware timestamping in NICs, SmartNICs, DPUs", 0),
         ("Multi-node GPU traces spanning thousands of ranks", 0),
         ("The better our clocks got, the more we trusted them \u2014 implicitly", 0),
         ("Precision raised confidence faster than it raised correctness", 1)],
        5, kicker="The problem",
        notes="Precision is necessary but insufficient. Higher precision made "
              "silent errors both more likely to be relied on and harder to see.")

    # 6
    table_slide(
        prs, "Three ways timestamps quietly mislead",
        ["Domain", "Naive claim", "What can go wrong"],
        [["Ordering", "A before B", "Intervals overlap \u2192 order is unknown"],
         ["Causality", "A caused B", "Off-by-one across nodes \u2192 false cause"],
         ["Compliance", "Log is ordered", "Cannot prove ordering is defensible"]],
        6, kicker="The problem",
        notes="Compliance angle from the abstract: auditors care about defensible "
              "ordering, not nanosecond vanity metrics.")

    # 7
    statement_slide(
        prs,
        "Two events 200 ns apart, each known to \u00b1150 ns.",
        "Their true order is unknown \u2014 and nothing in the timestamp told you so.",
        7,
        notes="This is the aha. The numbers look confident; the reality is "
              "ambiguous. We need the error bar to be part of the data.")

    # ---- PART 2 ----
    section_slide(prs, "Part 2", "A timestamp is an interval", 8)

    # 9
    content_slide(
        prs, "From a point to an interval",
        [("Instead of:  \u201cthe event happened at t\u201d", 0),
         ("Say:  \u201cthe event happened at t \u00b1 U\u201d", 0),
         ("U = the time-uncertainty bound at the moment of observation", 1),
         ("Now applications can ask explicit questions:", 0),
         ("Is ordering between A and B definite, or ambiguous?", 1),
         ("Is this window fresh enough for a compliance decision?", 1)],
        9, kicker="The model",
        notes="This is the core thesis of the abstract. Keep returning to it.")

    # 10 — ordering rule (code-style)
    code_slide(
        prs, "The ordering rule",
        ["  Point model              Interval model",
         "",
         "      |                        [----*----]",
         "      t                    t-U      t     t+U",
         "",
         "",
         "  A is before B   ONLY IF   t_A + U_A  <  t_B - U_B",
         "",
         "  otherwise  ->  AMBIGUOUS   (unknown, not wrong)"],
        10, kicker="The model",
        caption="The overlap region is where causality cannot be resolved from "
                "timestamps alone.",
        notes="Draw this on a whiteboard if possible. 'Unknown' is a valid, "
               "useful answer a system can act on.")

    # 11 — is / is not
    two_col_slide(
        prs, "What uncertainty is \u2014 and is not",
        "U IS",
        ["A conservative bound on clock error, right now",
         "Derived from measurable sync state + configured limits",
         "An explicit input to application logic"],
        "U IS NOT",
        ["A statistical confidence interval (unless you add stats)",
         "A substitute for good clock design",
         "Zero just because PTP reports \u201cSLAVE\u201d"],
        11, kicker="The model",
        notes="Emphasize conservatism: we want a defensible upper bound, not a "
              "best guess.")

    # ---- PART 3 ----
    section_slide(prs, "Part 3", "Where does uncertainty come from?", 12)

    # 13 — the stack
    code_slide(
        prs, "Walk the stack, bottom to top",
        ["  6  Userspace observation delay      <- syscall + scheduling",
         "  5  Kernel -> userspace transfer     <- IRQ, softirq, copy",
         "  4  Timestamp capture point          <- HW vs SW",
         "  3  Network path asymmetry           <- queueing, routing",
         "  2  PTP servo & synchronization      <- offset, delay",
         "  1  Oscillator / PHC hardware        <- drift, temperature"],
        13, kicker="Anatomy",
        caption="Each layer adds error or delay. Only some layers expose metrics.",
        notes="Walk slowly. The point: 'the event time' means different things at "
              "different layers even when everything is 'synced'.")

    # 14 — offset & delay
    content_slide(
        prs, "Layers 1\u20132: hardware & sync offset",
        [("Oscillator: TCXO/OCXO stability (ppb), temperature sensitivity, PHC read latency", 0),
         ("PTP gives estimates, not truths:", 0),
         ("offsetFromMaster \u2014 clock offset estimate", 1),
         ("meanPathDelay \u2014 path-asymmetry estimate", 1),
         ("stepsRemoved \u2014 distance from the grandmaster", 1),
         ("The servo converges; it never mathematically reaches zero", 0)],
        14, kicker="Anatomy",
        notes="PTP believes something about your clock. That belief is an input to "
              "U, not a guarantee.")

    # 15 — capture point table
    table_slide(
        prs, "Layer 4: where was the timestamp taken?",
        ["Method", "Typical error", "Notes"],
        [["PHC hardware RX timestamp", "smallest", "needs NIC/driver support"],
         ["SO_TIMESTAMPING (software)", "larger", "IRQ + softirq delay"],
         ["clock_gettime() in app", "largest", "syscall + scheduling jitter"]],
        15, kicker="Anatomy",
        notes="Critical for profiling: GPU, NIC and CPU may live in different "
              "timestamp domains even when 'synced'.")

    # 16 — kernel path
    content_slide(
        prs, "Layers 3 & 5: network and kernel path",
        [("meanPathDelay is a mean \u2014 not a constant; congestion spikes it", 0),
         ("AI fabrics: asymmetric up/down links, leaf-switch queueing", 1),
         ("Linux exposes useful data \u2014 but not as one package:", 0),
         ("PTP_SYS_OFFSET / _EXTENDED \u2014 PHC vs system clock", 1),
         ("SO_TIMESTAMPING \u2014 ingress / egress timestamps", 1),
         ("ptp4l management API \u2014 offset, delay, ingress time", 1)],
        16, kicker="Anatomy",
        notes="Foreshadow the kernel-gaps section: ingredients exist, the single "
              "'current uncertainty' API does not.")

    # 17 — staleness (the big one)
    code_slide(
        prs, "Layer that everyone forgets: staleness",
        ["  Between PTP updates, the clock drifts.",
         "",
         "  U_drift  =  elapsed_time  x  max_drift_rate",
         "",
         "  Example:  100 ppm  x  1 s   =   100 microseconds",
         "",
         "  A perfect offset at sync ingress still becomes",
         "  a GROWING interval a moment later."],
        17, kicker="Anatomy",
        caption="Staleness turns a point sync measurement into a growing interval "
                "\u2014 this is what the model daemon implements.",
        notes="Many tools show offset but never show the interval growing since "
              "the last correction. This is the term the daemon makes explicit.")

    # ---- PART 4 ----
    section_slide(prs, "Part 4", "Turning PTP state into a bound", 18)

    # 19 — datasets
    table_slide(
        prs, "PTP answers: what does the protocol believe?",
        ["Dataset (via ptp4l)", "Provides"],
        [["CURRENT_DATA_SET", "offsetFromMaster, meanPathDelay, stepsRemoved"],
         ["PORT_DATA_SET", "port state, logSyncInterval"],
         ["TIME_STATUS_NP", "sync ingress time, grandmaster identity"],
         ["PORT_HWCLOCK_NP", "PHC index (optional)"]],
        19, kicker="PTP \u2192 bound",
        notes="PTP does NOT answer 'what is my application-level timestamp error "
              "bar?'. We build that on top.")

    # 20 — ingress anchor
    code_slide(
        prs, "Ingress time is the drift anchor",
        ["  TIME_STATUS_NP.ingress_time",
         "     = when the last sync event arrived (PHC time)",
         "",
         "  drift_ns = (now_mono - ingress_mono)",
         "                 * max_drift_ppb / 1e9",
         "",
         "  Uncertainty grows between sync messages",
         "  even when the offset display looks flat."],
        20, kicker="PTP \u2192 bound",
        notes="This makes 'staleness' concrete: anchor at ingress, extrapolate at "
              "read time using a worst-case drift bound.")

    # 21 — the formula
    statement_slide(
        prs,
        "total_uncertainty_ns = |offset| + |path_delay| + drift",
        "Example: offset 80 ns + delay 120 ns + drift 50 ns  =  250 ns bound.",
        21,
        notes="This is the exact formula the library computes. Honest: it is a "
              "practical model, not a full Allan-deviation analysis.")

    # 22 — port state trust
    table_slide(
        prs, "Sync status is a prerequisite, not a proof",
        ["Port state", "Meaning for uncertainty"],
        [["SLAVE", "actively disciplining \u2014 bounds meaningful"],
         ["UNCALIBRATED", "converging \u2014 bounds unstable"],
         ["LISTENING / FAULTY", "do not trust ordering claims"],
         ["ptp4l disconnected", "hold last anchor + drift keeps growing"]],
        22, kicker="PTP \u2192 bound",
        notes="'Synchronized' is necessary but not sufficient. The last row is the "
              "interesting failure mode the daemon handles explicitly.")

    # ---- PART 5 ----
    section_slide(prs, "Part 5", "A model implementation: ptp-uncertainty", 23)

    # 24 — architecture
    code_slide(
        prs, "Architecture",
        ["  ptp4l",
         "    |  Unix management socket (poll offset/delay/ingress)",
         "    v",
         "  ptp_unc_dmn        <- daemon: collects + anchors",
         "    |  /ptp_uncertainty (POSIX shared memory)",
         "    v",
         "  libptp_unc.so      <- client lib: extrapolates at read time",
         "    |",
         "    v",
         "  applications       <- get a live bound, no PTP code needed"],
        24, kicker="Implementation",
        caption="No direct PHC access required. A live bound, not just the last "
                "offset snapshot.",
        notes="Transition from theory to something the audience can actually run.")

    # 25 — what daemon collects
    table_slide(
        prs, "What the daemon collects",
        ["Field", "Source"],
        [["offset, delay, steps removed", "CURRENT_DATA_SET"],
         ["port state, sync interval", "PORT_DATA_SET"],
         ["ingress time, grandmaster id", "TIME_STATUS_NP"],
         ["PHC index (optional)", "PORT_HWCLOCK_NP"]],
        25, kicker="Implementation",
        notes="Auto features: poll interval derived from logSyncInterval (>=2x "
              "sync rate); optional PHC index autodetection.")

    # 26 — client API
    code_slide(
        prs, "Client API",
        ["  struct ptp_unc_handle *h = ptp_unc_open();",
         "  struct ptp_uncertainty u;",
         "",
         "  ptp_unc_get(h, &u);            // uncertainty at now",
         "  ptp_unc_get_at(h, &u, t_mono); // at a given monotonic t",
         "",
         "  // u.total_uncertainty_ns, u.drift_ns",
         "  // u.is_synchronized, u.ptp4l_connected",
         "  // u.age_ns  (snapshot freshness != drift anchor)",
         "",
         "  ptp_unc_close(h);"],
        26, kicker="Implementation",
        caption="Clients extrapolate at read time; age_ns (snapshot freshness) is "
                "distinct from the drift term.",
        notes="Clarify snapshot age vs drift \u2014 a common confusion and a good "
              "teaching moment.")

    # 27 — failure behavior
    code_slide(
        prs, "Behavior under failure = explicit correctness",
        ["  // ptp4l restarts or disconnects:",
         "  //   - preserve last valid sync anchor",
         "  //   - set ptp4l_connected = 0",
         "  //   - drift KEEPS growing from the held anchor",
         "",
         "  if (!u.ptp4l_connected ||",
         "      u.total_uncertainty_ns > threshold)",
         "      mark_event_ordering_untrusted();"],
        27, kicker="Implementation",
        caption="The application decides what 'trustworthy enough' means \u2014 the "
                "daemon just keeps the bound honest.",
        notes="This is the abstract's phrase 'evaluate temporal correctness "
              "explicitly' turned into three lines of code.")

    # ---- PART 6 ----
    section_slide(prs, "Part 6", "Payoff: profiling AI clusters", 28)

    # 29 — bridge
    statement_slide(
        prs,
        "PTP aligns cross-node events. Uncertainty says when that alignment can carry a causal claim.",
        "Synchronization solves alignment; uncertainty solves the epistemic limits of alignment.",
        29,
        notes="Explicit bridge to the companion talk. Speak to both audiences in "
              "the room here.")

    # 30 — AI example + table
    table_slide(
        prs, "512-GPU trace: what bounds add",
        ["Capability", "Sync only", "Sync + uncertainty"],
        [["Align traces visually", "yes", "yes"],
         ["Merge cross-node spans", "fragile", "confidence-gated"],
         ["Detect bottlenecks", "heuristic", "defensible"],
         ["Ordering disputes", "hidden", "explicit ambiguity"],
         ["Trace-buffer / merge window", "fixed", "adapts to live U"]],
        30, kicker="AI profiling",
        notes="Scenario: rank-42 launch at T, rank-7 stall at T+300 ns. If U ~ 500 "
              "ns on both, ordering is ambiguous \u2014 the 'launch caused stall' "
              "conclusion is false causality and wasted engineering time.")

    # ---- PART 7 ----
    section_slide(prs, "Part 7", "Linux APIs: what we have, what we lack", 31)

    # 32 — have vs missing
    two_col_slide(
        prs, "The kernel gives ingredients, not the recipe",
        "Available today",
        ["SO_TIMESTAMPING \u2014 HW/SW RX/TX timestamps",
         "PTP_SYS_OFFSET(_EXTENDED) \u2014 PHC \u2194 system",
         "ptp4l mgmt socket \u2014 offset, delay, ingress",
         "/dev/ptpN \u2014 freq adjust, ext timestamps"],
        "Not exposed / not standardized",
        ["Oscillator stability (Allan deviation)",
         "Calibration age + temperature model",
         "Per-read PHC access-latency bound",
         "A unified \u201cstaleness since last discipline\u201d"],
        31 + 1, kicker="Kernel limits",
        notes="Matches the abstract's conclusion: frequency offset is available, "
              "but oscillator stability and calibration staleness are not \u2014 so "
              "precise bounds still need operator config and hardware knowledge. "
              "Do not oversell automation.")

    # ---- CLOSE ----
    content_slide(
        prs, "Takeaways",
        [("Timestamps are intervals \u2014 design systems around t \u00b1 U", 0),
         ("PTP provides inputs, not a complete uncertainty model", 0),
         ("Staleness / drift is the term most tools ignore \u2014 don\u2019t", 0),
         ("Explicit bounds enable explicit correctness for ordering & compliance", 0),
         ("For AI profiling: sync aligns data, uncertainty qualifies causality", 0)],
        33, kicker="Closing",
        notes="End on the bridge sentence: better profiles need better time \u2014 "
              "and better time needs error bars.")

    # 34 — thanks / QA
    s = _blank(prs)
    _set_bg(s, INK)
    _rect(s, 0, Inches(3.0), SW, Inches(0.09), ACCENT)
    _rect(s, 0, Inches(3.09), Inches(4.2), Inches(0.09), ACCENT2)
    _text(s, Inches(0.9), Inches(2.1), Inches(11.5), Inches(1.0),
          [[R("Questions?", 44, True, WHITE)]])
    _text(s, Inches(0.92), Inches(3.4), Inches(11.5), Inches(1.4),
          [[R("Treat time as an interval. Make the error bar part of the data.",
              20, False, RGBColor(0xC7, 0xD2, 0xF0))]])
    _text(s, Inches(0.92), Inches(5.6), Inches(11.5), Inches(0.8),
          [[R("ptp-uncertainty  \u00b7  daemon + libptp_unc.so + watch_uncertainty",
              16, False, RGBColor(0x9A, 0xA6, 0xC4), FONT_MONO)]])
    _notes(s, "Offer to collaborate with profiling-tool authors. Have the demo "
              "plot ready as a backup.")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    prs.save(path)
    return len(prs.slides._sldIdLst)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "time-uncertainty-error-bar.pptx")
    out = sys.argv[1] if len(sys.argv) > 1 else default
    n = build(out)
    print(f"Wrote {n} slides -> {out}")
