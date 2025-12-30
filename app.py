import os
import re
from io import BytesIO
from datetime import datetime

import pandas as pd
import streamlit as st

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# =========================
# Streamlit config
# =========================
st.set_page_config(page_title="Owner Report", layout="wide")


# =========================
# THEME (sellable UI)
# =========================
def apply_app_theme():
    st.markdown("""
    <style>
      :root{
        --bg: #0b1020;
        --panel: rgba(255,255,255,0.06);
        --panel2: rgba(255,255,255,0.08);
        --border: rgba(255,255,255,0.10);
        --text: rgba(255,255,255,0.92);
        --muted: rgba(255,255,255,0.68);

        --good: #22c55e;
        --warn: #f59e0b;
        --bad:  #ef4444;

        --accent: #7c3aed;
        --accent2:#06b6d4;
      }

      .stApp {
        background: radial-gradient(1200px 700px at 20% 0%, rgba(124,58,237,0.25), transparent 60%),
                    radial-gradient(900px 600px at 90% 20%, rgba(6,182,212,0.18), transparent 55%),
                    linear-gradient(180deg, #070a14 0%, #0b1020 100%);
        color: var(--text);
      }

      .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1180px; }

      section[data-testid="stSidebar"]{
        background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border-right: 1px solid var(--border);
      }

      h1,h2,h3 { letter-spacing: -0.02em; }
      p, li, div, label { color: var(--text); }

      .card{
        background: linear-gradient(180deg, var(--panel) 0%, rgba(255,255,255,0.04) 100%);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 16px 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      }
      .card-tight{ padding: 12px 12px; border-radius: 16px; }

      .title-xl{
        font-size: 34px; font-weight: 780; line-height: 1.08;
        margin: 0 0 8px 0;
      }
      .subtitle{ color: var(--muted); font-size: 14px; margin: 0; }

      .badge{
        display:inline-flex; align-items:center; gap:8px;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.06);
        color: var(--text);
        font-size: 12px;
      }
      .dot{ width:10px; height:10px; border-radius:999px; display:inline-block; }

      .kpi{
        font-size: 22px; font-weight: 780; letter-spacing:-0.01em;
        margin-top: 4px;
      }
      .kpi-label{ color: var(--muted); font-size: 12px; }

      .stButton button, .stDownloadButton button{
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        padding: 10px 14px !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, rgba(124,58,237,0.95), rgba(6,182,212,0.85)) !important;
        color: white !important;
      }
      .stButton button:hover, .stDownloadButton button:hover{
        filter: brightness(1.05);
        transform: translateY(-1px);
      }

      div[data-testid="stDataFrame"]{
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        border: 1px solid var(--border);
        overflow: hidden;
      }

      /* ===== SELECTBOX CLOSED STATE ===== */
      div[data-baseweb="select"] > div{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.16) !important;
        border-radius: 14px !important;
      }
      div[data-baseweb="select"] span,
      div[data-baseweb="select"] div{
        color: rgba(255,255,255,0.92) !important;
      }
      div[data-baseweb="select"] input{
        color: rgba(255,255,255,0.92) !important;
        -webkit-text-fill-color: rgba(255,255,255,0.92) !important;
      }
      div[data-baseweb="select"] svg{ fill: rgba(255,255,255,0.85) !important; }

      /* ===== STRONG DROPDOWN FIX ===== */
      div[data-baseweb="popover"] > div,
      div[data-baseweb="menu"],
      div[role="listbox"]{
        background: rgba(12,14,28,0.98) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 14px !important;
        box-shadow: 0 18px 60px rgba(0,0,0,0.55) !important;
      }
      div[role="option"]{
        color: rgba(255,255,255,0.92) !important;
        background: transparent !important;
      }
      div[role="option"][aria-selected="true"]{
        background: rgba(124,58,237,0.22) !important;
      }
      div[role="option"]:hover{
        background: rgba(255,255,255,0.08) !important;
      }
      div[role="option"][aria-disabled="true"],
      div[role="option"][aria-disabled="true"] *{
        color: rgba(255,255,255,0.55) !important;
      }

      /* ===== FILE UPLOADER ===== */
      section[data-testid="stSidebar"] div[data-testid="stFileUploader"]{
        background: rgba(255,255,255,0.06) !important;
        border: 1px dashed rgba(255,255,255,0.18) !important;
        border-radius: 16px !important;
        padding: 12px !important;
      }
      section[data-testid="stSidebar"] div[data-testid="stFileUploader"] small{
        color: rgba(255,255,255,0.70) !important;
      }
      section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button{
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        padding: 10px 14px !important;
        font-weight: 750 !important;
        background: linear-gradient(90deg, rgba(124,58,237,0.92), rgba(6,182,212,0.80)) !important;
        color: white !important;
      }

      hr { border-color: rgba(255,255,255,0.08) !important; }
      header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


apply_app_theme()


# =========================
# UI helpers
# =========================
def ui_badge(status: str) -> str:
    if status == "CRITICAL":
        color = "var(--bad)"; text = "CRITICAL"
    elif status == "WARNING":
        color = "var(--warn)"; text = "WARNING"
    elif status == "OK":
        color = "var(--good)"; text = "OK"
    else:
        color = "rgba(255,255,255,0.45)"; text = "N/A"
    return f"""
    <span class="badge">
      <span class="dot" style="background:{color}"></span>
      <b>{text}</b>
    </span>
    """

def ui_kpi_card(label: str, value: str, hint: str = "") -> str:
    hint_html = f'<div class="subtitle" style="margin-top:6px">{hint}</div>' if hint else ""
    return f"""
    <div class="card card-tight">
      <div class="kpi-label">{label}</div>
      <div class="kpi">{value}</div>
      {hint_html}
    </div>
    """

def ui_section(title: str, subtitle: str = "") -> str:
    sub = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="margin: 2px 0 12px 0;">
      <div>
        <div style="font-size:18px; font-weight:780;">{title}</div>
        {sub}
      </div>
    </div>
    """


# =========================
# Basic helpers
# =========================
def fmt_money(x: float, currency: str) -> str:
    try:
        return f"{float(x):,.0f} {currency}"
    except Exception:
        return f"{x} {currency}"

def safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

def norm(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


# =========================
# File load + column guessing
# =========================
def read_file(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    if name.endswith(".xlsx"):
        return pd.read_excel(BytesIO(file.getvalue()), engine="openpyxl")
    raise ValueError("Неподдерживаемый формат")

def guess_columns(cols):
    ncols = [norm(c) for c in cols]
    mapping = {"date": None, "amount": None, "type": None, "category": None, "project": None}

    def find_any(patterns):
        for i, c in enumerate(ncols):
            for p in patterns:
                if re.search(p, c):
                    return cols[i]
        return None

    mapping["date"] = find_any([r"\bdate\b", r"\bдата\b", r"операц"])
    mapping["amount"] = find_any([r"\bamount\b", r"\bсумма\b", r"\bитог\b", r"\btotal\b"])
    mapping["type"] = find_any([r"\btype\b", r"\bтип\b", r"\bдоход\b", r"\bрасход\b", r"\bincome\b", r"\bexpense\b"])
    mapping["category"] = find_any([r"\bcategory\b", r"категор", r"статья", r"назначение"])
    mapping["project"] = find_any([r"\bproject\b", r"проект", r"филиал", r"магазин", r"branch", r"точка"])
    return mapping

def try_parse_date(series: pd.Series) -> float:
    try:
        return pd.to_datetime(series, errors="coerce").notna().mean()
    except Exception:
        return 0.0

def try_parse_amount(series: pd.Series) -> float:
    try:
        return pd.to_numeric(series, errors="coerce").notna().mean()
    except Exception:
        return 0.0

def guess_by_content(df: pd.DataFrame, mapping: dict) -> dict:
    if mapping["date"] is None:
        scores = {c: try_parse_date(df[c]) for c in df.columns}
        best = max(scores, key=scores.get)
        if scores[best] >= 0.7:
            mapping["date"] = best

    if mapping["amount"] is None:
        scores = {c: try_parse_amount(df[c]) for c in df.columns}
        best = max(scores, key=scores.get)
        if scores[best] >= 0.7:
            mapping["amount"] = best

    return mapping


# =========================
# Metrics / risks / insights
# =========================
def compute_metrics(flt: pd.DataFrame) -> pd.DataFrame:
    flt = flt.copy()
    flt["month"] = flt["date"].dt.to_period("M").dt.to_timestamp()

    income = flt[flt["amount"] > 0].groupby("month")["amount"].sum()
    expense = -flt[flt["amount"] < 0].groupby("month")["amount"].sum()

    m = pd.DataFrame({"Выручка": income, "Расходы": expense}).fillna(0)
    m["Прибыль"] = m["Выручка"] - m["Расходы"]
    m["Маржа"] = (m["Прибыль"] / m["Выручка"]).replace([float("inf"), -float("inf")], 0)
    return m.sort_index()

def compare_periods(m: pd.DataFrame):
    if m is None or m.empty or len(m) < 2:
        return None
    last, prev = m.index[-1], m.index[-2]
    prev_rev = safe_float(m.loc[prev, "Выручка"])
    prev_exp = safe_float(m.loc[prev, "Расходы"])
    last_rev = safe_float(m.loc[last, "Выручка"])
    last_exp = safe_float(m.loc[last, "Расходы"])
    revenue_change = (last_rev / prev_rev - 1.0) if prev_rev else 0.0
    expense_change = (last_exp / prev_exp - 1.0) if prev_exp else 0.0
    margin_pp = (safe_float(m.loc[last, "Маржа"]) - safe_float(m.loc[prev, "Маржа"])) * 100.0
    return {
        "last_month": last,
        "prev_month": prev,
        "revenue_change": revenue_change,
        "expense_change": expense_change,
        "margin_pp": margin_pp,
    }

def calc_risks(flt: pd.DataFrame, m: pd.DataFrame, target_margin: float):
    risks = []
    if m.empty:
        return risks, "N/A"

    last = m.index.max()
    prev = m.index[-2] if len(m) >= 2 else None

    # 1) Loss
    last_profit = safe_float(m.loc[last, "Прибыль"])
    if last_profit < 0:
        risks.append({"level": "CRIT", "title": "Убыток в последнем месяце", "details": f"Прибыль: {last_profit:,.0f}."})

    # 2) Margin drop
    if prev is not None:
        last_margin = safe_float(m.loc[last, "Маржа"])
        prev_margin = safe_float(m.loc[prev, "Маржа"])
        drop_pp = (prev_margin - last_margin) * 100.0
        lvl = "CRIT" if drop_pp > 10 else "WARN" if drop_pp > 5 else None
        if lvl:
            risks.append({"level": lvl, "title": "Падение маржи", "details": f"Маржа упала на {drop_pp:.1f} п.п. ({prev_margin:.1%} → {last_margin:.1%})."})

    # 3) Expense concentration (raw category)
    exp = flt[flt["amount"] < 0].copy()
    if not exp.empty:
        exp["expense_abs"] = -exp["amount"]
        by_cat = exp.groupby("category")["expense_abs"].sum().sort_values(ascending=False)
        total = safe_float(by_cat.sum(), 0.0)
        if total > 0 and len(by_cat):
            top_cat = str(by_cat.index[0])
            share = safe_float(by_cat.iloc[0] / total, 0.0)
            lvl = "CRIT" if share > 0.50 else "WARN" if share > 0.35 else None
            if lvl:
                risks.append({"level": lvl, "title": "Концентрация расходов", "details": f"Категория «{top_cat}» = {share:.1%} всех расходов."})

    # 4) Expense spike MoM
    if prev is not None:
        last_exp = safe_float(m.loc[last, "Расходы"])
        prev_exp = safe_float(m.loc[prev, "Расходы"])
        if prev_exp > 0:
            spike = (last_exp / prev_exp) - 1.0
            lvl = "CRIT" if spike > 0.50 else "WARN" if spike > 0.30 else None
            if lvl:
                risks.append({"level": lvl, "title": "Резкий рост расходов месяц-к-месяцу", "details": f"Расходы выросли на {spike:.1%} ({prev_exp:,.0f} → {last_exp:,.0f})."})

    # 5) Below target margin
    if target_margin and target_margin > 0:
        last_margin = safe_float(m.loc[last, "Маржа"])
        gap_pp = (target_margin / 100.0 - last_margin) * 100.0
        lvl = "CRIT" if gap_pp > 10 else "WARN" if gap_pp > 5 else None
        if lvl:
            risks.append({"level": lvl, "title": "Маржа ниже целевой", "details": f"Цель: {target_margin:.0f}% · Факт: {last_margin:.1%} · Отклонение: {gap_pp:.1f} п.п."})

    status = "CRITICAL" if any(r["level"] == "CRIT" for r in risks) else "WARNING" if any(r["level"] == "WARN" for r in risks) else "OK"
    return risks, status

def generate_insights(risks, m: pd.DataFrame, cmp, business_type: str, target_margin: float):
    insights, actions = [], []

    if not m.empty:
        last = m.index.max()
        rev = safe_float(m.loc[last, "Выручка"])
        exp = safe_float(m.loc[last, "Расходы"])
        prof = safe_float(m.loc[last, "Прибыль"])
        mar = safe_float(m.loc[last, "Маржа"])
        insights.append(f"Последний месяц: выручка {rev:,.0f}, расходы {exp:,.0f}, прибыль {prof:,.0f}, маржа {mar:.1%}.")
        insights.append(f"Тип бизнеса: {business_type}. Целевая маржа: {target_margin:.0f}%.")

    if cmp:
        insights.append(f"MoM: выручка {cmp['revenue_change']:+.1%}, расходы {cmp['expense_change']:+.1%}, маржа {cmp['margin_pp']:+.1f} п.п.")

    for r in risks:
        t = (r.get("title") or "").lower()
        if "концентрация" in t:
            actions += [
                "Проверить 5 самых крупных списаний в этой категории.",
                "Согласовать лимит по категории на следующий месяц.",
                "Проверить договоры/подписки и убрать лишнее."
            ]
        if "маржа" in t:
            actions += [
                "Проверить рост постоянных расходов и разовые платежи.",
                "Проанализировать цены/скидки и маржинальность по продуктам/услугам.",
                "Сравнить маржу по проектам/филиалам."
            ]
        if "убыток" in t:
            actions += [
                "Сократить необязательные расходы в ближайшие 2–4 недели.",
                "Пересмотреть лимиты по категориям.",
                "Сделать план роста выручки на 30 дней (3 гипотезы)."
            ]
        if "рост расходов" in t:
            actions += [
                "Найти разовые платежи в последнем месяце и подтвердить их необходимость.",
                "Разделить расходы на постоянные и переменные.",
                "Ввести простой контроль: недельный лимит."
            ]

    if business_type == "Торговля":
        actions += ["Проверить валовую маржу по ключевым товарным группам и скидочную политику."]
    elif business_type == "Услуги":
        actions += ["Проверить загрузку команды и долю непроизводительных часов."]
    elif business_type == "IT / Digital":
        actions += ["Проверить долю ФОТ и окупаемость проектов по контрактам."]
    elif business_type == "Производство":
        actions += ["Разложить себестоимость на сырьё/энергию/персонал и найти драйвер роста затрат."]

    actions = list(dict.fromkeys(actions))[:7]
    if not actions:
        actions = ["Провести контрольную проверку данных и уточнить структуру категорий расходов."]

    return insights[:7], actions[:7]


# =========================
# Explainability
# =========================
def explain_risk(risk: dict, m: pd.DataFrame, target_margin: float, currency: str):
    if not risk or m is None or m.empty:
        return []

    title = (risk.get("title") or "").lower()
    last = m.index.max()
    row = m.loc[last]

    explanations = []
    rev = safe_float(row.get("Выручка", 0))
    exp = safe_float(row.get("Расходы", 0))
    prof = safe_float(row.get("Прибыль", 0))
    mar_pct = safe_float(row.get("Маржа", 0)) * 100
    explanations.append(f"Последний месяц: выручка {rev:,.0f}, расходы {exp:,.0f}, прибыль {prof:,.0f}, маржа {mar_pct:.1f}%.")

    if "маржа" in title:
        fact = safe_float(row.get("Маржа", 0)) * 100
        gap_pp = target_margin - fact
        impact = max(0.0, gap_pp / 100.0) * rev * 12.0
        explanations += [
            f"Целевая маржа: {target_margin:.0f}%. Фактическая: {fact:.1f}%.",
            f"Отклонение: −{gap_pp:.1f} п.п.",
        ]
        if rev > 0:
            explanations.append(f"Оценка недополученной прибыли: ≈ {impact:,.0f} {currency} в год (если тренд сохранится).")

    if "падение маржи" in title:
        explanations.append("Маржа снизилась относительно прошлого месяца — это ухудшает устойчивость прибыли.")

    if "концентрация" in title:
        explanations += [
            "Одна категория расходов занимает непропорционально большую долю.",
            "При высокой концентрации любое увеличение в этой категории резко бьёт по прибыли."
        ]

    if "убыток" in title:
        explanations += [
            "Расходы превысили выручку в последнем месяце.",
            "Это означает отрицательный финансовый результат за период."
        ]

    if "рост расходов" in title:
        explanations += [
            "Расходы выросли быстрее, чем ранее, что может продолжить снижать маржу.",
            "Часто причина — разовые платежи или рост постоянных затрат."
        ]

    return explanations


# =========================
# XLSX export
# =========================
def build_xlsx_export(normalized: pd.DataFrame, metrics: pd.DataFrame, risks: list, currency: str) -> BytesIO:
    buf = BytesIO()

    if risks:
        risks_df = pd.DataFrame([{
            "Уровень": r.get("level"),
            "Заголовок": r.get("title"),
            "Детали": r.get("details"),
        } for r in risks])
    else:
        risks_df = pd.DataFrame([{"Уровень": "", "Заголовок": "Рисков не выявлено", "Детали": ""}])

    metrics_out = metrics.copy()
    if not metrics_out.empty:
        metrics_out = metrics_out.reset_index()
        idx_col = metrics_out.columns[0]
        metrics_out = metrics_out.rename(columns={idx_col: "Месяц"})
        metrics_out["Месяц"] = pd.to_datetime(metrics_out["Месяц"], errors="coerce").dt.strftime("%Y-%m")

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        normalized_out = normalized.copy()
        normalized_out["date"] = pd.to_datetime(normalized_out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        normalized_out.to_excel(writer, index=False, sheet_name="Transactions")
        (metrics_out if not metrics_out.empty else pd.DataFrame([{"Месяц": ""}])).to_excel(writer, index=False, sheet_name="Monthly_Metrics")
        risks_df.to_excel(writer, index=False, sheet_name="Risks")
        pd.DataFrame([{
            "currency": currency,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }]).to_excel(writer, index=False, sheet_name="Meta")

    buf.seek(0)
    return buf


# =========================
# PDF (consulting style)
# =========================
FONT_FILE = "DejaVuSans.ttf"
if os.path.exists(FONT_FILE):
    pdfmetrics.registerFont(TTFont("MainFont", FONT_FILE))
    FONT_OK = True
else:
    FONT_OK = False


def pick_main_risk(risks: list) -> dict | None:
    if not risks:
        return None
    for r in risks:
        if r.get("level") == "CRIT":
            return r
    return risks[0]


def pdf_block(title: str, body_html: str, styles, bg, border, pad=10):
    t = Table([[Paragraph(f"<b>{title}</b>", styles["B_H3"]),
                Paragraph(body_html, styles["B_BODY"])]],
              colWidths=[45*mm, 135*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 1, border),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), pad),
    ]))
    return t


