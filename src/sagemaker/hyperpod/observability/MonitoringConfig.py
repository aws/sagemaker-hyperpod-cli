from typing import Optional
from pydantic import BaseModel


class MonitoringConfig(BaseModel):
    grafanaURL: Optional[str] = None
    prometheusURL: Optional[str] = None
    availableMetrics: Optional[dict] = None

    