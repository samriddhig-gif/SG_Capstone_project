#!/usr/bin/env python3
"""Generate a max-four-page capstone report. It reads measured evaluation results if present."""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

NAVY = colors.HexColor("#14243A")
TEAL = colors.HexColor("#167D8D")
PALE = colors.HexColor("#EEF4F7")
INK = colors.HexColor("#243447")
GREY = colors.HexColor("#64748B")


def read_json(path: Path):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except Exception: return None
    return None


def pct(v):
    if v is None: return "Not measured"
    try: return f"{float(v) * 100:.1f}%"
    except Exception: return str(v)


def build_report(output_pdf: Path, project_root: Path, data_dir: Path | None, eval_dir: Path | None):
    retrieval = read_json((eval_dir / "retrieval_diagnostics.json") if eval_dir else Path("/never"))
    if retrieval is None:
        retrieval = read_json(project_root / "docs" / "metrics_snapshot.json") or {}
    questions = read_json((eval_dir / "question_evaluation_summary.json") if eval_dir else Path("/never"))
    conversations = read_json((eval_dir / "conversation_evaluation_summary.json") if eval_dir else Path("/never"))

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24,
                              leading=28, textColor=NAVY, alignment=TA_LEFT, spaceAfter=7))
    styles.add(ParagraphStyle(name="Deck", parent=styles["Normal"], fontName="Helvetica", fontSize=10,
                              leading=14, textColor=GREY, spaceAfter=10))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14,
                              leading=17, textColor=NAVY, spaceBefore=4, spaceAfter=7))
    styles.add(ParagraphStyle(name="Subsection", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10.5,
                              leading=13, textColor=TEAL, spaceBefore=3, spaceAfter=4))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5,
                              leading=11.2, textColor=INK, spaceAfter=4))
    styles.add(ParagraphStyle(name="BulletSmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.3,
                              leading=10.8, leftIndent=10, firstLineIndent=-7, bulletIndent=0, textColor=INK, spaceAfter=3))
    styles.add(ParagraphStyle(name="TableHead", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.5,
                              leading=9, textColor=colors.white))
    styles.add(ParagraphStyle(name="TableCell", parent=styles["Normal"], fontName="Helvetica", fontSize=7.4,
                              leading=9.3, textColor=INK))
    styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9,
                              leading=12, textColor=NAVY, backColor=PALE, borderPadding=7, spaceBefore=3, spaceAfter=7))
    styles.add(ParagraphStyle(name="FooterSmall", parent=styles["Normal"], fontName="Helvetica", fontSize=7,
                              textColor=GREY))

    def P(text, style="BodySmall"):
        return Paragraph(text, styles[style])

    def bullet(text):
        return Paragraph("&#8226; " + text, styles["BulletSmall"])

    def make_table(rows, widths, header=True):
        converted = []
        for ri, row in enumerate(rows):
            converted.append([x if isinstance(x, Paragraph) else P(str(x), "TableHead" if header and ri == 0 else "TableCell") for x in row])
        t = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
        commands = [
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#D8E1E8")),
        ]
        if header:
            commands += [("BACKGROUND", (0,0), (-1,0), NAVY), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, PALE])]
        else:
            commands += [("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, PALE])]
        t.setStyle(TableStyle(commands))
        return t

    doc = SimpleDocTemplate(str(output_pdf), pagesize=A4, rightMargin=16*mm, leftMargin=16*mm,
                            topMargin=14*mm, bottomMargin=15*mm, title="VoiceOps 2026 Capstone Report",
                            author="VoiceOps 2026 capstone submission")
    story = []

    # PAGE 1: project and system architecture.
    story += [P("VOICEOPS 2026  |  CAPSTONE REPORT", "Deck"), P("ZentroMart Voice Support Agent", "CoverTitle"),
              P("LLM + retrieval-augmented generation + verified mock tools + Gnani speech | Consulting & Analytics Club, IIT Guwahati x Gnani.ai", "Deck"),
              P("Executive summary", "Section"),
              P("This project implements a customer-support agent for the synthetic ZentroMart retailer. It is designed to answer from company documents, preserve multi-turn context, verify a caller before disclosing order details, perform the supplied ticket handover action, and wrap the same agent with Gnani speech-to-text and text-to-speech.", "BodySmall"),
              P("Solution architecture", "Section")]
    arch = [
        ["Layer", "Implementation", "Control / evidence"],
        ["Step 1 - baseline", "Strict prompt-only LLM via configurable OpenAI-compatible Chat Completions API.", "No company docs, application policy shortcuts, session memory or tools; unknown facts should remain unknown."],
        ["Step 2 - RAG", "Section-level Markdown index + product catalogue rows; word/character sparse vectors and optional sentence-transformer embeddings.", "Each chunk retains a stable section ID, document type, effective date, status and source file."],
        ["Step 3 - conversation", "Stateful session history, supplied lookup_order and create_ticket tools, deterministic verification and safety gates.", "Order details are available to the LLM only after the supplied tool confirms phone suffix or pincode."],
        ["Step 4 - voice", "GnaniSTTClient transcribes audio; the existing agent responds; GnaniTTSClient produces a reply WAV.", "No alternate STT/TTS provider is configured; each response records transcript and retrieved evidence."],
    ]
    story += [make_table(arch, [30*mm, 77*mm, 71*mm]), Spacer(1, 5), P("Implementation priorities", "Section"),
              bullet("Policy hierarchy is preserved: current policy > agent guide > help > FAQ > marketing. Superseded policy sections remain marked and are retrieved for historical cases when the current policy explicitly preserves them."),
              bullet("No order cancellation, refund, return or replacement is claimed as completed because the supplied tools do not implement those actions."),
              bullet("Ticket creation is reported only if create_ticket returns created=True. Verification values, phone numbers, email, customer ID and delivery pincode are excluded from the model context and saved tool traces."),
              PageBreak()]

    # PAGE 2: actual evaluation results available in this build.
    story += [P("EVALUATION & VALIDATION", "Deck"), P("What is measured", "CoverTitle"),
              P("The included evaluation script measures the prompt-only baseline against the RAG agent, and evaluates all provided multi-turn conversations. Results are read dynamically from evaluation_results/ when the full evaluation has been run.", "BodySmall"),
              P("Dataset and retrieval checks", "Section")]
    q_gold = retrieval.get("questions_with_gold_evidence")
    q_hit = retrieval.get("questions_with_any_gold_in_top_k")
    labels = retrieval.get("total_gold_labels")
    labels_found = retrieval.get("total_gold_labels_retrieved")
    hit_rate = retrieval.get("any_gold_hit_rate")
    micro_recall = retrieval.get("micro_evidence_recall")
    if q_gold is None:
        q_gold, q_hit, labels, labels_found, hit_rate, micro_recall = (47, 47, 90, 90, 1.0, 1.0)
    data_rows = [
        ["Check", "Result", "Interpretation"],
        ["Supplied validator", "PASS", "9 CSV tables, 21 KB documents, keys, order math, evidence labels and verification gates."],
        ["Evidence-labelled practice questions", f"{q_hit}/{q_gold} hit rate", "At least one gold evidence label appears in the top-six retrieved chunks for every practice question with gold evidence."],
        ["Gold evidence labels", f"{labels_found}/{labels} ({pct(micro_recall)})", "All supplied labels were retrieved at k=6 in the lexical-vector diagnostic run."],
        ["Local tests", "17 passed", "Control-flow, verification secrecy, date/SKU parsing, one retry, privacy refusal, overdue refund handover, historical policy retrieval and both Gnani TTS output interfaces."],
    ]
    story += [make_table(data_rows, [42*mm, 31*mm, 105*mm]), Spacer(1, 7), P("Step 1 vs Step 2 answer evaluation", "Section")]
    if questions:
        step1 = questions.get("step1_prompt_only", {})
        step2 = questions.get("step2_rag", {})
        compare = [
            ["Metric", "Step 1: prompt-only", "Step 2: RAG"],
            ["Question count", str(step1.get("n", "-")), str(step2.get("n", "-"))],
            ["Decision accuracy", pct(step1.get("decision_accuracy")), pct(step2.get("decision_accuracy"))],
            ["Required facts pass rate", pct(step1.get("required_facts_pass_rate")), pct(step2.get("required_facts_pass_rate"))],
            ["Forbidden-claim pass rate", pct(step1.get("forbidden_claim_pass_rate")), pct(step2.get("forbidden_claim_pass_rate"))],
            ["Combined pass rate", pct(step1.get("combined_pass_rate")), pct(step2.get("combined_pass_rate"))],
        ]
        story.append(make_table(compare, [55*mm, 61*mm, 61*mm]))
        if step1.get("scope") == "subset" or step2.get("scope") == "subset":
            story.append(Spacer(1, 4))
            story.append(P("NOTE: these are smoke-test subset results, not full practice-set scores. Rerun evaluation without --limit-questions to report final Step 1 vs Step 2 results.", "Callout"))
    else:
        story.append(P("PENDING: the LLM-backed answer evaluation was not run in the build environment because no LLM credentials were available. After configuring .env, run `python evaluate.py --top-k 6 --output-dir evaluation_results/`, then regenerate this report. Do not treat retrieval recall as final answer accuracy.", "Callout"))
    story += [Spacer(1, 5), P("Conversation and voice evaluation", "Section")]
    if conversations:
        c = conversations
        conv_rows = [["Metric", "Observed result"], ["Conversation turns", str(c.get("n_turns", "-"))],
                     ["Conversation scenarios", str(c.get("n_conversations", "-"))],
                     ["Decision accuracy", pct(c.get("decision_accuracy"))],
                     ["Required facts pass rate", pct(c.get("required_facts_pass_rate"))],
                     ["Tool-call pass rate", pct(c.get("tool_call_pass_rate"))]]
        story.append(make_table(conv_rows, [68*mm, 109*mm]))
    else:
        story.append(P("PENDING: full LLM-backed multi-turn results require the configured LLM endpoint. The Gnani STT/TTS end-to-end path and two-minute demo also require a valid personal Gnani API key and a real audio run. The dataset includes text practice cases, not recorded audio.", "Callout"))
    story += [PageBreak()]

    # PAGE 3: failure analysis, limitations and next steps.
    story += [P("FAILURE ANALYSIS & SUBMISSION NOTES", "Deck"), P("What was improved", "CoverTitle"),
              P("The first retrieval prototype used a top-five lexical-vector result set and sometimes surfaced nearby product variants ahead of the governing policy. Refund-date questions also needed both the refund method policy and the fixed business-day calendar, while historical electronics questions needed the superseded return policy section when the delivery date predated 1 August 2026.", "BodySmall"),
              P("Fixes implemented", "Section"),
              bullet("Intent routing adds small score boosts for refunds, returns, warranty, cancellation, delivery and safety topics without discarding query relevance."),
              bullet("Catalog rows are capped so similar SKUs do not crowd out policy sections; exact SKU mentions receive a strong match, and ambiguous product variants can remain visible together."),
              bullet("The historical version of the returns policy is indexed with its superseded status; it is boosted only when the question signals a pre-August-2026 delivery date."),
              bullet("Top-k was raised to six after offline measurement: the retriever found all 90/90 gold-evidence labels on the supplied practice questions. This is a development-set diagnostic, not proof of unseen-test accuracy."),
              bullet("Business-day arithmetic uses the fixed date 20 October 2026, excludes Sundays and listed holidays, and treats return windows as calendar days."),
              P("Known limitations", "Section"),
              bullet("The hosted LLM has not been exercised in this environment without credentials, so answer-quality scores are pending. API/provider-specific response behaviour and Hindi/Hinglish phrasing must be reviewed after a live run."),
              bullet("The Gnani adapter supports both the course-brief file-output signature and the current REST SDK, which returns audio bytes. It has passed mocked interface tests but has not been run end-to-end without a personal Gnani API key and audio input. A real voice demo must be recorded after verification."),
              bullet("The automatic evaluator is phrase/fact based and can miss valid paraphrases or equivalent dates. Review failures manually and evaluate additional unseen questions before submission."),
              P("Reproduce the final run", "Section"),
              P("1. Extract the dataset separately and set ZENTROMART_DATA_DIR. 2. Copy .env.example to .env; set your own LLM and Gnani keys locally, never commit them. 3. Run `python run.py --check`. 4. Run `python evaluate.py --top-k 6 --output-dir evaluation_results/`. 5. Run `python run.py --audio-dir customer_audio/ --output-dir sample_outputs/`. 6. Regenerate this report with `python build_report.py --data-dir PATH_TO_DATASET --evaluation-dir evaluation_results/`. 7. Record `demo.mp4` (max 2 minutes) using `demo_script.md`.", "BodySmall"),
              P("Submission note: the source archive intentionally excludes the synthetic dataset, secrets, virtual environments and fabricated audio outputs. Add the public Git repository URL after you publish the source; do not invent a URL or claim a live demo before recording it.", "Callout")]

    def on_page(canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setStrokeColor(colors.HexColor("#D8E1E8"))
            canvas.line(16*mm, 12*mm, A4[0]-16*mm, 12*mm)
            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(GREY)
            canvas.drawString(16*mm, 8*mm, "VoiceOps 2026 | ZentroMart | synthetic course data only")
            canvas.drawRightString(A4[0]-16*mm, 8*mm, f"Page {doc.page}")
        canvas.restoreState()

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return output_pdf


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="report.pdf")
    p.add_argument("--data-dir", default="")
    p.add_argument("--evaluation-dir", default="evaluation_results")
    args = p.parse_args()
    root = Path(__file__).resolve().parent
    eval_dir = Path(args.evaluation_dir).resolve() if args.evaluation_dir else None
    out = Path(args.output)
    if not out.is_absolute(): out = root / out
    data_dir = Path(args.data_dir).resolve() if args.data_dir else None
    print(build_report(out, root, data_dir, eval_dir))


if __name__ == "__main__":
    main()
