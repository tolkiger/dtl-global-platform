# DTL-Global HubSpot app (developer platform 2025.2)

This folder is a **HubSpot developer project** using **static authentication** and **private** distribution — the [current recommended path](https://developers.hubspot.com/docs/api/developer-tools-overview) for a single-account integration (same Bearer token model as legacy private apps, managed as a project).

## Prerequisites

- [HubSpot CLI](https://developers.hubspot.com/developer-tooling/local-development/hubspot-cli/install-the-cli) v7.6.0+ (`npm install -g @hubspot/cli@latest`)
- HubSpot account with permission to create projects and install apps

## One-time setup

1. **Authenticate the CLI** (Personal Access Key from Development → Keys → Personal Access Key):

   ```bash
   hs account auth
   ```

2. From **this directory** (`hubspot/dtl-global-platform-app/`):

   ```bash
   hs project upload
   ```

3. **Install the app** on the HubSpot account that should receive CRM automation:
   - Development → **Projects** → project `dtl-global-platform-app` → open the **app** component → **Distribution** → **Install now** (standard account) or add a **test install** (developer test account).
   - Approve the requested scopes.

4. **Copy the static access token**:
   - Same app component page → **Auth** tab → copy the **access token** (Bearer) into your repo `.env` as `HUBSPOT_ACCESS_TOKEN`.

5. Run Phase 0 scripts from the repo root:

   ```bash
   python scripts/phase0_hubspot_setup.py && python scripts/phase0_hubspot_verify.py
   ```

## Changing scopes

Edit `src/app/app-hsmeta.json` → `requiredScopes`, then run `hs project upload` again and re-install / approve the new permissions if HubSpot prompts you.

## Official references

- [Create a new app using the CLI](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/create-an-app)
- [Authentication overview (static vs OAuth)](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview)
- [App configuration (`app-hsmeta.json`)](https://developers.hubspot.com/docs/apps/developer-platform/build-apps/app-configuration)
