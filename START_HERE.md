# Start here

This repository contains my VoiceOps 2026 ZentroMart support-agent implementation and the final project artifacts.

## What is included

- Four-step implementation: prompt-only baseline, RAG, multi-turn conversation/tools, and Gnani STT/TTS.
- Full evaluation report (`report.pdf`) and screen-recorded demo (`demo.mp4`).
- Python source, tests, system-design notes and sample voice outputs with evidence traces.
- `.env.example` with variable names only. No API credentials are included.

## Before running

1. Download and extract the course-provided `Capstone_Project_Dataset_FTTT_2026.zip` separately.
2. Follow the setup instructions in `README.md`.
3. Copy `.env.example` to `.env`, set the dataset path, and add your own LLM and Gnani credentials. Never commit `.env`.
4. Run `python run.py --check` to validate the local setup.

## Main commands

```bash
python run.py --interactive
python run.py --audio-dir customer_audio/ --output-dir sample_outputs/
python evaluate.py --retrieval-only --top-k 6 --output-dir evaluation_results/
python evaluate.py --top-k 6 --output-dir evaluation_results/
pytest -q
```

The full evaluation uses API quota. A smoke test is available by adding `--limit-questions 5 --limit-conversations 2` to the evaluation command. See the root `README.md` for details, metrics and limitations.

## Final artifacts

- `report.pdf`
- `demo.mp4` (maximum two minutes)
- Public repository: https://github.com/samriddhig-gif/SG-zentromart-voiceops-agent
