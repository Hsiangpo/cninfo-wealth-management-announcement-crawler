from __future__ import annotations

from types import SimpleNamespace

from cninfo_ssgs.extract_wealth_mgmt import (
    amount_to_yuan,
    amount_to_yuan_with_unit_hint,
    extract_records,
    is_candidate_announcement,
    normalize_date,
)
from cninfo_ssgs.pdf_parser import PdfContent


def test_normalize_date() -> None:
    assert normalize_date("2025年1月2日") == "2025-01-02"
    assert normalize_date("2025/12/31") == "2025-12-31"


def test_amount_to_yuan() -> None:
    assert amount_to_yuan("1亿元") == 100_000_000
    assert amount_to_yuan("2.5万元") == 25_000
    assert amount_to_yuan("100元") == 100


def test_amount_to_yuan_with_unit_hint() -> None:
    # 表头写明“(万元)”，数值列可能只有纯数字
    assert amount_to_yuan_with_unit_hint("4,214", "认购金额（万元）") == 42_140_000


def test_is_candidate_announcement() -> None:
    assert is_candidate_announcement("关于使用闲置募集资金购买理财产品的公告") is True
    assert is_candidate_announcement("关于2026年度委托理财额度预计的公告") is False
    assert is_candidate_announcement("关于董事会决议的公告") is False
    assert is_candidate_announcement("浙商银行股份有限公司关于浙银理财有限责任公司获准开业的公告") is False


def test_fill_purchase_date_fallback() -> None:
    # 回填逻辑在 extract_records 内部，这里只验证 normalize_date 空时的处理方向：
    # normalize_date 不会凭空生成日期，缺失应由上层回填公告日期。
    assert normalize_date("") == ""


def test_purchase_date_forced_to_announcement_date() -> None:
    ann = SimpleNamespace(
        detail_url="https://example.com/detail",
        pdf_url="https://example.com/a.pdf",
        sec_name="测试公司",
        sec_code="600000",
        title="关于购买理财产品的公告",
        announcement_date="2025-12-30",
    )
    pdf = PdfContent(
        text="",
        tables=[
            [
                ["产品类型", "认购金额（万元）", "购买日"],
                ["结构性存款", "4,214", "2025/12/23"],
            ]
        ],
    )

    recs = extract_records(ann, pdf)  # type: ignore[arg-type]
    assert recs
    assert all(r.purchase_date == "2025-12-30" for r in recs)


def test_text_extraction_skips_quota_sentence() -> None:
    ann = SimpleNamespace(
        detail_url="https://example.com/detail",
        pdf_url="https://example.com/a.pdf",
        sec_name="测试公司",
        sec_code="600000",
        title="关于使用闲置自有资金购买理财产品的公告",
        announcement_date="2025-01-28",
    )
    pdf = PdfContent(
        text="公司拟使用最高额度不超过人民币55亿元的闲置自有资金购买理财产品，在额度内资金可以滚动使用。",
        tables=[],
    )
    recs = extract_records(ann, pdf)  # type: ignore[arg-type]
    assert recs == []


def test_text_extraction_skips_registered_capital() -> None:
    ann = SimpleNamespace(
        detail_url="https://example.com/detail",
        pdf_url="https://example.com/a.pdf",
        sec_name="测试公司",
        sec_code="600000",
        title="关于理财子公司获准开业的公告",
        announcement_date="2025-01-26",
    )
    pdf = PdfContent(
        text="浙银理财注册资本为20亿元人民币，业务范围为面向不特定社会公众公开发行理财产品。",
        tables=[],
    )
    recs = extract_records(ann, pdf)  # type: ignore[arg-type]
    assert recs == []