def pdf_kpi_cards(kpis: list[tuple[str, str]], styles):
    cells = []
    for label, value in kpis:
        card = Table(
            [[Paragraph(f"<font color='#667085'>{label}</font>", styles["B_SMALL"])],
             [Paragraph(f"<b>{value}</b>", styles["B_KPI"])]],
            colWidths=[43*mm]
        )
        card.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#EAECF0")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        cells.append(card)

    row = Table([cells], colWidths=[45*mm, 45*mm, 45*mm, 45*mm])
    row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return row


def pdf_money_big(title: str, value: str, subtitle: str, styles, bg, border):
    tbl = Table(
        [[Paragraph(f"<b>{title}</b>", styles["B_H3"])],
         [Paragraph(value, styles["B_BIG"])],
         [Paragraph(subtitle, styles["B_SMALL"])]],
        colWidths=[180*mm]
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 1, border),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    return tbl


def build_pdf(company_name: str, source_name: str, period_text: str,
              status: str, m: pd.DataFrame, risks, insights, actions,
              business_type: str, target_margin: float, currency: str, cmp) -> BytesIO:
    if not FONT_OK:
        raise FileNotFoundError(f"Не найден шрифт {FONT_FILE}. Положи его рядом с app.py")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="B_TITLE", fontName="MainFont", fontSize=20, leading=24, spaceAfter=4))
    styles.add(ParagraphStyle(name="B_SUB", fontName="MainFont", fontSize=10, leading=14, textColor=colors.HexColor("#475467")))
    styles.add(ParagraphStyle(name="B_H2", fontName="MainFont", fontSize=12, leading=16, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#101828")))
    styles.add(ParagraphStyle(name="B_H3", fontName="MainFont", fontSize=11, leading=14, spaceAfter=4, textColor=colors.HexColor("#101828")))
    styles.add(ParagraphStyle(name="B_BODY", fontName="MainFont", fontSize=10, leading=14, textColor=colors.HexColor("#101828")))
    styles.add(ParagraphStyle(name="B_SMALL", fontName="MainFont", fontSize=8.5, leading=11, textColor=colors.HexColor("#667085")))
    styles.add(ParagraphStyle(name="B_KPI", fontName="MainFont", fontSize=14, leading=18, textColor=colors.HexColor("#101828")))
    styles.add(ParagraphStyle(name="B_BIG", fontName="MainFont", fontSize=18, leading=22, textColor=colors.HexColor("#101828")))
    styles.add(ParagraphStyle(name="B_TAG", fontName="MainFont", fontSize=10, leading=12, textColor=colors.white))

    if status == "CRITICAL":
        status_bg = colors.HexColor("#D92D20")
        status_sub = "Есть серьёзные риски — нужно действие"
    elif status == "WARNING":
        status_bg = colors.HexColor("#F79009")
        status_sub = "Есть отклонения — стоит проверить"
    else:
        status_bg = colors.HexColor("#12B76A")
        status_sub = "Критичных отклонений не обнаружено"

    c_border = colors.HexColor("#EAECF0")

    story = []

    # =========================
    # PAGE 1 — Executive Summary
    # =========================
    story.append(Paragraph("Отчёт для собственника", styles["B_TITLE"]))
    story.append(Paragraph(
        f"<b>{company_name}</b> · {business_type} · Цель маржи: <b>{target_margin:.0f}%</b> · Валюта: <b>{currency}</b>",
        styles["B_SUB"]
    ))
    story.append(Paragraph(f"Период: <b>{period_text}</b> · Источник: {source_name}", styles["B_SUB"]))
    story.append(Spacer(1, 8))

    status_tbl = Table(
        [[Paragraph(f"<b>STATUS: {status}</b>", styles["B_TAG"]),
          Paragraph(status_sub, ParagraphStyle("tmp", parent=styles["B_SUB"], textColor=colors.white))]],
        colWidths=[50*mm, 130*mm]
    )
    status_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), status_bg),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(status_tbl)
    story.append(Spacer(1, 10))

    # KPI cards (last month)
    last_rev = last_exp = last_profit = last_margin = 0.0
    if m is not None and not m.empty:
        last = m.index.max()
        row = m.loc[last]
        last_rev = safe_float(row.get("Выручка", 0))
        last_exp = safe_float(row.get("Расходы", 0))
        last_profit = safe_float(row.get("Прибыль", 0))
        last_margin = safe_float(row.get("Маржа", 0))

    kpis = [
        ("Выручка (мес.)", fmt_money(last_rev, currency)),
        ("Расходы (мес.)", fmt_money(last_exp, currency)),
        ("Прибыль (мес.)", fmt_money(last_profit, currency)),
        ("Маржа (мес.)", f"{last_margin:.1%}"),
    ]
    story.append(pdf_kpi_cards(kpis, styles))
    story.append(Spacer(1, 10))

    # Main issue
    main_risk = pick_main_risk(risks)
    if main_risk:
        t = main_risk.get("title", "Главная проблема месяца")
        d = main_risk.get("details", "")
        bg = colors.HexColor("#FEF3F2") if main_risk.get("level") == "CRIT" else colors.HexColor("#FFFAEB")
        br = colors.HexColor("#FDA29B") if main_risk.get("level") == "CRIT" else colors.HexColor("#FEC84B")
        story.append(pdf_block("Главная проблема месяца", f"{t}<br/>{d}", styles, bg=bg, border=br))
    else:
        story.append(pdf_block("Главная проблема месяца", "Критичных проблем не выявлено по текущим правилам.", styles,
                               bg=colors.HexColor("#ECFDF3"), border=colors.HexColor("#ABEFC6")))
    story.append(Spacer(1, 8))

    # Financial effect (big number)
    target_m = target_margin / 100.0
    gap = max(0.0, target_m - last_margin)
    annual_impact = gap * last_rev * 12.0

    if last_rev > 0 and gap > 0:
        story.append(pdf_money_big(
            "Оценка потери прибыли",
            f"≈ {fmt_money(annual_impact, currency)} / год",
            "При сохранении текущей маржи: (цель − факт) × выручка × 12.",
            styles,
            bg=colors.HexColor("#F8FAFC"),
            border=c_border
        ))
    else:
        story.append(pdf_money_big(
            "Оценка потери прибыли",
            "—",
            "Недостаточно выручки или маржа не ниже цели.",
            styles,
            bg=colors.HexColor("#F8FAFC"),
            border=c_border
        ))
    story.append(Spacer(1, 10))

    # 3 actions
    top_actions = (actions or [])[:3]
    actions_html = "<br/>".join([f"• {a}" for a in top_actions]) if top_actions else "• Проверь корректность данных и категорий расходов."
    story.append(pdf_block("Первые действия (2–4 недели)", actions_html, styles,
                           bg=colors.HexColor("#F0F9FF"), border=colors.HexColor("#B2DDFF")))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Отчёт сформирован автоматически. Для управленческих решений рекомендуется сверка первичных данных.", styles["B_SMALL"]))

    # =========================
    # PAGE 2 — Explainability
    # =========================
    story.append(PageBreak())
    story.append(Paragraph("Почему система считает это риском", styles["B_TITLE"]))
    story.append(Paragraph("Прозрачная логика: факт → отклонение → последствия.", styles["B_SUB"]))
    story.append(Spacer(1, 10))

    if main_risk:
        expl = explain_risk(main_risk, m=m, target_margin=target_margin, currency=currency)
        bullets = "<br/>".join([f"• {e}" for e in expl[:10]]) if expl else "Недостаточно данных для подробного объяснения."
        story.append(pdf_block("Обоснование", bullets, styles, bg=colors.HexColor("#FFFFFF"), border=c_border))
    else:
        story.append(pdf_block("Обоснование", "Рисков не выявлено по текущим правилам.", styles, bg=colors.HexColor("#FFFFFF"), border=c_border))

    story.append(Spacer(1, 10))

    if cmp:
        mom_html = (
            f"• Выручка MoM: {cmp.get('revenue_change',0):+.1%}<br/>"
            f"• Расходы MoM: {cmp.get('expense_change',0):+.1%}<br/>"
            f"• Маржа MoM: {cmp.get('margin_pp',0):+.1f} п.п."
        )
        story.append(pdf_block("Изменения месяц-к-месяцу", mom_html, styles, bg=colors.HexColor("#F8FAFC"), border=c_border))
    else:
        story.append(pdf_block("Изменения месяц-к-месяцу", "Недостаточно месяцев для сравнения.", styles, bg=colors.HexColor("#F8FAFC"), border=c_border))

    # =========================
    # PAGE 3 — Details
    # =========================
    story.append(PageBreak())
    story.append(Paragraph("Детали и наблюдения", styles["B_TITLE"]))
    story.append(Paragraph("Для сверки и уточнения причин отклонений.", styles["B_SUB"]))
    story.append(Spacer(1, 10))

    # compact KPI table
    kpi_data = [["Показатель", "Значение"]]
    if m is not None and not m.empty:
        kpi_data += [
            ["Выручка (посл. мес.)", fmt_money(last_rev, currency)],
            ["Расходы (посл. мес.)", fmt_money(last_exp, currency)],
            ["Прибыль (посл. мес.)", fmt_money(last_profit, currency)],
            ["Маржа (посл. мес.)", f"{last_margin:.1%}"],
        ]
        if cmp:
            kpi_data += [
                ["Выручка MoM", f"{cmp['revenue_change']:+.1%}"],
                ["Расходы MoM", f"{cmp['expense_change']:+.1%}"],
                ["Маржа MoM", f"{cmp['margin_pp']:+.1f} п.п."],
            ]
    else:
        kpi_data += [["Нет данных", "—"]]

    kpi_tbl = Table(kpi_data, colWidths=[110*mm, 70*mm])
    kpi_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "MainFont"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F4F7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#101828")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EAECF0")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Риски и тревоги", styles["B_H2"]))
    if not risks:
        story.append(Paragraph("Отклонений по текущим правилам не выявлено.", styles["B_BODY"]))
    else:
        for r in risks:
            lvl = r.get("level")
            tag = "CRIT" if lvl == "CRIT" else "WARN"
            bg = colors.HexColor("#FEF3F2") if lvl == "CRIT" else colors.HexColor("#FFFAEB")
            br = colors.HexColor("#FDA29B") if lvl == "CRIT" else colors.HexColor("#FEC84B")
            story.append(KeepTogether([
                pdf_block(f"{tag}: {r.get('title','')}", r.get("details",""), styles, bg=bg, border=br, pad=8),
                Spacer(1, 6)
            ]))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Управленческие выводы", styles["B_H2"]))
    for i in (insights or [])[:8]:
        story.append(Paragraph(f"• {i}", styles["B_BODY"]))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Рекомендованные действия", styles["B_H2"]))
    for a in (actions or [])[:8]:
        story.append(Paragraph(f"• {a}", styles["B_BODY"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"Источник: {source_name} · Период: {period_text} · Сформировано: {datetime.now().strftime('%d.%m.%Y')}",
        styles["B_SMALL"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf


# =========================
# OWNER MODE
# =========================
def render_owner_mode(company_name: str, source_name: str, period_text: str,
                      status: str, m: pd.DataFrame, risks, insights, actions,
                      business_type: str, target_margin: float, currency: str, cmp, pdf_buf):
    st.markdown(f"""
    <div class="card">
      <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px;">
        <div>
          <div class="title-xl">Финансовая картина за месяц</div>
          <p class="subtitle">{company_name} · Период: {period_text} · Источник: {source_name}</p>
        </div>
        <div>{ui_badge(status)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    main_risk = pick_main_risk(risks)

    last_rev = last_exp = last_profit = last_margin = 0.0
    if m is not None and not m.empty:
        last = m.index.max()
        row = m.loc[last]
        last_rev = safe_float(row.get("Выручка", 0))
        last_exp = safe_float(row.get("Расходы", 0))
        last_profit = safe_float(row.get("Прибыль", 0))
        last_margin = safe_float(row.get("Маржа", 0))

    target_m = target_margin / 100.0
    gap = max(0.0, target_m - last_margin)
    annual_impact = gap * last_rev * 12.0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(ui_kpi_card("Выручка (посл. месяц)", fmt_money(last_rev, currency)), unsafe_allow_html=True)
    c2.markdown(ui_kpi_card("Расходы (посл. месяц)", fmt_money(last_exp, currency)), unsafe_allow_html=True)
    c3.markdown(ui_kpi_card("Прибыль (посл. месяц)", fmt_money(last_profit, currency)), unsafe_allow_html=True)
    c4.markdown(ui_kpi_card("Маржа (посл. месяц)", f"{last_margin:.1%}"), unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([2, 1])

    with left:
        st.markdown(ui_section("Главная проблема месяца", "Один сигнал, который требует внимания"), unsafe_allow_html=True)
        if main_risk:
            lvl = main_risk.get("level")
            title = main_risk.get("title", "")
            details = main_risk.get("details", "")
            stripe = "var(--bad)" if lvl == "CRIT" else "var(--warn)"
            st.markdown(f"""
            <div class="card">
              <div style="display:flex; gap:12px; align-items:flex-start;">
                <div style="width:6px; border-radius:999px; background:{stripe};"></div>
                <div>
                  <div style="font-weight:780; font-size:16px;">{title}</div>
                  <div class="subtitle" style="margin-top:6px; font-size:15px; line-height:1.35">{details}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 Почему это считается риском?"):
                expl = explain_risk(main_risk, m=m, target_margin=target_margin, currency=currency)
                if expl:
                    for e in expl:
                        st.write("•", e)
                else:
                    st.write("Недостаточно данных для подробного объяснения.")
        else:
            st.markdown("""
            <div class="card">
              <div style="font-weight:780; font-size:16px;">Критичных проблем не выявлено</div>
              <div class="subtitle" style="margin-top:6px">Система не видит опасных отклонений по текущим правилам.</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.markdown(ui_section("Что изменилось (MoM)", "Сравнение с прошлым месяцем"), unsafe_allow_html=True)
        if cmp:
            a, b, c = st.columns(3)
            a.markdown(ui_kpi_card("Выручка", f"{cmp.get('revenue_change',0):+.1%}"), unsafe_allow_html=True)
            b.markdown(ui_kpi_card("Расходы", f"{cmp.get('expense_change',0):+.1%}"), unsafe_allow_html=True)
            c.markdown(ui_kpi_card("Маржа", f"{cmp.get('margin_pp',0):+.1f} п.п."), unsafe_allow_html=True)
        else:
            st.info("Недостаточно месяцев для сравнения.")

        st.write("")
        st.markdown(ui_section("Первые действия", "Что сделать в ближайшие 2–4 недели"), unsafe_allow_html=True)
        if actions:
            st.markdown("<div class='card'>" + "".join([f"<div>• {a}</div>" for a in actions[:3]]) + "</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='card'>• Проверить корректность данных и категорий расходов</div>", unsafe_allow_html=True)

    with right:
        st.markdown(ui_section("Финансовый эффект", "Оценка потери прибыли при недоборе маржи"), unsafe_allow_html=True)
        if last_rev > 0 and gap > 0:
            st.markdown(ui_kpi_card(
                "Потеря прибыли (оценка/год)",
                fmt_money(annual_impact, currency),
                hint=f"(цель {target_margin:.0f}% − факт {last_margin*100:.1f}%) × выручка × 12"
            ), unsafe_allow_html=True)
        else:
            st.markdown("<div class='card'>Нет потери прибыли по цели маржи (или нет выручки).</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown(ui_section("Отчёт", "PDF для пересылки"), unsafe_allow_html=True)
        if not FONT_OK:
            st.error(f"Не найден шрифт {FONT_FILE}. Положи его рядом с app.py.")
        else:
            if pdf_buf is not None:
                st.download_button(
                    "⬇️ Скачать PDF (Owner report)",
                    data=pdf_buf,
                    file_name="owner_report.pdf",
                    mime="application/pdf",
                    width="stretch",
                )
            else:
                st.info("Сначала сделай анализ — появится кнопка PDF.")


# =========================
# ANALYTICS (details)
# =========================
def render_analytics(df_raw: pd.DataFrame, normalized: pd.DataFrame, m: pd.DataFrame, risks, status: str,
                     insights, actions, currency: str, target_margin: float):
    st.markdown("## 📈 Аналитика и детали")

    st.markdown(ui_section("Динамика по месяцам", "Выручка / расходы / прибыль"), unsafe_allow_html=True)
    if m is not None and not m.empty:
        st.line_chart(m[["Выручка", "Расходы", "Прибыль"]])
    else:
        st.info("Недостаточно данных для графика.")

    st.write("")
    st.markdown(ui_section("Риски и тревоги", "Что выглядит опасно по правилам"), unsafe_allow_html=True)
    if status == "CRITICAL":
        st.error("🔴 CRITICAL — есть серьёзные риски, нужно действие.")
    elif status == "WARNING":
        st.warning("🟠 WARNING — есть отклонения, стоит проверить.")
    elif status == "OK":
        st.success("🟢 OK — критичных отклонений не обнаружено.")
    else:
        st.info("ℹ️ N/A — недостаточно данных.")

    if risks:
        for r in risks:
            lvl = r.get("level")
            title = r.get("title", "")
            details = r.get("details", "")
            stripe = "var(--bad)" if lvl == "CRIT" else "var(--warn)"
            st.markdown(f"""
            <div class="card">
              <div style="display:flex; gap:12px; align-items:flex-start;">
                <div style="width:6px; border-radius:999px; background:{stripe};"></div>
                <div>
                  <div style="font-weight:780; font-size:16px;">{title}</div>
                  <div class="subtitle" style="margin-top:6px; font-size:15px; line-height:1.35">{details}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 Почему это считается риском?"):
                expl = explain_risk(r, m=m, target_margin=target_margin, currency=currency)
                if expl:
                    for e in expl:
                        st.write("•", e)
                else:
                    st.write("Недостаточно данных для подробного объяснения.")

            st.write("")
    else:
        st.info("Риски не выявлены по текущим правилам.")

    st.markdown(ui_section("Управленческие выводы", ""), unsafe_allow_html=True)
    for i in insights or []:
        st.write("•", i)

    st.markdown(ui_section("Рекомендованные действия", ""), unsafe_allow_html=True)
    for a in actions or []:
        st.write("•", a)

    st.write("")
    st.markdown(ui_section("Данные (нормализованные)", "Можно скачать в XLSX"), unsafe_allow_html=True)
    st.dataframe(normalized.head(200), width="stretch")

    xlsx_buf = build_xlsx_export(normalized=normalized, metrics=m, risks=risks, currency=currency)
    st.download_button(
        "⬇️ Скачать XLSX (Transactions + Metrics + Risks)",
        data=xlsx_buf,
        file_name="dashboard_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch"
    )


# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## ⚙️ Профиль компании")
company_name = st.sidebar.text_input("Название компании", value="Моя компания")
business_type = st.sidebar.selectbox("Тип бизнеса", ["Услуги", "Торговля", "IT / Digital", "Производство"], index=0)
target_margin = st.sidebar.slider("Целевая маржа, %", 5, 80, 30, 5)
currency = st.sidebar.selectbox("Валюта", ["₸", "₽", "$", "€"], index=0)

st.sidebar.markdown("---")
view_mode = st.sidebar.radio("Режим", ["Собственник", "Аналитика"], index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("## 📂 Данные")
uploaded = st.sidebar.file_uploader("Загрузи Excel (.xlsx) или CSV", type=["xlsx", "csv"])


# =========================
# MAIN FLOW
# =========================
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

if uploaded is None:
    st.markdown("""
    <div class="card">
      <div class="title-xl">Отчёт для собственника</div>
      <p class="subtitle">Загрузи файл расходов/доходов и получи: главную проблему месяца, MoM-изменения, финансовый эффект и PDF.</p>
      <div style="height:12px"></div>
      <div class="subtitle">Поддерживается Excel/CSV. Минимум: <b>Дата</b> и <b>Сумма</b>.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Load file
try:
    df_raw = read_file(uploaded)
except Exception as e:
    st.error(f"Не удалось прочитать файл: {e}")
    st.stop()

st.markdown(ui_section("Предпросмотр файла", "Проверь первые строки — всё ли ок"), unsafe_allow_html=True)
st.dataframe(df_raw.head(30), width="stretch")

auto = guess_by_content(df_raw, guess_columns(df_raw.columns))
cols = ["(не выбрано)"] + list(df_raw.columns)

def pick(label, suggested, key):
    idx = cols.index(suggested) if suggested in cols else 0
    return st.selectbox(label, cols, index=idx, key=key)

st.markdown(ui_section("Сопоставление колонок", "Выбери правильные поля (минимум дата и сумма)"), unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    date_col = pick("Дата", auto["date"], "date")
    amount_col = pick("Сумма", auto["amount"], "amount")
with c2:
    type_col = pick("Тип (income/expense) — опционально", auto["type"], "type")
    category_col = pick("Категория — опционально", auto["category"], "category")
with c3:
    project_col = pick("Проект/филиал — опционально", auto["project"], "project")

if date_col == "(не выбрано)" or amount_col == "(не выбрано)":
    st.warning("Нужно выбрать минимум: Дата и Сумма.")
    st.stop()

# Normalize
out = pd.DataFrame()
out["date"] = pd.to_datetime(df_raw[date_col], errors="coerce")
out["amount"] = pd.to_numeric(df_raw[amount_col], errors="coerce")

if type_col != "(не выбрано)":
    out["type"] = df_raw[type_col].astype(str).str.lower().str.strip()
else:
    out["type"] = out["amount"].apply(lambda x: "expense" if pd.notna(x) and x < 0 else "income")

out["category"] = df_raw[category_col].astype(str).str.strip() if category_col != "(не выбрано)" else "Без категории"
out["project"] = df_raw[project_col].astype(str).str.strip() if project_col != "(не выбрано)" else "Основной"

out = out.dropna(subset=["date", "amount"])

# Make amount signs consistent with type
out.loc[out["type"].str.contains("expense|расход", na=False), "amount"] = -out["amount"].abs()
out.loc[out["type"].str.contains("income|доход", na=False), "amount"] = out["amount"].abs()

# Filter period
min_date = out["date"].min()
max_date = out["date"].max()
if pd.isna(min_date) or pd.isna(max_date):
    st.error("Не удалось определить диапазон дат. Проверь колонку даты.")
    st.stop()

st.markdown(ui_section("Период отчёта", "Можно сузить диапазон"), unsafe_allow_html=True)
dr = st.date_input("Период", value=(min_date.date(), max_date.date()), min_value=min_date.date(), max_value=max_date.date())
start = pd.to_datetime(dr[0])
end = pd.to_datetime(dr[1])

flt = out[(out["date"] >= start) & (out["date"] <= end)].copy()

# Compute
m = compute_metrics(flt)
cmp = compare_periods(m)
risks, status = calc_risks(flt, m, target_margin=target_margin)
insights, actions = generate_insights(risks=risks, m=m, cmp=cmp, business_type=business_type, target_margin=target_margin)

period_text = f"{start.strftime('%d.%m.%Y')}–{end.strftime('%d.%m.%Y')}"
source_name = uploaded.name

pdf_buf = None
if FONT_OK:
    try:
        pdf_buf = build_pdf(
            company_name=company_name,
            source_name=source_name,
            period_text=period_text,
            status=status,
            m=m,
            risks=risks,
            insights=insights,
            actions=actions,
            business_type=business_type,
            target_margin=target_margin,
            currency=currency,
            cmp=cmp
        )
    except Exception as e:
        pdf_buf = None
        st.warning(f"PDF не собрался: {e}")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

if view_mode == "Собственник":
    render_owner_mode(
        company_name=company_name,
        source_name=source_name,
        period_text=period_text,
        status=status,
        m=m,
        risks=risks,
        insights=insights,
        actions=actions,
        business_type=business_type,
        target_margin=target_margin,
        currency=currency,
        cmp=cmp,
        pdf_buf=pdf_buf
    )

    st.write("")
    show_details = st.checkbox("Показать детали (аналитика)", value=False)
    if show_details:
        render_analytics(df_raw=df_raw, normalized=flt, m=m, risks=risks, status=status,
                         insights=insights, actions=actions, currency=currency, target_margin=target_margin)
else:
    render_analytics(df_raw=df_raw, normalized=flt, m=m, risks=risks, status=status,
                     insights=insights, actions=actions, currency=currency, target_margin=target_margin)
