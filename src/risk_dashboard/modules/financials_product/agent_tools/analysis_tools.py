from __future__ import annotations

from risk_dashboard.modules.agentic_core.domain.tools import RiskClass, ToolGrant, ToolManifest
from risk_dashboard.modules.financials_product.agent_tools.helpers import (
    extract_ticker,
    get_line_item_val,
)
from risk_dashboard.modules.financials_product.api.public import (
    _calculated_ratio,
    _formula_by_id,
)
from risk_dashboard.modules.financials_product.domain.formula_registry import get_formula
from risk_dashboard.modules.financials_product.application.report_resolver import ReportResolver
from risk_dashboard.modules.financials_product.schemas.agent_tools import (
    CalculateRatioInput,
    CalculateRatioOutput,
    ComparePeriodsInput,
    ComparePeriodsOutput,
    NumericValue,
    PeriodDelta,
)

COMPARE_PERIODS_MANIFEST = ToolManifest(
    tool_id="bctc.compare_periods",
    name="Compare BCTC Periods",
    module="financials_product",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Compare a line item across multiple reporting periods with absolute and percentage changes.",
    required_capabilities=("bctc:report:read",),
)


class BctcComparePeriodsTool:
    manifest = COMPARE_PERIODS_MANIFEST

    def __init__(self, resolver: ReportResolver | None = None) -> None:
        self.resolver = resolver or ReportResolver()

    def execute(
        self,
        payload: ComparePeriodsInput,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> ComparePeriodsOutput:
        ticker = extract_ticker(payload.report_id)
        report_out = self.resolver.resolve_report(ticker)
        dataset = self.resolver.load_dataset(ticker)

        observations: list[NumericValue] = []
        for period in payload.periods:
            p_data = self.resolver.get_period_data(dataset, period)
            v = get_line_item_val(p_data, payload.line_item)
            prov = self.resolver.make_provenance_ref(report_out, period, line_item=payload.line_item)
            st = "ok" if v is not None else "insufficient_data"
            observations.append(NumericValue(value=v, unit="VND", provenance=prov, calculation_status=st))

        deltas: list[PeriodDelta] = []
        for i in range(len(payload.periods) - 1):
            p_from, p_to = payload.periods[i], payload.periods[i + 1]
            obs_from, obs_to = observations[i], observations[i + 1]
            prov_to = obs_to.provenance

            if obs_from.value is not None and obs_to.value is not None:
                diff = obs_to.value - obs_from.value
                abs_nv = NumericValue(value=diff, unit="VND", provenance=prov_to, calculation_status="ok")
                if obs_from.value != 0:
                    pct = diff / abs(obs_from.value)
                    pct_nv = NumericValue(value=pct, unit="pct", provenance=prov_to, calculation_status="ok")
                else:
                    pct_nv = NumericValue(value=None, unit="pct", provenance=prov_to, calculation_status="insufficient_data")
            else:
                abs_nv = NumericValue(value=None, unit="VND", provenance=prov_to, calculation_status="insufficient_data")
                pct_nv = NumericValue(value=None, unit="pct", provenance=prov_to, calculation_status="insufficient_data")

            deltas.append(PeriodDelta(
                from_period=p_from,
                to_period=p_to,
                absolute=abs_nv,
                pct_change=pct_nv,
                formula_id="period_delta",
                expression="(to_period - from_period) / abs(from_period)",
            ))

        return ComparePeriodsOutput(
            schema_version="1.0.0",
            line_item=payload.line_item,
            observations=tuple(observations),
            deltas=tuple(deltas),
            limitations=(),
        )


CALCULATE_RATIO_MANIFEST = ToolManifest(
    tool_id="bctc.calculate_ratio",
    name="Calculate BCTC Financial Ratio",
    module="financials_product",
    risk_class=RiskClass.READ,
    version="1.0.0",
    description="Calculate an approved financial ratio with full inputs provenance and step calculation.",
    required_capabilities=("bctc:formula:read",),
)


class BctcCalculateRatioTool:
    manifest = CALCULATE_RATIO_MANIFEST

    def __init__(self, resolver: ReportResolver | None = None) -> None:
        self.resolver = resolver or ReportResolver()

    def execute(
        self,
        payload: CalculateRatioInput,
        *,
        grant: ToolGrant | None = None,
        account_id: str = "",
    ) -> CalculateRatioOutput:
        ticker = extract_ticker(payload.report_id)
        report_out = self.resolver.resolve_report(ticker, period=payload.period)
        dataset = self.resolver.load_dataset(ticker)
        period_data = self.resolver.get_period_data(dataset, payload.period)

        try:
            formula_entry = get_formula(payload.formula_id, version=payload.formula_version)
            expression = formula_entry.expression
            unit = formula_entry.unit
            applicability = formula_entry.applicability
            limitations = formula_entry.limitations
            formula_ver = formula_entry.version
        except ValueError:
            formula_info = _formula_by_id(payload.formula_id)
            expression = formula_info.get("expression", payload.formula_id) if formula_info else payload.formula_id
            unit = "ratio"
            applicability = ("income_statement",)
            limitations = ()
            formula_ver = payload.formula_version or "1.0.0"

        num_val: float | None = None
        den_val: float | None = None

        if payload.formula_id == "gross_margin":
            num_val = get_line_item_val(period_data, "gross_profit")
            den_val = get_line_item_val(period_data, "revenue")
        elif payload.formula_id == "operating_margin":
            num_val = get_line_item_val(period_data, "operating_profit")
            den_val = get_line_item_val(period_data, "revenue")
        elif payload.formula_id == "net_margin":
            num_val = get_line_item_val(period_data, "net_profit")
            den_val = get_line_item_val(period_data, "revenue")
        elif payload.formula_id == "gross_profit":
            num_val = get_line_item_val(period_data, "revenue")
            den_val = get_line_item_val(period_data, "cogs")
            calc_diff = (num_val - den_val) if num_val is not None and den_val is not None else None
            calc_status = "ok" if calc_diff is not None else "insufficient_data"
            prov = self.resolver.make_provenance_ref(report_out, payload.period, line_item="gross_profit")
            res_val = NumericValue(value=calc_diff, unit="VND", provenance=prov, calculation_status=calc_status)
            return CalculateRatioOutput(
                schema_version="1.0.0",
                formula_id=payload.formula_id,
                formula_version=formula_ver,
                expression=expression,
                inputs=(),
                result=res_val,
                applicability=applicability,
                limitations=limitations,
            )

        calc_result = _calculated_ratio(num_val, den_val, payload.formula_id, expression)
        prov = self.resolver.make_provenance_ref(report_out, payload.period, line_item=payload.formula_id)
        res_val = NumericValue(
            value=calc_result.get("value"),
            unit=unit,  # type: ignore
            provenance=prov,
            calculation_status=calc_result.get("calculation_status", "ok"),
        )
        return CalculateRatioOutput(
            schema_version="1.0.0",
            formula_id=payload.formula_id,
            formula_version=formula_ver,
            expression=expression,
            inputs=(),
            result=res_val,
            applicability=applicability,
            limitations=limitations,
        )
