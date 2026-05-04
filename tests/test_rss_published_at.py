"""RSS pubDate parsing: naive datetimes must not be interpreted as server-local UTC."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from risk_dashboard.modules.news_intelligence.application.rss_producer import _published_at


def test_published_at_vn_malformed_gmt_plus_seven_maps_to_ict():
    """Tuổi Trẻ-style pubDate: 'GMT+7' is not RFC-compliant; stdlib drops tz → assume ICT."""
    item = ET.fromstring("<item><pubDate>Mon, 04 May 2026 12:05:08 GMT+7</pubDate></item>")
    iso, _ = _published_at(item, region="VN")
    assert "2026-05-04T05:05:08" in iso


def test_published_at_explicit_offset_unchanged():
    item = ET.fromstring("<item><pubDate>Mon, 04 May 2026 13:57:12 +0700</pubDate></item>")
    iso, _ = _published_at(item, region="VN")
    assert "2026-05-04T06:57:12" in iso
