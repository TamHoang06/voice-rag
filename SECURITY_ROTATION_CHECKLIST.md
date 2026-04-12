# Security Rotation Checklist

Use this checklist immediately after removing hard-coded secrets from the repo.

## Immediate actions

1. Rotate the exposed `OPENAI_API_KEY`.
2. Rotate the exposed `AZURE_API_KEY`.
3. Rotate the exposed `GEMINI_API_KEY`.
4. Verify old keys are revoked, not just regenerated.

## Repo cleanup

1. Remove secrets from every tracked file.
2. Rewrite Git history if the repo was pushed anywhere public or shared.
3. Invalidate any cached CI/CD variables or local copied `.env` files.
4. Check logs, screenshots, docs, and sample data for leaked credentials.

## Safe storage going forward

1. Keep runtime secrets only in `src/.env` or a deployment secret manager.
2. Keep only placeholder values in examples and docs.
3. Never commit keys into `data/`, markdown files, tests, or notebooks.
4. Restrict key scopes and quotas to the minimum needed for each provider.

## Verification

1. Confirm the app boots with new keys from `src/.env`.
2. Confirm `/health`, `/debug/tts`, upload, RAG Q&A, STT, and TTS still work.
3. Confirm `git grep -n \"API_KEY\\|sk-\\|AIza\\|AQ\\.\"` returns no real secrets.
