"""Simulation Lab product domain — re-exports the pro_lab package module.

HTTP paths stay under /api/v1/public/pro-lab for FE compatibility; registered slug is simulation_lab.
"""

from risk_dashboard.modules.pro_lab.module import module

__all__ = ["module"]
