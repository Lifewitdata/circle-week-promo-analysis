# Retrieval and AI-assisted reporting

```bash
python -m src.pipeline
python -m src.ai_summary
```

Default mode builds a local TF-IDF index of metric definitions, methodology,
governance and the generated decision brief; retrieves up to three passages;
and renders approved facts. It is an offline extractive smoke test, not an LLM call.
Evidence contains source IDs and retrieval scores under reports/ai_offline/.

Optional live mode:
```bash
pip install -r requirements-cloud.txt
# Set GROQ_API_KEY and a currently available GROQ_MODEL in your shell.
python -m src.ai_summary --live --question "What revenue evidence supports a limited pilot?"
```

The LLM returns a constrained JSON selection of approved metrics/actions and
retrieved citations. The validator rejects unknown fields, IDs, citations,
duplicates and free-text numeric claims. Selected metric sentences are rendered
from summary.json. Evidence is saved only after validation succeeds. The workflow
does not answer arbitrary questions: a profit question still receives explicit
limits and cost-verification guidance, not invented profit. It never runs SQL.

Evaluation: tests check relevant retrieval, empty/no-context queries, schema
validation, invented facts/citations, duplicate citations, prompt-injection-shaped
responses and mocked live success/failure. A mocked transport tests code paths,
not model quality. Actual model evaluations require the optional live command;
no live model score is claimed. Citations are provenance to retrieved context,
not a claim that all selected metrics were extracted from a cited paragraph.
