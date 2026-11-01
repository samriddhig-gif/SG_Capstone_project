#!/usr/bin/env python3
"""Evaluate retrieval offline, or run LLM-backed single-turn and conversation evaluation."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from voiceops import HybridRetriever, LLMClient, SupportAgent
from voiceops.evaluation import evaluate_questions, evaluate_conversations


def main() -> int:
    load_dotenv(ROOT / ".env")
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", help="Path to extracted dataset")
    p.add_argument("--output-dir", default="evaluation_results")
    p.add_argument("--retrieval-only", action="store_true", help="Run evidence retrieval diagnostics without an LLM API")
    p.add_argument("--top-k", type=int, default=6)
    p.add_argument("--skip-conversations", action="store_true")
    p.add_argument("--limit-questions", type=int, default=None,
                   help="Optional first-N question subset for an API smoke test; omit for the full 52-question suite")
    p.add_argument("--limit-conversations", type=int, default=None,
                   help="Optional first-N conversation subset for an API smoke test; omit for all 23 conversations")
    args = p.parse_args()
    data_arg = args.data_dir or os.getenv("ZENTROMART_DATA_DIR", "")
    if not data_arg:
        print("Set ZENTROMART_DATA_DIR or pass --data-dir.", file=sys.stderr)
        return 2
    data_dir = Path(data_arg).resolve()
    if not (data_dir / "practice" / "questions.csv").exists():
        print(f"Could not find practice/questions.csv under {data_dir}", file=sys.stderr)
        return 2
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    retriever = HybridRetriever(data_dir)
    retrieval = retriever.gold_evidence_recall(data_dir / "practice" / "questions.csv", k=args.top_k)
    (out / "retrieval_diagnostics.json").write_text(
        json.dumps({k: v for k, v in retrieval.items() if k != "details"}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    import pandas as pd
    pd.DataFrame(retrieval["details"]).to_csv(out / "retrieval_diagnostics.csv", index=False, encoding="utf-8-sig")
    print("Retrieval diagnostics:", json.dumps({k: v for k, v in retrieval.items() if k != "details"}, ensure_ascii=False, indent=2))
    if args.retrieval_only:
        return 0

    llm = LLMClient()
    if not llm.configured:
        print("LLM_API_KEY is not configured; ran retrieval diagnostics only. Set credentials for full answer evaluation.", file=sys.stderr)
        return 2
    agent = SupportAgent(data_dir, llm=llm, retriever=retriever, top_k=args.top_k)
    q_summary = evaluate_questions(agent, data_dir / "practice" / "questions.csv", out,
                                   top_k=args.top_k, max_questions=args.limit_questions)
    print("Question evaluation:", json.dumps(q_summary, ensure_ascii=False, indent=2))
    if not args.skip_conversations:
        c_summary = evaluate_conversations(agent, data_dir / "practice" / "conversations.csv", out,
                                           max_conversations=args.limit_conversations)
        print("Conversation evaluation:", json.dumps(c_summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
