from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import Theme, ThemeScore
from app.schemas.mainline import (
    MainlineMarketSummary,
    MainlineRadarResponse,
    MainlineThemeScore,
    ThemeDiagnosis,
)
from app.services.akshare_service import AKShareService


ak_service = AKShareService()


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def _round(value: float) -> float:
    return round(value, 1)


def _load_news_text() -> str:
    try:
        news = ak_service.fetch_market_news(limit=30)
    except Exception:
        return ""
    return " ".join(
        f"{item.get('title') or ''} {item.get('summary') or ''}"
        for item in news
    )


def _theme_keywords(theme_name: str) -> list[str]:
    tokens = [theme_name]
    for suffix in ("概念", "板块", "行业", "设备", "技术", "产业"):
        if theme_name.endswith(suffix):
            tokens.append(theme_name.removesuffix(suffix))
    return list(dict.fromkeys(item for item in tokens if len(item) >= 2))


def _catalyst_score(theme_name: str, news_text: str) -> float:
    if not news_text:
        return 35
    direct_hits = news_text.count(theme_name)
    keyword_hits = sum(
        1 for keyword in _theme_keywords(theme_name) if keyword in news_text
    )
    return _clamp(35 + direct_hits * 25 + keyword_hits * 12)


def _crowding_penalty(score: ThemeScore, catalyst: float) -> float:
    penalty = 0.0
    if score.average_return >= 8:
        penalty += 18
    elif score.average_return >= 5:
        penalty += 12
    elif score.average_return >= 3:
        penalty += 6

    if score.advancing_ratio >= 0.9:
        penalty += 10
    elif score.advancing_ratio >= 0.78:
        penalty += 6

    if score.strong_weeks >= 5:
        penalty += 10
    elif score.strong_weeks >= 3:
        penalty += 5

    if catalyst >= 85 and score.average_return >= 4:
        penalty += 5
    return _clamp(penalty, 0, 30)


def _status(total: float, health_level: str) -> str:
    if total >= 80 and health_level != "低":
        return "强主线"
    if total >= 65:
        return "潜在主线"
    if total >= 50:
        return "轮动热点"
    if total >= 35:
        return "弱热点"
    return "噪音"


def _stage(
    total: float,
    score: ThemeScore,
    crowding_penalty: float,
    previous_score: float | None,
) -> str:
    trend = total - previous_score if previous_score is not None else 0
    if previous_score is not None and trend <= -8:
        return "退潮期"
    if crowding_penalty >= 18 and total >= 70:
        return "高潮期"
    if total >= 78 and score.advancing_ratio >= 0.65:
        return "主升期"
    if total >= 62 and trend >= -3:
        return "确认期"
    return "萌芽期"


def _health_level(
    fund: float,
    return_strength: float,
    breadth: float,
    persistence: float,
) -> str:
    weak_count = sum(
        1 for value in (fund, return_strength, breadth, persistence) if value < 45
    )
    if min(fund, return_strength, breadth) >= 60 and weak_count == 0:
        return "高"
    if weak_count <= 1:
        return "中"
    return "低"


def _risk_level(crowding_penalty: float, breadth: float, persistence: float) -> str:
    if crowding_penalty >= 18 or (breadth < 45 and persistence >= 65):
        return "高"
    if crowding_penalty >= 10 or breadth < 55:
        return "中"
    return "低"


def _reasons(
    *,
    fund: float,
    return_strength: float,
    breadth: float,
    persistence: float,
    catalyst: float,
    crowding_penalty: float,
    score: ThemeScore,
) -> list[str]:
    reasons: list[str] = []
    if fund >= 70:
        reasons.append("资金强度处于高位，成交占比对主题形成支撑。")
    elif fund >= 50:
        reasons.append("资金强度中等，具备继续观察价值。")
    else:
        reasons.append("资金强度偏弱，主线确认度不足。")

    if return_strength >= 65:
        reasons.append(
            f"成分股平均涨幅 {score.average_return:.2f}%，涨幅强度较好。"
        )
    if breadth >= 65:
        reasons.append(
            f"上涨成分股占比 {(score.advancing_ratio * 100):.1f}%，扩散情况较好。"
        )
    elif breadth < 45:
        reasons.append("上涨扩散不足，当前更依赖局部个股表现。")
    if persistence >= 65:
        reasons.append(f"已连续强势 {score.strong_weeks} 个周期，持续性较强。")
    if catalyst >= 65:
        reasons.append("近期资讯中出现相关催化，叙事关注度提升。")
    if crowding_penalty >= 15:
        reasons.append("短期拥挤度偏高，继续上行需要更多增量资金承接。")
    return reasons[:5]


