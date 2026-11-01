#!/usr/bin/env python3
"""Batch audio runner and interactive text client for the VoiceOps 2026 submission."""
from __future__ import annotations
import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from voiceops import LLMClient, SupportAgent

AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}


def _dataset_dir(arg: str | None) -> Path:
    candidate = arg or os.getenv("ZENTROMART_DATA_DIR", "")
    if not candidate:
        raise RuntimeError("Set ZENTROMART_DATA_DIR or pass --data-dir pointing to the extracted dataset folder.")
    p = Path(candidate).resolve()
    if not (p / "kb").is_dir() or not (p / "data").is_dir():
        raise RuntimeError(f"{p} is not the extracted Capstone_Project_Dataset_FTTT_2026 folder (expected kb/ and data/).")
    return p


def _session_key(path: Path) -> str:
    # Files named conversationID_turnNN.wav share state; all other files are independent sessions.
    match = re.match(r"^(.+?)[_-](?:turn|t)(?:[_-]?\d+)$", path.stem, re.I)
    return match.group(1) if match else path.stem


def _run_audio(agent, input_dir: Path, output_dir: Path) -> int:
    from voiceops.voice import GnaniVoice
    files = sorted([p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTS])
    if not files:
        raise RuntimeError(f"No audio files found in {input_dir}. Supported extensions: {', '.join(sorted(AUDIO_EXTS))}")
    gnani = GnaniVoice()
    output_dir.mkdir(parents=True, exist_ok=True)
    sessions = {}
    rows = []
    for audio in files:
        relative = audio.relative_to(input_dir)
        stem = audio.stem
        target_dir = output_dir / relative.parent / stem
        target_dir.mkdir(parents=True, exist_ok=True)
        session_key = _session_key(audio)
        session = sessions.setdefault(session_key, agent.new_session())
        try:
            heard = gnani.transcribe(audio)
            result = agent.respond(heard, session=session)
            # Spoken text is normalized to short sentences by the agent prompt.
            reply_audio = target_dir / "reply.wav"
            gnani.synthesize(result["answer"], reply_audio)
            record = {
                "input_file": str(relative), "transcript": heard, "answer": result["answer"],
                "decision": result.get("decision", "answer"), "sources": result.get("sources", []),
                "retrieved": result.get("retrieved", []), "tool_events": result.get("tool_events", []),
                "reply_audio": str(reply_audio.relative_to(output_dir)), "error": "",
            }
        except Exception as exc:
            record = {"input_file": str(relative), "transcript": "", "answer": "", "decision": "error",
                      "sources": [], "retrieved": [], "tool_events": [], "reply_audio": "", "error": f"{type(exc).__name__}: {exc}"}
        (target_dir / "result.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        (target_dir / "transcript.txt").write_text(record["transcript"], encoding="utf-8")
        (target_dir / "reply.txt").write_text(record["answer"], encoding="utf-8")
        rows.append(record)
        print(f"[{len(rows)}/{len(files)}] {relative}: {record['decision']}")
    with (output_dir / "results.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (output_dir / "results.csv").open("w", encoding="utf-8-sig", newline="") as f:
        cols = ["input_file", "transcript", "answer", "decision", "sources", "retrieved", "tool_events", "reply_audio", "error"]
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            r = dict(row)
            for k in ["sources", "retrieved", "tool_events"]:
                r[k] = json.dumps(r.get(k, []), ensure_ascii=False)
            writer.writerow({k: r.get(k, "") for k in cols})
    failures = sum(bool(r.get("error")) for r in rows)
    print(f"Processed {len(rows)} audio file(s); failures={failures}. Results: {output_dir}")
    return 1 if failures else 0


def _interactive(agent) -> int:
    session = agent.new_session()
    print("ZentroMart AI support · type 'exit' to stop. Order lookups require verification.")
    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0
        if msg.lower() in {"exit", "quit", ":q"}:
            return 0
        result = agent.respond(msg, session=session)
        print(f"Agent: {result['answer']}")
        if result.get("sources"):
            print("  [evidence: " + ", ".join(result["sources"]) + "]")


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Run the ZentroMart VoiceOps support agent.")
    parser.add_argument("--data-dir", help="Path to extracted Capstone_Project_Dataset_FTTT_2026 folder")
    parser.add_argument("--audio-dir", help="Folder of customer audio files to transcribe and answer with Gnani STT/TTS")
    parser.add_argument("--output-dir", default="sample_outputs", help="Where to save transcript, replies, source evidence and reply WAVs")
    parser.add_argument("--interactive", action="store_true", help="Start a text-based interactive session")
    parser.add_argument("--check", action="store_true", help="Check dataset, retrieval initialization and environment configuration")
    args = parser.parse_args()
    try:
        data_dir = _dataset_dir(args.data_dir)
        agent = SupportAgent(data_dir)
        if args.check:
            print("Dataset path:", data_dir)
            print("Retrievable chunks:", len(agent.retriever.chunks))
            print("LLM configured:", agent.llm.configured)
            print("Gnani key configured:", bool(os.getenv("GNANI_API_KEY", "").strip()))
            print("Optional semantic embeddings:", bool(agent.retriever._semantic_model))
            print("PASS: project and retrieval initialized")
            if not agent.llm.configured:
                print("NOTE: set LLM_API_KEY/LLM_BASE_URL/LLM_MODEL before asking questions")
            return 0
        if args.audio_dir:
            return _run_audio(agent, Path(args.audio_dir).resolve(), Path(args.output_dir).resolve())
        if args.interactive:
            if not agent.llm.configured:
                raise RuntimeError("Set LLM_API_KEY, LLM_BASE_URL and LLM_MODEL before starting an interactive session.")
            return _interactive(agent)
        parser.print_help()
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
