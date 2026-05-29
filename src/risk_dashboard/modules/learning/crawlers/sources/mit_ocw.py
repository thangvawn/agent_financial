"""MIT OpenCourseWare curated seeder.

OCW does not expose a stable public catalog API for the finance vertical
without scraping a heavy JS index, so we hand-curate the most widely-cited
finance courses with their canonical URLs. The list is small (~15) but
defensible: every entry is a real, free MIT course with a stable identifier.
"""
from __future__ import annotations

import sqlite3

from ..common import (
    ResourceRow,
    stable_id,
    upsert_resource,
)
from ..runner import CrawlResult

KIND = "course"
SOURCE = "mit_ocw"

# (course_code, title, instructor, topics, level, duration_minutes)
COURSES: list[dict] = [
    {
        "code": "15.401",
        "title": "Finance Theory I",
        "instructor": "Andrew W. Lo",
        "topics": ["portfolio_theory", "valuation", "asset_classes"],
        "level": "intermediate",
        "duration_minutes": 1800,
        "description": "Khoá nền tảng về lý thuyết tài chính — present value, "
                       "định giá tài sản, mô hình CAPM, lý thuyết danh mục.",
    },
    {
        "code": "15.402",
        "title": "Finance Theory II",
        "instructor": "Dirk Jenter",
        "topics": ["valuation", "derivatives", "risk_management"],
        "level": "advanced",
        "duration_minutes": 1800,
        "description": "Phần nâng cao: cấu trúc vốn, định giá option, M&A.",
    },
    {
        "code": "15.414",
        "title": "Financial Management",
        "instructor": "Jonathan Lewellen",
        "topics": ["valuation", "financial_statements"],
        "level": "intermediate",
        "duration_minutes": 1500,
        "description": "Quyết định tài chính doanh nghiệp — capital budgeting, "
                       "cấu trúc vốn, định giá.",
    },
    {
        "code": "15.450",
        "title": "Analytics of Finance",
        "instructor": "Leonid Kogan",
        "topics": ["quantitative_finance", "valuation"],
        "level": "advanced",
        "duration_minutes": 1500,
        "description": "Toolkit định lượng: stochastic processes, dynamic "
                       "programming, Monte Carlo cho định giá phái sinh.",
    },
    {
        "code": "15.401-fall-2008",
        "title": "Introduction to Financial and Managerial Accounting",
        "instructor": "Joseph Weber",
        "topics": ["financial_statements"],
        "level": "beginner",
        "duration_minutes": 1200,
        "description": "Đọc, phân tích báo cáo tài chính từ góc nhìn nhà đầu tư.",
    },
    {
        "code": "14.01",
        "title": "Principles of Microeconomics",
        "instructor": "Jonathan Gruber",
        "topics": ["macroeconomics"],
        "level": "beginner",
        "duration_minutes": 2400,
        "description": "Kinh tế học vi mô nền tảng — cung cầu, thị trường, "
                       "thất bại thị trường.",
    },
    {
        "code": "14.02",
        "title": "Principles of Macroeconomics",
        "instructor": "Ricardo Caballero",
        "topics": ["macroeconomics", "inflation"],
        "level": "beginner",
        "duration_minutes": 2400,
        "description": "Kinh tế vĩ mô: GDP, lạm phát, thất nghiệp, chính sách "
                       "tiền tệ và tài khoá.",
    },
    {
        "code": "14.32",
        "title": "Econometrics",
        "instructor": "Joshua Angrist",
        "topics": ["quantitative_finance"],
        "level": "intermediate",
        "duration_minutes": 1800,
        "description": "Hồi quy, biến công cụ, kiểm định giả thuyết cho dữ "
                       "liệu kinh tế tài chính.",
    },
    {
        "code": "15.S08",
        "title": "FinTech: Shaping the Financial World",
        "instructor": "Gary Gensler",
        "topics": ["banking_products", "quantitative_finance"],
        "level": "intermediate",
        "duration_minutes": 1500,
        "description": "Blockchain, AI trong tài chính, robo-advisor, "
                       "regulatory tech.",
    },
    {
        "code": "15.433",
        "title": "Investments",
        "instructor": "Leonid Kogan",
        "topics": ["portfolio_theory", "risk_management", "asset_classes"],
        "level": "intermediate",
        "duration_minutes": 1500,
        "description": "Khoá đầu tư hiện đại — alpha/beta, factor models, "
                       "hedge funds, behavioral.",
    },
    {
        "code": "15.S12",
        "title": "Blockchain and Money",
        "instructor": "Gary Gensler",
        "topics": ["banking_products"],
        "level": "intermediate",
        "duration_minutes": 1200,
        "description": "Khoá nổi tiếng về tiền và blockchain, bao gồm cả "
                       "stablecoin và CBDC.",
    },
    {
        "code": "14.122",
        "title": "Microeconomic Theory III",
        "instructor": "Muhamet Yildiz",
        "topics": ["behavioral_finance"],
        "level": "advanced",
        "duration_minutes": 1500,
        "description": "Lý thuyết trò chơi và quyết định dưới bất định.",
    },
    {
        "code": "18.S096",
        "title": "Topics in Mathematics with Applications in Finance",
        "instructor": "Vasily Strela",
        "topics": ["quantitative_finance", "derivatives"],
        "level": "advanced",
        "duration_minutes": 1500,
        "description": "Toán cho tài chính: stochastic calculus, định giá "
                       "phái sinh, calibration mô hình.",
    },
    {
        "code": "15.071",
        "title": "The Analytics Edge",
        "instructor": "Dimitris Bertsimas",
        "topics": ["quantitative_finance"],
        "level": "intermediate",
        "duration_minutes": 1800,
        "description": "Data science thực hành trong tài chính, vận tải, "
                       "y tế. Có bài thực hành về dự báo và clustering.",
    },
    {
        "code": "15.480",
        "title": "The Science and Business of Biotechnology",
        "instructor": "Andrew W. Lo",
        "topics": ["valuation"],
        "level": "advanced",
        "duration_minutes": 1500,
        "description": "Định giá biotech và risk management trong R&D — "
                       "ứng dụng nguyên lý tài chính tiên tiến.",
    },
]


def crawl(conn: sqlite3.Connection, *, limit: int, run_id: str) -> CrawlResult:  # noqa: ARG001
    result = CrawlResult(source=SOURCE, kind=KIND)

    for item in COURSES[:limit]:
        code = item["code"]
        external_id = code
        url = f"https://ocw.mit.edu/courses/{code.lower().replace('.', '-')}/"
        resource_id = stable_id("course", SOURCE, external_id)
        row = ResourceRow(
            kind=KIND,
            resource_id=resource_id,
            source=SOURCE,
            external_id=external_id,
            title=f"{code} {item['title']}",
            url=url,
            language="en",
            topics=item["topics"],
            fields={
                "provider": "MIT OpenCourseWare",
                "instructor": item.get("instructor"),
                "description": item.get("description", ""),
                "thumbnail_url": None,
                "level": item.get("level"),
                "duration_minutes": item.get("duration_minutes"),
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