def _watch_points(stage: str, risk_level: str, crowding_penalty: float) -> list[str]:
    points = [
        "观察成交额是否继续放大，避免仅靠短期涨幅驱动。",
        "观察上涨成分股是否继续扩散，确认不是少数龙头独涨。",
    ]
    if stage in {"高潮期", "退潮期"} or risk_level == "高":
        points.append("重点关注高位分歧和回撤速度，拥挤度继续升高时降低追高权重。")
    else:
        points.append("跟踪下一交易日热度和扩散是否同步改善。")
    if crowding_penalty >= 10:
        points.append("若拥挤扣分继续抬升，注意主升转高潮或退潮。")
    return points


def _previous_totals(
    db: Session,
    theme_ids: list[int],
    current_week_end,
) -> dict[int, float]:
    if not theme_ids:
        return {}
    rows = db.execute(
        select(ThemeScore.theme_id, ThemeScore.overall_score)
        .where(ThemeScore.theme_id.in_(theme_ids), ThemeScore.week_end < current_week_end)
        .order_by(ThemeScore.theme_id, desc(ThemeScore.week_end))
    ).all()
    results: dict[int, float] = {}
    for theme_id, overall_score in rows:
        results.setdefault(theme_id, float(overall_score))
    return results


def get_mainline_radar(db: Session) -> MainlineRadarResponse:
    latest_week = db.scalar(select(func.max(ThemeScore.week_end)))
    if latest_week is None:
        return MainlineRadarResponse(
            generatedAt=datetime.now(),
            marketSummary=MainlineMarketSummary(
                strongestTheme=None,
                potentialCount=0,
                highCrowdingRiskCount=0,
                marketStatus="弱势混沌",
            ),
            themes=[],
        )

    rows = db.execute(
        select(Theme, ThemeScore)
        .join(ThemeScore, ThemeScore.theme_id == Theme.id)
        .where(ThemeScore.week_end == latest_week)
        .order_by(desc(ThemeScore.overall_score), Theme.name)
    ).all()
    previous = _previous_totals(db, [theme.id for theme, _ in rows], latest_week)
    news_text = _load_news_text()
    max_turnover = max(
        (float(score.total_turnover or 0) for _, score in rows),
        default=0,
    ) or 1.0

    diagnoses: list[ThemeDiagnosis] = []
    for theme, score in rows:
        fund = _clamp((float(score.total_turnover or 0) / max_turnover) * 100)
        return_strength = _clamp(float(score.average_return_score))
        breadth = _clamp(float(score.advancing_ratio_score))
        persistence = _clamp(float(score.strength_streak_score))
        catalyst = _catalyst_score(theme.name, news_text)
        crowding_penalty = _crowding_penalty(score, catalyst)
        total = _clamp(
            fund * 0.25
            + return_strength * 0.20
            + breadth * 0.20
            + persistence * 0.15
            + catalyst * 0.10
            - crowding_penalty
        )
        health = _health_level(fund, return_strength, breadth, persistence)
        risk = _risk_level(crowding_penalty, breadth, persistence)
        stage = _stage(total, score, crowding_penalty, previous.get(theme.id))
        status = _status(total, health)
        diagnoses.append(
            ThemeDiagnosis(
                themeId=str(theme.id),
                themeName=theme.name,
                score=MainlineThemeScore(
                    total=_round(total),
                    fund=_round(fund),
                    returnStrength=_round(return_strength),
                    breadth=_round(breadth),
                    persistence=_round(persistence),
                    catalyst=_round(catalyst),
                    crowdingPenalty=_round(crowding_penalty),
                ),
                status=status,
                stage=stage,
                healthLevel=health,
                riskLevel=risk,
                reasons=_reasons(
                    fund=fund,
                    return_strength=return_strength,
                    breadth=breadth,
                    persistence=persistence,
                    catalyst=catalyst,
                    crowding_penalty=crowding_penalty,
                    score=score,
                ),
                watchPoints=_watch_points(stage, risk, crowding_penalty),
            )
        )

    diagnoses.sort(key=lambda item: item.score.total, reverse=True)
    strong_count = sum(1 for item in diagnoses if item.status == "强主线")
    potential_count = sum(1 for item in diagnoses if item.status == "潜在主线")
    high_risk_count = sum(1 for item in diagnoses if item.riskLevel == "高")
    if strong_count >= 1:
        market_status = "主线清晰"
    elif potential_count >= 3:
        market_status = "多线轮动"
    elif high_risk_count >= 5:
        market_status = "退潮观察"
    else:
        market_status = "弱势混沌"

    return MainlineRadarResponse(
        generatedAt=datetime.now(),
        marketSummary=MainlineMarketSummary(
            strongestTheme=diagnoses[0] if diagnoses else None,
            potentialCount=potential_count,
            highCrowdingRiskCount=high_risk_count,
            marketStatus=market_status,
        ),
        themes=diagnoses,
    )
