# Tested local stack

`pyproject.toml` is the authoritative manifest. `requirements.txt` delegates to `-e .[test]`; it contains no second dependency list.

| Component | Tested version on Python 3.12 |
|---|---:|
| Python | 3.12 |
| Streamlit | 1.64.0 |
| pandas | 2.3.3 |
| NumPy | 2.5.3 |
| openpyxl | 3.1.5 |
| Plotly | 7.1.0 |
| Pydantic | 2.13.5 |
| scikit-learn | 1.9.1 |
| pytest | 9.1.1 |

The clean environment lives under ignored `runtime/venv312/`; the prior `.venv` Python 3.14 installation was left intact. The app runs in one Streamlit process with SQLite, typed Python calculations and local CPU forecasting. No React, FastAPI, server database, LLM SDK or GPU runtime was added.

```powershell
py -3.12 -m venv runtime\venv312
.\runtime\venv312\Scripts\python.exe -m pip install -e '.[test]'
.\runtime\venv312\Scripts\python.exe -m pytest -q
.\runtime\venv312\Scripts\python.exe -m streamlit run frontend\app.py --server.address 127.0.0.1 --server.port 8511
```

The active Streamlit CLI supports `skills --yes`; it reported both project skill symlinks up to date. The Vercel design skill was present in `.agents/skills/web-design-guidelines/SKILL.md` and its current upstream rules were fetched for review. This is verification of an existing installation, not a claimed fresh CLI install.
