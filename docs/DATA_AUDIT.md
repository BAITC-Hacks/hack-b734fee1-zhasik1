# Supplier data audit

The original `Downloads/IEK.zip` was read in memory and left unchanged. The earlier full import audit counted 171,603 transaction rows, 81,279 monthly-sale cells, 306 inbound lines, 1,937 purchase-rule rows and no current available-stock rows. September 2026 is incomplete at the historical 22 September snapshot. Transaction and monthly totals are reconciled, never summed together. Source file/sheet/row references, textual SKU and physical unit remain in normalized records.

SKU `200400085_` (meters) is traceable in the existing private verification output. Its monthly and transaction totals disagree in several months; the disagreement is visible rather than silently resolved. Its draft remains `needs_stock_input` without an evidenced dated available stock. A prior zero-stock scenario was labeled hypothetical and is not a real IEK order.

No actual Systeme Electric workbook/archive was found in the accessible workspace, attachments or searched Downloads/Desktop/Documents paths. The import path is exercised with synthetic canonical files, but supplier-specific real header and stock semantics remain unverified. No real anonymized customer IDs or confirmed stockout intervals were supplied.
