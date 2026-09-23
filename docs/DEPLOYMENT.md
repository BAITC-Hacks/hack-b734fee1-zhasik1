# QOR demo deployment

## Streamlit Community Cloud

Create the app at <https://share.streamlit.io/> with these values:

| Setting | Value |
|---|---|
| Repository | **BAITC-Hacks/hack-b734fee1-zhasik1** |
| Branch | **main** |
| Main file path | **frontend/app.py** |
| Python version | **3.12** |

The app needs no secrets. Keep the generated **.streamlit.app** URL as the
stable demo address. New pushes to **main** are picked up by Community Cloud.

The repository belongs to a GitHub organization. The account creating the app
must have admin access to the repository and must authorize Streamlit's GitHub
OAuth application for that organization. If the repository stays private,
configure app viewers in Community Cloud. Make the app public there when a
public demo is required.

## Runtime behavior

- The landing page and the built-in synthetic walkthrough work without uploads.
- Real supplier source archives are private and are not committed.
- Uploaded source data and the SQLite workflow database live on the app
  container filesystem. Community Cloud may restart or redeploy the container,
  so this demo does not provide durable approval history.
- The application sends no purchase order to a supplier.
- The app uses the dependency pins in **pyproject.toml** through
  **requirements.txt**.

## Verification

After the deployment reports success:

1. Open the generated **.streamlit.app** URL in a signed-out browser window.
2. Confirm the Russian product overview loads.
3. Open **/workspace** using the overview button.
4. Load the synthetic walkthrough and calculate a draft order.
5. Confirm that the app can move a draft to review and approval.
6. Confirm the approved CSV/XLSX export downloads.

For the full guided path, use [DEMO_SCRIPT.md](DEMO_SCRIPT.md).

## Release automation

**.github/workflows/ci.yml** tests Python 3.12 on every push and pull request.
**.github/workflows/release.yml** publishes a GitHub Release when a **v*** tag
is pushed. The demo tag is **v0.1.0-demo**. The GitHub organization must allow
GitHub-hosted Actions runners; otherwise jobs stop before any workflow step.
