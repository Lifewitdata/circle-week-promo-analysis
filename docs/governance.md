# Data governance and responsible AI

This independent portfolio is not affiliated with Target. All source observations
are synthetic. Brand references provide a scenario only. Costs, margin and rollout
store count are labelled assumptions. Do not describe simulated revenue as money
earned for an employer or claim original store randomization was verified.

Input SHA-256 hashes in summary.json establish which source bytes produced the
results. The input contract runs before SQL and inference. Primary SQL and Python
effects must reconcile before publishing. Outputs include definitions and source
logic. A failed CLI run marks reports/run_status.json as failed; previous outputs
must be considered stale. CI checks data and calculations on pull requests.

AI uses an allow-listed document corpus, TF-IDF passage retrieval and an optional
Groq model to select approved metric IDs, action IDs and retrieved citations.
Generated selections must pass a strict schema and membership check. Numeric
sentences are rendered from computed metrics rather than unverified LLM prose.
No model-generated SQL executes, no files or URLs from prompts are read, and no
arbitrary tools are exposed. Retrieved passages/user questions are untrusted data.
This is bounded retrieval-augmented generation, not unrestricted business advice.

Offline extractive summaries do not call a model and are labelled accordingly.
Live mode needs GROQ_API_KEY and GROQ_MODEL in the environment. Only approved
aggregate facts and documents leave the machine. Never send customer data or
keys in prompts. Do not commit .env, ADC credentials, tokens or private prompts.
Model selection and access are user-controlled; calls are not claimed tested
without successful recorded evidence. Citations establish provenance, not factual
truth of arbitrary prose (arbitrary prose is rejected here).

Human review remains required for a commercial recommendation. Margin/cost
assumptions, representativeness, privacy obligations and corporate approval rules
must be reviewed in the target organization. No HIPAA/GDPR compliance certification,
Target corporate policy compliance or production readiness is asserted.
