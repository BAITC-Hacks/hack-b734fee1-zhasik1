"""Russian product overview. All displayed quantities are illustrative."""

import streamlit as st


st.html("""
<style>
.qor-eyebrow {color:#93c5fd;font-size:.78rem;font-weight:750;letter-spacing:.17em;text-transform:uppercase;margin:0 0 1rem}
.qor-preview {background:linear-gradient(145deg,#152b4b,#0b1930 65%);border:1px solid #335882;border-radius:20px;padding:22px;box-shadow:0 24px 60px #0208177a;color:#eaf3ff}
.qor-preview * {box-sizing:border-box}
.qor-preview-head {display:flex;justify-content:space-between;gap:10px;align-items:center;border-bottom:1px solid #294562;padding-bottom:14px}
.qor-brand {font-size:1.35rem;font-weight:850;letter-spacing:.08em}
.qor-chip {border:1px solid #356697;border-radius:999px;padding:5px 10px;color:#b5d6ff;font-size:.72rem;white-space:nowrap}
.qor-preview-title {font-size:1.1rem;font-weight:700;margin:18px 0 4px}
.qor-preview-note {font-size:.78rem;color:#bdcee2;margin:0 0 16px}
.qor-preview-metrics {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.qor-preview-metric {background:#172e4d;border:1px solid #29496d;border-radius:12px;padding:11px;min-width:0}
.qor-preview-metric span {display:block;color:#b9cee6;font-size:.68rem}
.qor-preview-metric strong {display:block;font-size:1.15rem;margin-top:3px}
.qor-preview-row {display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;border-bottom:1px solid #294562;padding:12px 2px;font-size:.79rem}
.qor-preview-row:last-child {border-bottom:0}
.qor-preview-row b {color:#93c5fd;white-space:nowrap}
.qor-preview-footer {margin-top:14px;color:#a8c4df;font-size:.72rem}
@media (max-width:560px) {.qor-preview {padding:15px;border-radius:14px}.qor-preview-metrics {grid-template-columns:1fr 1fr}.qor-preview-metric:last-child {grid-column:1 / -1}}
</style>
""")

hero, preview = st.columns([1.08, 1], gap="large", vertical_alignment="center")
with hero:
    st.html('<p class="qor-eyebrow">QOR / Управление закупками</p>')
    st.title("Закупки без догадок")
    st.markdown(
        "Соберите продажи, остатки и поставки в одном расчёте. "
        "QOR покажет, **сколько заказать у каждого поставщика, когда возникнет дефицит "
        "и откуда взялась каждая цифра**."
    )
    st.page_link("app_pages/workspace.py", label="Открыть приложение",
                 icon=":material/arrow_forward:", width="stretch")
    st.caption("Локальная версия · решение подтверждает менеджер · поставщикам ничего не отправляется автоматически")

with preview:
    st.html("""
    <section class="qor-preview" aria-label="Демонстрационный вид панели QOR">
      <div class="qor-preview-head"><span class="qor-brand">QOR<span style="color:#60a5fa">.</span></span>
      <span class="qor-chip">ДЕМО · НЕ РЕАЛЬНЫЙ ЗАКАЗ</span></div>
      <div class="qor-preview-title">Черновик для проверки</div>
      <p class="qor-preview-note">Иллюстрация интерфейса · данные синтетические</p>
      <div class="qor-preview-metrics">
        <div class="qor-preview-metric"><span>Прогноз спроса</span><strong>188 шт.</strong></div>
        <div class="qor-preview-metric"><span>Доступно</span><strong>28 шт.</strong></div>
        <div class="qor-preview-metric"><span>Ожидается</span><strong>40 шт.</strong></div>
      </div>
      <div class="qor-preview-row"><span>Поставщик · демо</span><b>На проверке</b></div>
      <div class="qor-preview-row"><span>Расчётная потребность</span><b>120 шт.</b></div>
      <div class="qor-preview-row"><span>Кратность упаковки</span><b>20 шт.</b></div>
      <div class="qor-preview-footer">Дата прихода, резервы и сроки в настоящем расчёте могут изменить результат.</div>
    </section>
    """)

st.header("От файла до согласованного заказа")
steps = [
    ("01 · Загрузите", "Добавьте Excel или ZIP поставщика. Источники и предупреждения остаются видимыми.", ":material/upload_file:"),
    ("02 · Проверьте", "Посмотрите спрос, расхождения источников и необычные продажи. Исключения требуют решения менеджера.", ":material/fact_check:"),
    ("03 · Рассчитайте", "Сравните прогноз с доступным остатком, поставками по датам и правилами заказа.", ":material/query_stats:"),
    ("04 · Согласуйте", "Отредактируйте черновик с причиной, подтвердите и выгрузите CSV или XLSX.", ":material/approval:"),
]
for start in (0, 2):
    columns = st.columns(2, gap="medium")
    for column, (title, body, icon) in zip(columns, steps[start:start + 2]):
        with column, st.container(border=True):
            st.subheader(title, icon=icon)
            st.write(body)

st.header("Каждая цифра проверяема")
capabilities = [
    ("Спрос и сезонность", "Текущие продажи сравниваются с завершёнными месяцами. Крупная разовая сделка помечается для проверки; устойчивый рост сохраняется."),
    ("Поставки по датам", "Товар учитывается только после ожидаемой даты поступления. Ранний дефицит показан отдельно от заказа, который придёт позже."),
    ("Правила поставщика", "Минимальный заказ и кратность упаковки применяются отдельно, с проверкой единиц измерения и исходных строк."),
    ("Контроль менеджера", "Черновик, причины изменений и согласование сохраняются по версиям. Выгрузка доступна после утверждения."),
]
for start in (0, 2):
    columns = st.columns(2, gap="medium")
    for column, (title, body) in zip(columns, capabilities[start:start + 2]):
        with column, st.container(border=True):
            st.subheader(title)
            st.write(body)

st.header("Пример расчёта")
with st.container(border=True):
    st.caption("СИНТЕТИЧЕСКИЙ ПРИМЕР · для объяснения принципа, не результат рабочего планировщика")
    st.metric("Иллюстративный заказ", "120 шт.", border=True)
    st.markdown("**188 шт. прогнозного спроса − (28 шт. текущего остатка + 40 шт. ожидаемой поставки) = 120 шт.**")
    st.caption("Кратность упаковки 20 шт. оставляет 120 шт. В рабочем расчёте дата поставки, резервы, сроки и буфер могут изменить потребность.")

st.header("Что уже работает")
st.write(
    "Импорт и сверка IEK проверены на найденном реальном архиве. Для IEK нет "
    "подтверждённого текущего остатка, поэтому окончательный заказ блокируется до ввода "
    "остатка с датой. Файлы Systeme Electric в доступных материалах не найдены; "
    "встроенный пример помечен как синтетический. Доступ к модели организатора пока не подтверждён."
)
st.page_link("app_pages/workspace.py", label="Открыть приложение",
             icon=":material/arrow_forward:")
st.caption("QOR · HackAlem AI · Объяснимые черновики заказов для менеджера по закупкам")
