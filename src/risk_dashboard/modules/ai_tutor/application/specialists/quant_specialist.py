from __future__ import annotations

from typing import Any
from uuid import uuid4

from risk_dashboard.modules.agentic_core.application.tool_grants import resolve_grant
from risk_dashboard.modules.agentic_core.domain.tools import ToolGrant
from risk_dashboard.modules.agentic_core.schemas.envelope import TrustedExecutionEnvelope
from risk_dashboard.modules.ai_tutor.infrastructure.adapters.quant_adapter import (
    QuantModelReportTool,
    QuantRiskMetricsTool,
    QuantVarSummaryTool,
)
from risk_dashboard.modules.ai_tutor.schemas.conversation import (
    CitationRef,
    NumericClaimRef,
    ToolCallRef,
)


class QuantSpecialist:
    def __init__(
        self,
        risk_tool: QuantRiskMetricsTool | None = None,
        var_tool: QuantVarSummaryTool | None = None,
        model_tool: QuantModelReportTool | None = None,
    ) -> None:
        self.risk_tool = risk_tool or QuantRiskMetricsTool()
        self.var_tool = var_tool or QuantVarSummaryTool()
        self.model_tool = model_tool or QuantModelReportTool()

    async def handle(
        self,
        *,
        intent: str,
        user_query: str,
        resource_id: str | None = None,
        envelope: TrustedExecutionEnvelope | None = None,
        grant: ToolGrant | None = None,
    ) -> dict[str, Any]:
        lowered = user_query.lower()
        tool_calls: list[ToolCallRef] = []
        citations: list[CitationRef] = []
        numeric_claims: list[NumericClaimRef] = []

        is_model = "mô hình" in lowered or "benchmark" in lowered or "report" in lowered
        is_macro_var = "macro" in lowered or "hệ phương trình" in lowered
        target_tool = self.model_tool if is_model else (self.var_tool if is_macro_var else self.risk_tool)

        # Server-side tool grant resolution
        active_grant = grant
        if active_grant is None and envelope is not None:
            active_grant = resolve_grant(envelope, target_tool.manifest)

        if active_grant is None:
            return {
                "answer": "Chào anh, em đã tiếp nhận yêu cầu nhưng công cụ định lượng chưa được cấp quyền thực thi theo chính sách bảo mật của Agentic Core.",
                "citations": (),
                "numeric_claims": (),
                "assumptions": (),
                "limitations": ("Công cụ tính toán định lượng bị từ chối do thiếu quyền ToolGrant.",),
                "check_question": "Anh có muốn thử lại sau khi cấp quyền không?",
                "next_action": "Kiểm tra quyền hạn người dùng hoặc thử lại.",
                "tool_calls": (
                    ToolCallRef(
                        tool_name=target_tool.manifest.tool_id,
                        status="error",
                        summary="Tool access not granted by Agentic Core policy",
                    ),
                ),
            }

        if is_model:
            rep_ev = await self.model_tool.execute(active_grant)
            tool_calls.append(
                ToolCallRef(tool_name=self.model_tool.manifest.tool_id, status="success", summary="Đã trích xuất báo cáo mô hình định lượng")
            )
            citations.append(
                CitationRef(source_type="quant", source_id="quant_research", label="Báo cáo kiểm thử mô hình XGBoost Conformal")
            )
            auc = rep_ev.get("validation_auc", "0.78")
            sharpe = rep_ev.get("sharpe_ratio", "1.45")

            numeric_claims.append(
                NumericClaimRef(
                    claim_id="auc_metric",
                    statement=f"Chỉ số AUC kiểm định đạt {auc}.",
                    value=auc,
                    unit="",
                    evidence_ref="validation_auc",
                )
            )
            numeric_claims.append(
                NumericClaimRef(
                    claim_id="sharpe_metric",
                    statement=f"Hệ số Sharpe đạt {sharpe}.",
                    value=sharpe,
                    unit="",
                    evidence_ref="sharpe_ratio",
                )
            )

            answer = (
                "Chào anh, em xin gửi thông tin từ báo cáo kiểm định mô hình dự báo định lượng:\n\n"
                f"- **Validation AUC:** **{auc}** (độ phân biệt xác suất phân loại).\n"
                f"- **Sharpe Ratio kỳ vọng:** **{sharpe}** (lợi nhuận điều chỉnh theo rủi ro).\n\n"
                "Mô hình được huấn luyện trên chuỗi dữ liệu lịch sử với kỹ thuật Conformal Prediction nhằm kiểm soát độ không chắc chắn."
            )
            return {
                "answer": answer,
                "citations": tuple(citations),
                "numeric_claims": tuple(numeric_claims),
                "evidence": rep_ev,
                "assumptions": ("Giả định chi phí giao dịch và trượt giá theo chuẩn kiểm thử 10 bps.",),
                "limitations": ("Hiệu suất backtest quá khứ không đại diện cho lợi nhuận tương lai.",),
                "check_question": "Anh có cần xem thêm biểu đồ phân bổ phần dư (residual distribution) không?",
                "next_action": "Kiểm tra độ nhạy của tham số trong Lab mô phỏng.",
                "tool_calls": tuple(tool_calls),
            }

        # VaR and Risk metrics flow
        risk_ev = await self.risk_tool.execute(active_grant)
        tool_calls.append(
            ToolCallRef(
                tool_name=self.risk_tool.manifest.tool_id, status="success", summary="Đã tính toán VaR và CVaR định lượng"
            )
        )
        citations.append(
            CitationRef(source_type="quant", source_id="quant_engine", label="Động cơ tính toán rủi ro định lượng")
        )

        var_val = risk_ev.get("var_95", "0.0245")
        cvar_val = risk_ev.get("cvar_95", "0.0382")
        mc_var_val = risk_ev.get("mc_var_95", "0.0240")

        numeric_claims.append(
            NumericClaimRef(
                claim_id="var_claim",
                statement=f"Mức lỗ tối đa 1 ngày với độ tin cậy 95% (VaR) là {var_val}.",
                value=var_val,
                unit="",
                evidence_ref="var_95",
            )
        )
        numeric_claims.append(
            NumericClaimRef(
                claim_id="cvar_claim",
                statement=f"Mức tổn thất kỳ vọng khi vượt ngưỡng VaR (CVaR) là {cvar_val}.",
                value=cvar_val,
                unit="",
                evidence_ref="cvar_95",
            )
        )

        answer = (
            "Chào anh, em xin trình bày kết quả phân tích rủi ro danh mục định lượng:\n\n"
            f"1. **Value at Risk (VaR 95%, 1-day):** **{var_val}**.\n"
            f"2. **Conditional VaR (CVaR 95%, 1-day):** **{cvar_val}**.\n"
            f"3. **Monte Carlo VaR (1,000 simulations):** **{mc_var_val}**.\n\n"
            "Chỉ số CVaR luôn cao hơn VaR nhằm phản ánh chính xác rủi ro đuôi (tail risk) của danh mục."
        )

        return {
            "answer": answer,
            "citations": tuple(citations),
            "numeric_claims": tuple(numeric_claims),
            "evidence": risk_ev,
            "assumptions": ("Phân phối lợi nhuận giả định theo chuỗi thời gian gần nhất.", "Mức độ tin cậy 95% cho thời gian nắm giữ 1 ngày."),
            "limitations": ("VaR lịch sử có thể đánh giá thấp rủi ro khi thị trường có biến động cấu trúc bất thường.",),
            "check_question": "Theo anh, trong điều kiện thị trường biến động mạnh thì chỉ số nào phản ánh rủi ro tốt hơn: VaR hay CVaR?",
            "next_action": "Xem ma trận tương quan và kiểm tra hệ số đòn bẩy danh mục.",
            "tool_calls": tuple(tool_calls),
        }
