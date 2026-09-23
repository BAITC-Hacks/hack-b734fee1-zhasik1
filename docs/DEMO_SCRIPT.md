# QOR: 4–5 minute honest demo

Run `python -m streamlit run frontend/app.py --server.address 127.0.0.1`.
The default 22 September 2026 snapshot is historical. Keep private supplier
rows out of any public recording.

1. **Landing, 35 s.** Show “Закупки без догадок,” the two working CTAs and the
   synthetic illustration: 188 − (28 + 40) = 120 units, pack multiple 20.
   Explain that real ETA, reserves and lead time can change a real result.
2. **Synthetic manager flow, 90 s.** Open Закупки → Источники → “Открыть
   синтетический пример.” State that its Systeme Electric rows and anonymized
   client IDs are generated. In Спрос, show original, reviewed and capped
   forecast-input series; inspect a large-sale candidate. In Заказы, calculate
   a draft, inspect the row explanation and dated timeline, save an edited
   quantity with a reason, move to review and approval, then generate/reopen
   and download an XLSX. Nothing is sent to a supplier.
3. **Scenarios, 45 s.** Show 7/14/30-day lead comparisons and shift an inbound
   ETA. Point out a shortage that happens before a new purchase could arrive.
4. **Real IEK boundary, 70 s.** Load the located `Downloads/IEK.zip` if
   authorized locally. Choose textual SKU `200400085_`, unit meters. Show
   monthly/transaction reconciliation and source references. Calculate its
   draft: `needs_stock_input` appears because no current dated available
   stock exists. Do not present a hypothetical zero-stock calculation as a
   real purchase order.
5. **Forecast and model status, 40 s.** Show the 21-day held-out table in
   [FORECAST_EVALUATION.md](FORECAST_EVALUATION.md): the HGB challenger lost;
   seasonal won for sampled meters/packs and mean3 for pieces. These are
   high-error, sampled results. The organizer model probe stops before a live
   call because endpoint, model ID and credential are missing.

If the IEK archive is unavailable on the demo machine, skip step 4 or ask the
owner to provide it through the local upload interface. Real Systeme Electric
files and the original criteria file were not accessible during this audit.
