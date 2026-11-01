# ZentroMart VoiceOps Agent | VoiceOps 2026

**Author:** Samriddhi Gupta  
**Repository:** https://github.com/samriddhig-gif/SG-zentromart-voiceops-agent  
**Capstone:** Consulting & Analytics Club, IIT Guwahati × Gnani.ai

An AI-powered customer-support agent for the fictional Indian e-commerce retailer ZentroMart. I built the system in four stages: a prompt-only baseline, evidence-grounded retrieval (RAG), multi-turn conversation and verified support tools, and voice input/output using Gnani.

> **Dataset:** The course dataset is intentionally not included in this repository. Download `Capstone_Project_Dataset_FTTT_2026.zip` from the capstone materials and extract it separately. Never upload the dataset or real customer data.

## What I built

| Layer | Implementation |
|---|---|
| Prompt-only baseline | OpenAI-compatible chat-completions interface, without company evidence or tools |
| RAG | Section-aware retrieval from 21 knowledge-base Markdown files and the product catalogue; evidence IDs and source metadata are retained |
| Conversation and tools | Session history, `lookup_order`, `create_ticket`, identity verification and privacy safeguards |
| Voice | Gnani speech-to-text (STT) → the same support agent → Gnani text-to-speech (TTS) |

The retriever uses lexical word/character matching with optional sentence-transformer embeddings. Current policies take precedence over agent guides, help pages, FAQs and marketing material. Superseded policy sections are handled separately.

### Safety and operational controls

- Order-specific details are withheld until the caller supplies the order ID and verifies using the registered phone suffix or delivery pincode.
- Verification values and sensitive customer details are excluded from the model context and saved tool traces.
- The agent confirms ticket creation only when the tool returns `created=True`.
- It does not claim to cancel, refund, return or replace an order because those actions are not available in the supplied mock tools.
- The project uses synthetic course data only.

## Evaluation snapshot

The figures below are from the full evaluation reported in `report.pdf`:

| Metric | Prompt-only baseline | RAG |
|---|---:|---:|
| Decision accuracy (52 questions) | 9.6% | 82.7% |
| Required-facts pass rate | 15.4% | 75.0% |
| Forbidden-claim pass rate | 100.0% | 100.0% |
| Combined pass rate | 7.7% | 61.5% |
| Evidence recall on answerable questions | 0.0% | 97.9% |

Conversation evaluation covered 23 scenarios and 96 turns: 78.1% decision accuracy, 85.4% required-facts pass rate, 100% forbidden-claim pass rate and 100% tool-call pass rate.

The separate offline retrieval diagnostic at `k=6` retrieved all 90 gold evidence labels across the 47 evidence-labelled practice questions (100%). This retrieval diagnostic is distinct from the end-to-end RAG evidence-recall metric above. The automatic evaluator is phrase-based and may miss valid paraphrases. Results are based on the supplied practice set, not unseen customer queries.

I also ran the Groq-hosted LLM (`openai/gpt-oss-120b`) and processed three short audio recordings through Gnani STT, the agent and Gnani TTS. Sample transcripts, replies, WAV files and evidence traces are in `sample_outputs/`.

## Repository structure

```text
.
├── README.md
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── run.py
├── evaluate.py
├── build_report.py
├── report.pdf
├── demo.mp4
├── src/voiceops/
├── tests/
├── docs/
└── sample_outputs/
```

## Setup

Python 3.10–3.12 is recommended.

1. Download and extract the course dataset separately.
2. Create and activate a virtual environment.
3. Install dependencies and configure environment variables.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and edit it. Set `ZENTROMART_DATA_DIR` to the extracted dataset folder. Add your own LLM and Gnani API keys locally. The example LLM endpoint/model is the Groq configuration used for the reported live evaluation; provider limits and model availability can change.

**Never commit `.env`, API keys, the dataset, or real customer information.** `.env` is excluded by `.gitignore`.

## Run the project

Check the configuration and dataset path:

```bash
python run.py --check
```

Start an interactive text session:

```bash
python run.py --interactive
```

Run the required batch voice workflow on a folder of audio clips:

```bash
python run.py --audio-dir customer_audio/ --output-dir sample_outputs/
```

Supported input extensions include WAV, MP3, M4A, FLAC, OGG and WEBM, subject to Gnani SDK limits. Files named like `PC002_turn_01.wav` and `PC002_turn_02.wav` share a conversation session. Each input produces a folder containing `transcript.txt`, `reply.txt`, `result.json` and, when TTS succeeds, `reply.wav`. Root-level `results.csv` and `results.jsonl` preserve the transcripts, answers, evidence and tool events.

## Evaluate

Retrieval-only diagnostic (does not call the LLM):

```bash
python evaluate.py --retrieval-only --top-k 6 --output-dir evaluation_results/
```

Full prompt-only vs. RAG and conversation evaluation (requires an LLM API key; uses API quota):

```bash
python evaluate.py --top-k 6 --output-dir evaluation_results/
```

A smaller smoke test is available:

```bash
python evaluate.py --top-k 6 --limit-questions 5 --limit-conversations 2 --output-dir smoke_eval/
```

The full evaluation runs the 52 practice questions in baseline and RAG modes and the 23 supplied conversations. The phrase-based evaluator is a useful repeatable check, not a substitute for manual review.

Run local tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Deliverables

- `report.pdf` — four-page capstone report.
- `demo.mp4` — screen-recorded demonstration, under two minutes.
- `sample_outputs/` — representative voice outputs and evidence traces.
- `docs/` — system design and validation/retrieval snapshots.

## Limitations and next steps

Voice testing covers three short recordings from one scenario; it does not establish performance across accents, noise conditions or longer calls. Hindi/Hinglish responses need further manual review. The phrase-based evaluator can misclassify paraphrases. The supplied tools are simulated and support order lookup and ticket creation only. Before production use, the system would need broader testing, stronger identity controls, live integrations, monitoring, latency/cost measurement and human-agent workflow validation.

## Acknowledgements

Built for the VoiceOps 2026 capstone by Consulting & Analytics Club, IIT Guwahati in collaboration with Gnani.ai. The project uses the supplied synthetic ZentroMart dataset and mock support tools.
