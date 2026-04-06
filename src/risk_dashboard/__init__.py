"""Risk dashboard: data ingestion, quant engine, multi-agent narrative, API."""

import logging
import os

__version__ = "0.1.0"

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
