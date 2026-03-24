---
name: dtl-cdk-local-workflow
description: Local CDK and Lambda layer setup for DTL-Global — pip install before synth/deploy, and why engine/ must stay in the repo. Use when deploying CDK, debugging layer errors, or cleaning the repository.
---

# DTL-Global CDK + Lambda local workflow

## Before `cdk synth` or `cdk deploy`

Run (same as CI `buildspec.yml`):

```bash
python3 -m pip install --no-cache-dir -r cdk/lambda_layer/requirements.txt -t cdk/lambda_layer/python
```

Then from `cdk/`: `cdk deploy` or `cdk synth DtlApi`.

`cdk/lambda_layer/python/` is **gitignored**; do not commit it.

## Do not remove `engine/`

- **`engine/`** = your **application** code (handlers, shared, templates). **Keep it in git.**
- **Layer** = **dependencies** only (`hubspot`, `stripe`, etc.) under `cdk/lambda_layer/python/`.

Deleting `engine/` would remove all Lambda handlers.

## Full rule

See **`.cursor/rules/dtl-cdk-lambda-local-workflow.mdc`** (always applied in this project).
