# 🏗️ Google - Agent Harness on Physical-Engineering's Last Exam (PLE)

**GitHub Repository**: [rishabhjain001/google-ple-exam](https://github.com/rishabhjain001/google-ple-exam)  
**Competition**: [Google - Agent Harness on Physical-Engineering's Last Exam (Kaggle)](https://www.kaggle.com/competitions/physical-engineerings-last-exam)  
**Prize Pool**: **$400,000 USD** (1st: $250,000 | 2nd: $100,000 | 3rd: $50,000)  
**Submission Deadline**: **January 5 / 6, 2027**  
**License**: Apache-2.0  

---

## 📌 Repository Overview

This repository is an autonomous engineering agent harness engineered to solve the 85 multi-hour engineering tasks in the **Physical-Engineering's Last Exam (PLE)** benchmark.

```
ple-agent-harness/
├── submission.yaml       # Harness entry configuration (model, install, serve commands)
├── serve.py              # WebSocket server entrypoint launched by the evaluator container
├── taskbridge.py         # Version 1 WebSocket protocol implementation
├── harness.py            # Multi-turn autonomous agent loop with tool-calling
├── prompts/
│   └── system.md         # Professional Engineer (PE) domain system prompt
├── tools/
│   ├── cad_tools.py      # CAD (.dxf) and 2D/3D geometry parsers
│   └── calc_tools.py     # Structural, Civil, Electrical, and Mechanical formulas
├── requirements.txt      # Python dependencies
├── LICENSE               # Apache-2.0
└── README.md
```

---

## 🚀 Quickstart & Testing Locally

### 1. Clone the Official PLE Benchmark Kit

```bash
git clone https://github.com/google-research/ple.git
cd ple
```

### 2. Check Your Harness Sanity

Verify your harness conforms to the evaluator specifications:

```bash
uv run python -m kit check /path/to/ple-agent-harness
```

### 3. Run on the Public Dev Tasks (29 Tasks)

To test your agent locally and generate your required evaluation artifacts:

```bash
uv run python eval/run.py /path/to/ple-agent-harness
```

### 4. Verify & Pack Artifacts

Confirm all deliverables and logs are generated:

```bash
uv run python -m kit artifacts
```

---

## 🧠 Supported Google-Sponsored Models

In `submission.yaml`, `model_api` can be set to any official Google-sponsored model:

* `google-cloud/claude-opus-5-5` *(Default — Recommended for complex multi-page calculations)*
* `google-cloud/gemini-4-argon`
* `google-cloud/gemini-3.8-flash`
* `google-cloud/gemini-3.1-pro-preview`
* `google-cloud/qwen3-coder-480b`

> **Note**: During evaluation in Stage 2, Google supplies all model inference compute for free. No personal Google Cloud billing account or API keys are required for official testing.

---

## 📤 How to Submit to Kaggle

1. Push this repository to GitHub (public or private with the competition GitHub App enabled):
   ```bash
   git init
   git add .
   git commit -m "Initial commit of PLE autonomous engineer harness"
   git remote add origin https://github.com/<your-username>/ple-agent-harness.git
   git push -u origin main
   ```
2. Get your exact 40-character commit SHA:
   ```bash
   git rev-parse HEAD
   ```
3. Go to the Kaggle competition submission page:
   - Provide your **GitHub Repository URL**
   - Provide your **Commit SHA**
   - Attach your Stage 1 writeup / artifacts summary
