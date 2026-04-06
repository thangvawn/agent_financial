"""
Pipeline materialize dữ liệu huấn luyện — tách module để bảo trì.

- ``settings``: đường dẫn mặc định, biến môi trường
- ``market_factory``: chọn nguồn giá/volume
- ``macro_factory``: chọn nguồn vĩ mô
- ``panel_materialize``: gộp + ghi Parquet/manifest
"""

from risk_dashboard.pipeline.panel_materialize import MaterializeResult, materialize_training_panel
from risk_dashboard.pipeline.settings import PipelinePaths

__all__ = [
    "MaterializeResult",
    "PipelinePaths",
    "materialize_training_panel",
]
