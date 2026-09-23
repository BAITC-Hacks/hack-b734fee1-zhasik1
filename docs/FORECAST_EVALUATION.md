# Forecast evaluation — local IEK experiment

Command:

```powershell
.\runtime\venv312\Scripts\python.exe scripts\train_forecast.py --iek 'C:\Users\Kuralai\Downloads\IEK.zip' --max-skus 100 --output runtime\forecast_evaluation.json
.\runtime\venv312\Scripts\python.exe scripts\evaluate_forecast.py runtime\forecast_evaluation.json
```

Source SHA-256: `fed312f909943e69b17d2cc5dd577123b5fe0874064558e8f503deaf9fc50054`; unchanged after training. Python 3.12 / scikit-learn 1.9.1. The 100 largest observed SKU histories produced 1,597 causal SKU-origin rows. The last three available monthly origins per supplier/unit/intermittency segment yielded 876 method predictions. Horizon: **21 days = 14 lead + 7 review**. Run time: **44.294 seconds** on this laptop, including cold archive import. September 2026 was excluded as an incomplete target.

| IEK unit / segment | Seasonal WAPE / bias | Mean3 WAPE / bias | HGB WAPE / bias | Selected |
|---|---:|---:|---:|---|
| meters / regular | 44.02% / +0.69% | 53.87% / −27.58% | 50.34% / −6.18% | Seasonal |
| packs / regular | 33.68% / −19.69% | 38.70% / −33.11% | Insufficient fold training | Seasonal |
| pieces / regular | 33.30% / +4.17% | 29.45% / −21.96% | 32.51% / −12.38% | Mean3 |

WAPE is undefined if held-out actual total is zero; such a group would not receive a percentage. The challenger fits only earlier labeled origins within each group, with at least 100 rows and 10 SKUs. Features are lags from completed months, recent levels and slope, observed/zero share, and calendar-month sine/cosine. Causal outlier limits use earlier transactions only. All predictions are floored at zero. The challenger must beat the best baseline WAPE by at least 5% without materially worse signed bias; it did not. No HGB artifact was saved or deployed. The app loads only the source-matched selected **baseline** from the ignored JSON report. A different source fingerprint or lead+review horizon uses a labeled seasonal fallback.

These errors are high, especially for the meter example, and are not a production accuracy claim. The sample favors active SKUs, omits real confirmed stockout intervals and real Systeme Electric data, and treats observed sales as the target. The planner's additional buffer extends its actual demand horizon beyond the evaluated lead+review horizon. No online retraining or LLM quantity prediction occurs.
