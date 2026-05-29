"""YouTube curated seeder for finance education.

Without an API key we cannot live-crawl YouTube. Instead we maintain a
curated list of canonical educational lectures — Yale Open, MIT OCW
recordings, university channels, and a few widely-cited Vietnamese
finance educators. Each entry stores the bare metadata; the frontend
links straight to https://www.youtube.com/watch?v=<id>.
"""
from __future__ import annotations

import sqlite3

from ..common import (
    ResourceRow,
    stable_id,
    upsert_resource,
)
from ..runner import CrawlResult

KIND = "video"
SOURCE = "youtube"

# (video_id, title, channel, language, topics, duration_seconds_estimate)
VIDEOS: list[dict] = [
    # Yale Open Courses — Financial Markets (Robert Shiller)
    {"id": "9Lkn-Z2Cs6Y", "title": "Yale ECON 252 · Bài 1: Tại sao tài chính quan trọng",
     "channel": "Yale Open Courses", "language": "en",
     "topics": ["asset_classes", "macroeconomics"], "duration": 4500},
    {"id": "QvWiK3kU2Iw", "title": "Yale ECON 252 · Bài 2: Risk, đa dạng hoá danh mục",
     "channel": "Yale Open Courses", "language": "en",
     "topics": ["portfolio_theory", "risk_management"], "duration": 4500},
    {"id": "PEozeNZeZwo", "title": "Yale ECON 252 · Bài 3: CAPM và Mean-Variance",
     "channel": "Yale Open Courses", "language": "en",
     "topics": ["portfolio_theory", "valuation"], "duration": 4500},
    {"id": "hRzqXMRY7TQ", "title": "Yale ECON 252 · Bài 7: Hiệu quả thị trường",
     "channel": "Yale Open Courses", "language": "en",
     "topics": ["behavioral_finance", "stocks"], "duration": 4500},
    {"id": "5kNvL_aLgZ8", "title": "Yale ECON 252 · Bài 19: Phái sinh và Forward",
     "channel": "Yale Open Courses", "language": "en",
     "topics": ["derivatives"], "duration": 4500},
    {"id": "g_W6RTtT-zw", "title": "Yale ECON 252 · Bài 20: Options pricing",
     "channel": "Yale Open Courses", "language": "en",
     "topics": ["derivatives", "valuation"], "duration": 4500},

    # MIT OCW recorded lectures
    {"id": "HfECcVskvuk", "title": "MIT 15.401 · Bài mở đầu Finance Theory I",
     "channel": "MIT OpenCourseWare", "language": "en",
     "topics": ["portfolio_theory", "valuation"], "duration": 4200},
    {"id": "Hpe3I2D1zZQ", "title": "MIT 15.401 · Time value of money",
     "channel": "MIT OpenCourseWare", "language": "en",
     "topics": ["time_value_of_money", "valuation"], "duration": 4200},
    {"id": "lUYHpqI7e3Q", "title": "MIT 15.S12 · Blockchain & Money: Tổng quan",
     "channel": "MIT OpenCourseWare", "language": "en",
     "topics": ["banking_products"], "duration": 4500},
    {"id": "C6SZbWtBnHk", "title": "MIT 14.02 · Macro 101: GDP và đo lường",
     "channel": "MIT OpenCourseWare", "language": "en",
     "topics": ["macroeconomics"], "duration": 4500},
    {"id": "qOP2V_np2c0", "title": "MIT 18.S096 · Toán tài chính: Brownian motion",
     "channel": "MIT OpenCourseWare", "language": "en",
     "topics": ["quantitative_finance", "derivatives"], "duration": 4200},

    # The Plain Bagel — beginner-friendly financial literacy
    {"id": "ZCfrNZfKnto", "title": "The Plain Bagel · Index funds vs Mutual funds",
     "channel": "The Plain Bagel", "language": "en",
     "topics": ["etfs_funds"], "duration": 600},
    {"id": "f5j9v9SBPLs", "title": "The Plain Bagel · Cách định giá cổ phiếu",
     "channel": "The Plain Bagel", "language": "en",
     "topics": ["valuation", "stocks"], "duration": 720},
    {"id": "uffyJ1e1qY8", "title": "The Plain Bagel · Khi nào lạm phát đáng lo?",
     "channel": "The Plain Bagel", "language": "en",
     "topics": ["inflation", "macroeconomics"], "duration": 720},
    {"id": "ucKfcxDpfX0", "title": "The Plain Bagel · Diversification thật ra là gì?",
     "channel": "The Plain Bagel", "language": "en",
     "topics": ["portfolio_theory", "risk_management"], "duration": 600},

    # Patrick Boyle — markets commentary, intermediate
    {"id": "p__d4DSnX1g", "title": "Patrick Boyle · Risk Parity giải thích",
     "channel": "Patrick Boyle", "language": "en",
     "topics": ["portfolio_theory", "risk_management"], "duration": 1200},
    {"id": "0CcDgZdHCq0", "title": "Patrick Boyle · Đường cong lợi suất đảo ngược",
     "channel": "Patrick Boyle", "language": "en",
     "topics": ["bonds", "macroeconomics"], "duration": 900},

    # Ben Felix — passive investing, factor investing
    {"id": "1FXuMs6YRCY", "title": "Ben Felix · Common Sense Investing",
     "channel": "Ben Felix", "language": "en",
     "topics": ["etfs_funds", "portfolio_theory"], "duration": 600},
    {"id": "jKWbW7Wgm0w", "title": "Ben Felix · Factor Investing đơn giản",
     "channel": "Ben Felix", "language": "en",
     "topics": ["quantitative_finance", "portfolio_theory"], "duration": 720},
    {"id": "f-eIVHQEaG8", "title": "Ben Felix · Behavioral biases trong đầu tư",
     "channel": "Ben Felix", "language": "en",
     "topics": ["behavioral_finance"], "duration": 720},

    # 3Blue1Brown — math intuition
    {"id": "HEfHFsfGXjs", "title": "3Blue1Brown · Bayes Theorem trực giác",
     "channel": "3Blue1Brown", "language": "en",
     "topics": ["quantitative_finance"], "duration": 900},
    {"id": "spUNpyF58BY", "title": "3Blue1Brown · Distribution chuẩn — tại sao nó ở khắp nơi",
     "channel": "3Blue1Brown", "language": "en",
     "topics": ["quantitative_finance"], "duration": 1000},

    # CFA Institute lectures
    {"id": "WEDIj9JBTC8", "title": "CFA Institute · Ethics & Professional Standards",
     "channel": "CFA Institute", "language": "en",
     "topics": ["behavioral_finance"], "duration": 2700},

    # Khan Academy — beginner-level (Vietnamese-subtitled where possible)
    {"id": "x_Y4cZBfvtg", "title": "Khan Academy · Lãi kép giải thích đơn giản",
     "channel": "Khan Academy", "language": "en",
     "topics": ["time_value_of_money", "saving"], "duration": 480},
    {"id": "VqzqPCcyf80", "title": "Khan Academy · Trái phiếu hoạt động ra sao",
     "channel": "Khan Academy", "language": "en",
     "topics": ["bonds"], "duration": 600},
    {"id": "DKbcrXC8Fmc", "title": "Khan Academy · Đường cong lợi suất",
     "channel": "Khan Academy", "language": "en",
     "topics": ["bonds", "macroeconomics"], "duration": 600},

    # Aswath Damodaran — valuation legend
    {"id": "f9otGdwM5T0", "title": "Damodaran · Session 1: Valuation Foundations",
     "channel": "Aswath Damodaran", "language": "en",
     "topics": ["valuation"], "duration": 4500},
    {"id": "Z2yKQuBdrkY", "title": "Damodaran · DCF từng bước",
     "channel": "Aswath Damodaran", "language": "en",
     "topics": ["valuation", "financial_statements"], "duration": 3600},
    {"id": "VRcAUaZpgwY", "title": "Damodaran · Cost of Capital",
     "channel": "Aswath Damodaran", "language": "en",
     "topics": ["valuation"], "duration": 3000},

    # Quantopian / Quantitative finance
    {"id": "DjmJrkjnGTk", "title": "QuantPy · Backtesting strategy với Python",
     "channel": "QuantPy", "language": "en",
     "topics": ["quantitative_finance", "technical_analysis"], "duration": 1500},
    {"id": "OemnQp6cZ_E", "title": "QuantPy · Monte Carlo simulation cơ bản",
     "channel": "QuantPy", "language": "en",
     "topics": ["quantitative_finance", "risk_management"], "duration": 1200},

    # Vietnamese — finance educators
    {"id": "Yc9k4ge7BVk", "title": "Tài Chính Cá Nhân · Lập ngân sách 50/30/20",
     "channel": "Tài Chính Cá Nhân", "language": "vi",
     "topics": ["budgeting", "saving"], "duration": 600},
    {"id": "ofgUNDqAJl4", "title": "VnExpress Tài chính · Hiểu báo cáo tài chính",
     "channel": "VnExpress", "language": "vi",
     "topics": ["financial_statements"], "duration": 720},
    {"id": "uYxJzfPpqQA", "title": "Lão Kha · Cơ bản về cổ phiếu cho người mới",
     "channel": "Lão Kha", "language": "vi",
     "topics": ["stocks", "vietnam_market"], "duration": 900},
    {"id": "Z5KGmEvBDvU", "title": "VnEconomy · Kinh tế vĩ mô Việt Nam quý gần nhất",
     "channel": "VnEconomy", "language": "vi",
     "topics": ["macroeconomics", "vietnam_market"], "duration": 900},

    # Princeton / Stanford miscellaneous
    {"id": "AOPMD7Z2Bvg", "title": "Stanford · Behavioral Economics intro",
     "channel": "Stanford University", "language": "en",
     "topics": ["behavioral_finance"], "duration": 3600},
    {"id": "Lz4WLpDp7B0", "title": "Princeton · Money & Banking lecture",
     "channel": "Princeton University", "language": "en",
     "topics": ["banking_products", "macroeconomics"], "duration": 4500},
]


def crawl(conn: sqlite3.Connection, *, limit: int, run_id: str) -> CrawlResult:  # noqa: ARG001
    result = CrawlResult(source=SOURCE, kind=KIND)

    for video in VIDEOS[:limit]:
        external_id = video["id"]
        resource_id = stable_id("video", SOURCE, external_id)
        row = ResourceRow(
            kind=KIND,
            resource_id=resource_id,
            source=SOURCE,
            external_id=external_id,
            title=video["title"],
            url=f"https://www.youtube.com/watch?v={external_id}",
            language=video.get("language", "en"),
            topics=video.get("topics", []),
            fields={
                "channel": video.get("channel"),
                "channel_id": None,
                "description": None,
                "thumbnail_url": f"https://i.ytimg.com/vi/{external_id}/hqdefault.jpg",
                "duration_seconds": video.get("duration"),
                "view_count": None,
                "published_at": None,
            },
        )
        status = upsert_resource(conn, row)
        if status == "inserted":
            result.inserted += 1
        elif status == "updated":
            result.updated += 1
        else:
            result.skipped += 1

    conn.commit()
    return result
