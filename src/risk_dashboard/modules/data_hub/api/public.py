from __future__ import annotations

from fastapi import APIRouter, HTTPException

from risk_dashboard.modules.data_hub.application.services import DataHubService

router = APIRouter(prefix="/data-hub", tags=["DataHub"])


@router.get("/topics")
def list_data_hub_topics() -> dict:
    return DataHubService().list_topic_status()


@router.get("/topics/{topic:path}")
def get_data_hub_topic(topic: str) -> dict:
    snapshot = DataHubService().get_topic(topic)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Unknown data hub topic.")
    return snapshot.to_dict()


@router.get("/global-terminal")
def get_global_terminal(view: str = "dashboard") -> dict:
    return DataHubService().get_global_terminal(view=view)


@router.get("/instruments/{symbol}/history")
def get_instrument_history(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
) -> dict:
    return DataHubService().get_instrument_history(symbol=symbol, period=period, interval=interval)
