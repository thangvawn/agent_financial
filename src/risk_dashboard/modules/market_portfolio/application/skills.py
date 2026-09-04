from __future__ import annotations

from dataclasses import dataclass



@dataclass(frozen=True)
class AgentSkillDefinition:
    skill_id: str
    version: str = "1.0.0"
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    allowed_tools: tuple[str, ...] = ()


MARKET_CONTEXT_EXPLAINER_SKILL = AgentSkillDefinition(
    skill_id="market.context_explainer.v1",
    name="Market Context Explainer",
    description="Explains current VN market conditions, indices, and quotes with strict factual grounding.",
    system_prompt=(
        "You are an educational financial market analyst specializing in the Vietnam stock market.\n"
        "Explain the provided market snapshot facts clearly.\n"
        "State data source and timestamp explicitly.\n"
        "Do NOT provide financial advice, buy/sell targets, or price predictions."
    ),
    allowed_tools=("market.get_snapshot.v1",),
)

PORTFOLIO_EXPOSURE_REVIEW_SKILL = AgentSkillDefinition(
    skill_id="portfolio.exposure_review.v1",
    name="Portfolio Exposure Reviewer",
    description="Analyzes paper portfolio asset allocation, position weights, top 3 concentration, and HHI.",
    system_prompt=(
        "You are a quantitative portfolio risk tutor for educational paper trading accounts.\n"
        "Review the calculated asset allocation, concentration, and HHI index.\n"
        "Cite exact weights from the deterministic calculations.\n"
        "Remind the user this is a paper portfolio and never suggest rebalancing or stock trades."
    ),
    allowed_tools=("portfolio.get_snapshot.v1", "portfolio.get_exposure.v1"),
)

PORTFOLIO_SCENARIO_WALKTHROUGH_SKILL = AgentSkillDefinition(
    skill_id="portfolio.scenario_walkthrough.v1",
    name="Portfolio Scenario Walkthrough",
    description="Explains simulated price shock scenarios and deterministic equity delta revaluations.",
    system_prompt=(
        "You are a stress-testing tutor for simulated paper portfolios.\n"
        "Walk through the deterministic price shocks and their impact on portfolio equity and positions.\n"
        "Explain the assumptions and limitations of linear mark-price revaluation.\n"
        "Do NOT suggest protective hedging trades or real market timing."
    ),
    allowed_tools=("portfolio.get_snapshot.v1", "portfolio.run_scenario.v1"),
)

PORTFOLIO_PAPER_FILL_EXPLAINER_SKILL = AgentSkillDefinition(
    skill_id="portfolio.paper_fill_explainer.v1",
    name="Paper Order Fill Explainer",
    description="Factual breakdown of a simulated paper execution fill, execution prices, and slippage.",
    system_prompt=(
        "You are an educational trade mechanics explainer.\n"
        "Explain the factual details of the paper order fill, comparing limit vs filled prices.\n"
        "State clearly that fills occurred in a paper simulated environment without broker execution."
    ),
    allowed_tools=("portfolio.explain_fill.v1",),
)

ALL_SKILLS: dict[str, AgentSkillDefinition] = {
    MARKET_CONTEXT_EXPLAINER_SKILL.skill_id: MARKET_CONTEXT_EXPLAINER_SKILL,
    PORTFOLIO_EXPOSURE_REVIEW_SKILL.skill_id: PORTFOLIO_EXPOSURE_REVIEW_SKILL,
    PORTFOLIO_SCENARIO_WALKTHROUGH_SKILL.skill_id: PORTFOLIO_SCENARIO_WALKTHROUGH_SKILL,
    PORTFOLIO_PAPER_FILL_EXPLAINER_SKILL.skill_id: PORTFOLIO_PAPER_FILL_EXPLAINER_SKILL,
}


