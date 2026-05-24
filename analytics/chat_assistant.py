"""
Context-aware water quality chat assistant.

Default mode: rule-based answers from the filtered dataset (no external API).
Optional mode: Ollama local LLM when OLLAMA_BASE_URL is set.

Metrics align with the dashboard: chemical pollutants for pollution/risk/trend;
high-risk region = most records with ratio > 2 (not highest mean ratio alone).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

import pandas as pd

from analytics.ai_insights import generate_insights

NON_CHEMICAL_POLLUTANTS = frozenset({"Water_Level_cm", "Mixed_Chemicals"})

CHAT_DISCLAIMER_EN = (
    "This assistant uses your current dashboard filters. "
    "Pollution metrics use chemical indicators only (excludes water-level proxies). "
    "Not regulatory advice."
)
CHAT_DISCLAIMER_RU = (
    "Ответы основаны на текущих фильтрах. "
    "Показатели загрязнения — только химические индикаторы (без уровня воды). "
    "Не нормативная рекомендация."
)

SUGGESTIONS_EN = [
    "What is the mean WQI for chemical pollutants?",
    "Which region has the most high-risk records?",
    "Is chemical water quality improving or deteriorating?",
    "Explain the high-risk share",
]
SUGGESTIONS_RU = [
    "Какой средний WQI по химическим показателям?",
    "В каком регионе больше всего записей высокого риска?",
    "Улучшается или ухудшается качество по химии?",
    "Объясни долю высокого риска",
]


def _disclaimer(lang: str) -> str:
    return CHAT_DISCLAIMER_RU if lang == "ru" else CHAT_DISCLAIMER_EN


def _suggestions(lang: str) -> list[str]:
    return list(SUGGESTIONS_RU if lang == "ru" else SUGGESTIONS_EN)


def _chemical_df(df: pd.DataFrame) -> pd.DataFrame:
    if "Pollutant" not in df.columns:
        return df
    return df[~df["Pollutant"].isin(NON_CHEMICAL_POLLUTANTS)]


def _stats_block(sub: pd.DataFrame) -> dict[str, Any]:
    if sub.empty:
        return {}
    return {
        "records": int(len(sub)),
        "mean_wqi": round(float(sub["WQI_Score"].mean()), 2),
        "mean_ratio": round(float(sub["Ratio"].mean()), 2),
        "high_risk_pct": round(float((sub["Ratio"] > 2).mean() * 100), 1),
        "moderate_risk_pct": round(float(((sub["Ratio"] >= 1) & (sub["Ratio"] <= 2)).mean() * 100), 1),
    }


def _high_risk_leader(sub: pd.DataFrame) -> tuple[str | None, int, float | None]:
    """Region with the most ratio > 2 records (matches dashboard risk table)."""
    high = sub[sub["Ratio"] > 2]
    if high.empty or "Region" not in high.columns:
        return None, 0, None
    counts = high.groupby("Region").size().sort_values(ascending=False)
    region = str(counts.index[0])
    count = int(counts.iloc[0])
    share = round(count / len(sub[sub["Region"] == region]) * 100, 1) if len(sub[sub["Region"] == region]) else None
    return region, count, share


def _mean_ratio_leader(sub: pd.DataFrame) -> tuple[str | None, float | None]:
    if sub.empty or "Region" not in sub.columns:
        return None, None
    regional = sub.groupby("Region")["Ratio"].mean().sort_values(ascending=False)
    if regional.empty:
        return None, None
    return str(regional.index[0]), round(float(regional.iloc[0]), 2)


def _wqi_extremes(sub: pd.DataFrame) -> dict[str, Any]:
    if sub.empty or "Region" not in sub.columns:
        return {}
    by_region = sub.groupby("Region")["WQI_Score"].mean().sort_values()
    if by_region.empty:
        return {}
    return {
        "best_wqi_region": str(by_region.index[0]),
        "best_wqi": round(float(by_region.iloc[0]), 2),
        "worst_wqi_region": str(by_region.index[-1]),
        "worst_wqi": round(float(by_region.iloc[-1]), 2),
    }


def _trend_block(sub: pd.DataFrame) -> dict[str, Any]:
    if sub.empty or "Year" not in sub.columns:
        return {}
    yearly = sub.groupby("Year")["WQI_Score"].mean().dropna().sort_index()
    if len(yearly) < 2:
        return {"trend_years": len(yearly)}
    delta = float(yearly.iloc[-1] - yearly.iloc[0])
    return {
        "year_range": [int(yearly.index[0]), int(yearly.index[-1])],
        "wqi_trend_delta": round(delta, 2),
        "trend_direction": "deteriorating" if delta > 0 else ("stable" if abs(delta) < 0.5 else "improving"),
        "trend_start_wqi": round(float(yearly.iloc[0]), 2),
        "trend_end_wqi": round(float(yearly.iloc[-1]), 2),
    }


def build_context(df: pd.DataFrame) -> dict[str, Any]:
    """Summarise filtered data — pollution metrics on chemical subset."""
    if df.empty:
        return {"empty": True, "records": 0}

    chem = _chemical_df(df)
    ctx: dict[str, Any] = {
        "empty": False,
        "records_total": int(len(df)),
        "records_chemical": int(len(chem)),
        "observed_pct": round(float((df["data_source"] == "observed").mean() * 100), 1)
        if "data_source" in df.columns else None,
    }

    # Primary pollution stats = chemical only (consistent with heatmap / hazard logic)
    poll = _stats_block(chem if not chem.empty else df)
    ctx.update(poll)
    ctx["records"] = ctx.get("records", ctx["records_total"])
    ctx["using_chemical_subset"] = not chem.empty and len(chem) < len(df)

    analysis = chem if not chem.empty else df
    hr_region, hr_count, _ = _high_risk_leader(analysis)
    ctx["high_risk_leader_region"] = hr_region
    ctx["high_risk_leader_count"] = hr_count
    mr_region, mr_ratio = _mean_ratio_leader(analysis)
    ctx["top_mean_ratio_region"] = mr_region
    ctx["top_mean_ratio"] = mr_ratio
    ctx.update(_wqi_extremes(analysis))
    ctx.update(_trend_block(analysis))

    if "Pollutant" in analysis.columns:
        by_poll = analysis.groupby("Pollutant")["Ratio"].mean().sort_values(ascending=False)
        if not by_poll.empty:
            ctx["worst_pollutant"] = str(by_poll.index[0])
            ctx["worst_pollutant_ratio"] = round(float(by_poll.iloc[0]), 2)

    if "data_source" in df.columns and "Region" in analysis.columns:
        high = analysis[analysis["Ratio"] > 2]
        if not high.empty:
            src = high["data_source"].value_counts(normalize=True).mul(100).round(1)
            ctx["high_risk_source_mix"] = src.to_dict()

    if "data_source" in df.columns:
        shares = (df["data_source"].value_counts(normalize=True) * 100).round(1)
        ctx["source_mix"] = shares.to_dict()

    return ctx


def _match_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def _detect_intent(message: str) -> str:
    """Priority-ordered intent — avoids 'risk' swallowing trend/region questions."""
    m = message.lower()
    if _match_any(m, [r"\btrend\b", r"тренд", r"динамик", r"улучш", r"ухудш", r"improv", r"deterior", r"год к году"]):
        return "trend"
    if _match_any(m, [
        r"which region.*risk", r"highest risk region", r"most high.risk", r"riskiest region",
        r"какой регион.*риск", r"самый рискован", r"больше всего.*риск", r"где больше.*риск",
    ]):
        return "risk_region"
    if _match_any(m, [r"priorit", r"actionable", r"комбинац", r"рекоменд", r"summarize.*3", r"три приоритет"]):
        return "priorities"
    if _match_any(m, [r"\bwqi\b", r"индекс", r"качеств"]):
        return "wqi"
    if _match_any(m, [r"\brisk\b", r"риск", r"опасн", r"threshold", r"порог", r"high.risk share", r"дол[яи]"]):
        return "risk"
    if _match_any(m, [r"\bregion\b", r"регион", r"област"]):
        return "region"
    if _match_any(m, [r"pollut", r"загрязн", r"nitrat", r"copper", r"нитрат", r"медь"]):
        return "pollutant"
    if _match_any(m, [r"\bml\b", r"forecast", r"прогноз", r"model", r"модел"]):
        return "ml"
    if _match_any(m, [r"\bdata\b", r"dataset", r"источник", r"данн", r"source", r"observed", r"reconstructed"]):
        return "data"
    if _match_any(m, [r"\bhelp\b", r"что ты", r"что умеешь", r"помощь", r"help me"]):
        return "help"
    return "general"


def _subset_note(ctx: dict[str, Any], lang: str) -> str:
    if not ctx.get("using_chemical_subset"):
        return ""
    n_chem = ctx.get("records_chemical", 0)
    n_total = ctx.get("records_total", 0)
    if lang == "ru":
        return f" (метрики загрязнения: {n_chem:,} хим. записей из {n_total:,})"
    return f" (pollution metrics: {n_chem:,} chemical records of {n_total:,})"


def _rule_reply(message: str, ctx: dict[str, Any], lang: str) -> str | None:
    if ctx.get("empty"):
        return (
            "Нет данных для текущих фильтров. Расширьте выборку."
            if lang == "ru"
            else "No data for the current filters. Try widening your selection."
        )

    intent = _detect_intent(message)
    n = ctx.get("records_chemical") or ctx["records"]
    note = _subset_note(ctx, lang)
    ru = lang == "ru"

    if intent == "help":
        if ru:
            return (
                "Я отвечаю по **химическим показателям** загрязнения (WQI, риск, регионы, тренды) "
                f"на основе текущих фильтров.{note}"
            )
        return (
            f"I answer using **chemical pollution** indicators for your current filters.{note}"
        )

    if intent == "trend":
        direction = ctx.get("trend_direction")
        delta = ctx.get("wqi_trend_delta")
        yr = ctx.get("year_range", [])
        if direction and delta is not None and len(yr) == 2:
            start_w = ctx.get("trend_start_wqi", "—")
            end_w = ctx.get("trend_end_wqi", "—")
            if ru:
                word = {"deteriorating": "ухудшается", "improving": "улучшается", "stable": "стабильно"}[direction]
                return (
                    f"По химическим показателям качество **{word}**: WQI **{start_w}** → **{end_w}** "
                    f"(Δ **{delta:+.2f}**, {yr[0]}–{yr[1]}, n={n:,}).{note} "
                    "Выше WQI = больше загрязнение относительно ПДК."
                )
            return (
                f"For **chemical indicators**, quality is **{direction}**: WQI **{start_w}** → **{end_w}** "
                f"(Δ **{delta:+.2f}**, {yr[0]}–{yr[1]}, n={n:,}).{note} "
                "Higher WQI = more pollution relative to MPC."
            )
        if ru:
            return f"Недостаточно лет с химическими данными для тренда (нужно ≥ 2).{note}"
        return f"Not enough years with chemical data for a trend (need ≥ 2).{note}"

    if intent == "risk_region":
        leader = ctx.get("high_risk_leader_region")
        count = ctx.get("high_risk_leader_count", 0)
        mean_r = ctx.get("top_mean_ratio_region")
        mean_v = ctx.get("top_mean_ratio")
        if leader:
            if ru:
                return (
                    f"Больше всего записей **высокого риска** (отношение > 2× ПДК) в **{leader}**: **{count}** записей. "
                    f"По **среднему** отношению к ПДК лидирует **{mean_r}** ({mean_v}) — это разные метрики.{note}"
                )
            return (
                f"Most **high-risk records** (ratio > 2× MPC) are in **{leader}**: **{count}** records. "
                f"Highest **mean ratio** is **{mean_r}** ({mean_v}) — these are different metrics.{note}"
            )
        if ru:
            return f"В текущей выборке нет записей с отношением > 2× ПДК.{note}"
        return f"No records exceed 2× MPC in the current selection.{note}"

    if intent == "wqi":
        if ru:
            return (
                f"Средний **WQI = {ctx['mean_wqi']}** по хим. показателям (n={n:,}). "
                f"Лучший регион: **{ctx.get('best_wqi_region', '—')}** ({ctx.get('best_wqi', '—')}). "
                f"Худший: **{ctx.get('worst_wqi_region', '—')}** ({ctx.get('worst_wqi', '—')}). "
                f"WQI = (C/ПДК)×50; ниже = чище.{note}"
            )
        return (
            f"Mean **WQI = {ctx['mean_wqi']}** for chemical indicators (n={n:,}). "
            f"Best region: **{ctx.get('best_wqi_region', '—')}** ({ctx.get('best_wqi', '—')}). "
            f"Worst: **{ctx.get('worst_wqi_region', '—')}** ({ctx.get('worst_wqi', '—')}). "
            f"WQI = (C/MPC)×50; lower = cleaner.{note}"
        )

    if intent == "risk":
        if ru:
            return (
                f"**Высокий риск** (> 2× ПДК): **{ctx['high_risk_pct']}%** записей. "
                f"**Умеренный** (1–2×): **{ctx['moderate_risk_pct']}%**. "
                f"Регион с наибольшим числом high-risk записей: **{ctx.get('high_risk_leader_region', '—')}** "
                f"({ctx.get('high_risk_leader_count', 0)} шт.).{note}"
            )
        return (
            f"**High risk** (> 2× MPC): **{ctx['high_risk_pct']}%** of records. "
            f"**Moderate** (1–2×): **{ctx['moderate_risk_pct']}%**. "
            f"Region with most high-risk records: **{ctx.get('high_risk_leader_region', '—')}** "
            f"({ctx.get('high_risk_leader_count', 0)} records).{note}"
        )

    if intent == "region":
        leader = ctx.get("high_risk_leader_region") or ctx.get("top_mean_ratio_region", "—")
        if ru:
            return (
                f"По high-risk записям: **{ctx.get('high_risk_leader_region', '—')}**. "
                f"По среднему отношению к ПДК: **{ctx.get('top_mean_ratio_region', '—')}** "
                f"({ctx.get('top_mean_ratio', '—')}). "
                f"WQI: **{ctx.get('best_wqi_region', '—')}** (лучший) — **{ctx.get('worst_wqi_region', '—')}** (худший).{note}"
            )
        return (
            f"By high-risk records: **{ctx.get('high_risk_leader_region', '—')}**. "
            f"By mean ratio: **{ctx.get('top_mean_ratio_region', '—')}** ({ctx.get('top_mean_ratio', '—')}). "
            f"WQI: **{ctx.get('best_wqi_region', '—')}** (best) — **{ctx.get('worst_wqi_region', '—')}** (worst).{note}"
        )

    if intent == "pollutant":
        wp = ctx.get("worst_pollutant", "—")
        wr = ctx.get("worst_pollutant_ratio", "—")
        if ru:
            return f"Самый проблемный загрязнитель: **{wp}** (ср. **{wr}** × ПДК).{note}"
        return f"Most critical pollutant: **{wp}** (mean **{wr}** × MPC).{note}"

    if intent == "priorities":
        parts = []
        if ru:
            parts.append(f"1. **Регион:** усилить контроль в **{ctx.get('high_risk_leader_region', '—')}** (лидер по high-risk записям).")
            parts.append(f"2. **Загрязнитель:** приоритет **{ctx.get('worst_pollutant', '—')}** (ср. {ctx.get('worst_pollutant_ratio', '—')}× ПДК).")
            if ctx.get("observed_pct", 0) > 90:
                parts.append(
                    f"3. **Данные:** {ctx['observed_pct']}% — уровень воды (Kazhydromet); "
                    "для нормативных выводов нужны прямые хим. замеры."
                )
            else:
                parts.append("3. **Данные:** расширить долю наблюдаемых химических измерений.")
            return "\n\n".join(parts) + note
        parts.append(f"1. **Region:** intensify monitoring in **{ctx.get('high_risk_leader_region', '—')}** (most high-risk records).")
        parts.append(f"2. **Pollutant:** prioritize **{ctx.get('worst_pollutant', '—')}** (mean {ctx.get('worst_pollutant_ratio', '—')}× MPC).")
        if ctx.get("observed_pct", 0) > 90:
            parts.append(
                f"3. **Data:** {ctx['observed_pct']}% is water-level (Kazhydromet); "
                "direct chemical sampling needed for regulatory conclusions."
            )
        else:
            parts.append("3. **Data:** expand observed chemical measurement coverage.")
        return "\n\n".join(parts) + note

    if intent == "ml":
        if ru:
            return (
                "Прогноз — вкладка **Forecast**: 8 моделей, TimeSeriesSplit CV. "
                "При n≈5 годовых точек надёжнее **линейная регрессия**."
            )
        return (
            "See **Forecast** tab: 8 models with TimeSeriesSplit CV. "
            "With n≈5 annual points, **Linear Regression** is most reliable."
        )

    if intent == "data":
        mix = ctx.get("source_mix", {})
        mix_str = ", ".join(f"{k}: {v}%" for k, v in mix.items()) if mix else "—"
        hr_mix = ctx.get("high_risk_source_mix", {})
        hr_str = ", ".join(f"{k}: {v}%" for k, v in hr_mix.items()) if hr_mix else "—"
        if ru:
            return (
                f"Вся выборка: {mix_str}. High-risk записи по источникам: {hr_str}. "
                f"Всего {ctx['records_total']:,} записей.{note}"
            )
        return (
            f"Full selection: {mix_str}. High-risk records by source: {hr_str}. "
            f"Total {ctx['records_total']:,} records.{note}"
        )

    return None


def _rule_reply_with_insights(message: str, ctx: dict[str, Any], insights: list[str], lang: str) -> str:
    specific = _rule_reply(message, ctx, lang)
    if specific:
        return specific

    chem_insights = [
        i for i in insights
        if "algorithmically" not in i.lower() and "алгоритм" not in i.lower()
    ][:2]
    if chem_insights:
        body = "\n\n".join(f"• {b.replace('**', '')}" for b in chem_insights)
        if lang == "ru":
            return f"По текущим фильтрам:\n\n{body}\n\nУточните: WQI, риск, регион, тренд или приоритеты?"
        return f"For your filters:\n\n{body}\n\nTry asking about: WQI, risk, region, trend, or priorities."

    if lang == "ru":
        return (
            f"Сводка: WQI **{ctx['mean_wqi']}**, high-risk **{ctx['high_risk_pct']}%** "
            f"(хим. данные, n={ctx.get('records_chemical', ctx['records']):,})."
        )
    return (
        f"Summary: WQI **{ctx['mean_wqi']}**, high-risk **{ctx['high_risk_pct']}%** "
        f"(chemical data, n={ctx.get('records_chemical', ctx['records']):,})."
    )


def _try_ollama(message: str, ctx: dict[str, Any], lang: str) -> str | None:
    base = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
    if not base:
        return None
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    system = (
        "You are AquaMonitor assistant for Kazakhstan water quality. "
        "Use ONLY the JSON context. Chemical metrics exclude water-level proxies. "
        "Higher WQI = worse pollution. High-risk = ratio > 2. "
        "Do not invent numbers. Not regulatory advice."
    )
    if lang == "ru":
        system += " Reply in Russian."

    payload = json.dumps({
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"Context:\n{json.dumps(ctx, ensure_ascii=False)}\n\nQuestion: {message}",
            },
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data.get("message", {}).get("content", "").strip() or None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        return None


def chat(message: str, df: pd.DataFrame, lang: str = "en") -> dict[str, Any]:
    """Answer a user message using filtered dashboard data."""
    message = (message or "").strip()
    if not message:
        empty_msg = "Задайте вопрос о качестве воды." if lang == "ru" else "Ask a question about water quality."
        return {"reply": empty_msg, "mode": "rules", "suggestions": _suggestions(lang)}

    ctx = build_context(df)
    chem = _chemical_df(df)
    insights = generate_insights(chem if not chem.empty else df) if not ctx.get("empty") else []

    ollama_reply = _try_ollama(message, ctx, lang)
    if ollama_reply:
        reply = f"{ollama_reply}\n\n_{_disclaimer(lang)}_"
        return {"reply": reply, "mode": "ollama", "suggestions": _suggestions(lang)}

    reply = _rule_reply_with_insights(message, ctx, insights, lang)
    reply = f"{reply}\n\n_{_disclaimer(lang)}_"
    return {"reply": reply, "mode": "rules", "suggestions": _suggestions(lang)}
