"""
通过官方 API 抓取双色球（SSQ）历史开奖数据，并导出为 Excel / CSV。

接口：
    https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice

注意：
- 已加入较完整的请求头（User-Agent / Referer / Accept 等），降低 403 风险
- 自动翻页，默认最多抓 60 页 * 30 期 = 1800 期
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import time
import random

import requests
import pandas as pd


API_URL = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"

# 尽量模拟正常浏览器 + 页面来源
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.cwl.gov.cn/ygkj/wqkjgg/ssq/",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://www.cwl.gov.cn",
}


@dataclass
class LotteryDraw:
    """单期双色球开奖信息"""

    issue: str            # 期号
    draw_date: str        # 开奖日期
    red_numbers: List[str]
    blue_numbers: List[str]
    sales: str            # 销售金额
    pool_money: str       # 奖池金额
    prize_details: str    # 一等奖/二等奖中奖情况描述
    details_link: str     # 详情链接（如果有）

    @classmethod
    def from_api_payload(cls, payload: Dict[str, Any]) -> "LotteryDraw":
        """
        根据 API 返回的一条记录构造 LotteryDraw。
        不同字段名可能会略有变动，这里做了兼容处理。
        """
        issue = str(payload.get("code", ""))            # 期号
        draw_date = str(payload.get("date", ""))        # 开奖日期

        red_raw = payload.get("red", "") or payload.get("redStr", "")
        blue_raw = payload.get("blue", "") or payload.get("blueStr", "")

        red_numbers = [x.strip() for x in red_raw.split(",") if x.strip()]
        blue_numbers = [x.strip() for x in blue_raw.split(",") if x.strip()]

        sales = str(payload.get("sales", ""))
        pool_money = str(payload.get("poolmoney", ""))

        prize_details = str(payload.get("content", ""))

        details_link = str(payload.get("detailsLink", ""))
        if details_link and not details_link.startswith("http"):
            details_link = "https://www.cwl.gov.cn" + details_link

        return cls(
            issue=issue,
            draw_date=draw_date,
            red_numbers=red_numbers,
            blue_numbers=blue_numbers,
            sales=sales,
            pool_money=pool_money,
            prize_details=prize_details,
            details_link=details_link,
        )


def fetch_draws(issue_count: int = 30, page_no: int = 1) -> List[LotteryDraw]:
    """
    抓取单页历史开奖。

    :param issue_count: 每页条数（官方接口上限一般是 30）
    :param page_no:     页码，从 1 开始
    """
    params = {
        "name": "ssq",
        "issueCount": str(issue_count),
        "issueStart": "",
        "issueEnd": "",
        "dayStart": "",
        "dayEnd": "",
        "pageNo": str(page_no),
    }

    # 随机稍微抖动一下 UA，避免太死板（非必须）
    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] += f" rand/{random.randint(1000,9999)}"

    resp = requests.get(
        API_URL,
        params=params,
        headers=headers,
        timeout=15,
    )

    # 如果直接 403，这里会抛异常
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"❌ 第 {page_no} 页请求失败，HTTP {resp.status_code}")
        # 打印一点点返回体，方便你调试（长度截断）
        print("响应前 200 字符：", resp.text[:200])
        raise e

    payload = resp.json()

    # API 实际返回结构可能是：
    # {
    #   "result": [ ... ],
    #   "list": [ ... ],
    #   "data": [ ... ],
    #   "pageNo": 1,
    #   ...
    # }
    candidates = [
        payload.get("result"),
        payload.get("list"),
        payload.get("data"),
    ]

    records: List[Dict[str, Any]] = []

    for c in candidates:
        if isinstance(c, list):
            records = c
            break
        if isinstance(c, dict):
            if "list" in c and isinstance(c["list"], list):
                records = c["list"]
                break
            if "data" in c and isinstance(c["data"], list):
                records = c["data"]
                break

    if not records:
        # 如果结构变了，这里直接告诉你 payload 长啥样
        print("⚠ 未能从返回值解析出开奖列表，原始 JSON：")
        print(payload)
        raise ValueError("未能从返回值中解析到开奖数据，请检查 API 响应格式。")

    return [LotteryDraw.from_api_payload(item) for item in records]


def fetch_all_draws(max_pages: int = 60, page_size: int = 30) -> List[LotteryDraw]:
    """
    自动翻页抓取历史开奖记录。

    :param max_pages: 最多翻多少页
    :param page_size: 每页多少条（建议 30）
    """
    all_draws: List[LotteryDraw] = []
    seen_issues = set()

    for page_no in range(1, max_pages + 1):
        print(f"正在抓取第 {page_no} 页（每页 {page_size} 条）…")

        page_draws = fetch_draws(issue_count=page_size, page_no=page_no)

        if not page_draws:
            print("本页返回为空，认为已经翻到底，结束。")
            break

        for d in page_draws:
            if d.issue not in seen_issues:
                all_draws.append(d)
                seen_issues.add(d.issue)

        # 如果这一页没满 page_size，说明已经到最后一页了
        if len(page_draws) < page_size:
            print(f"第 {page_no} 页不足 {page_size} 条，已是最后一页，结束。")
            break

        # 随机 sleep 一下，降低被风控的风险
        time.sleep(random.uniform(0.5, 1.5))

    if not all_draws:
        raise ValueError("未能抓取到任何双色球开奖数据，请检查网络或 API 参数。")

    print(f"\n✅ 共抓取到 {len(all_draws)} 期双色球开奖数据。")
    return all_draws


def export_to_excel(draws: List[LotteryDraw], file_path: str = "ssq_history.xlsx") -> None:
    df = pd.DataFrame([asdict(d) for d in draws])
    df.to_excel(file_path, index=False)
    print(f"📁 已保存到 Excel：{file_path}")


def export_to_csv(draws: List[LotteryDraw], file_path: str = "ssq_history.csv") -> None:
    df = pd.DataFrame([asdict(d) for d in draws])
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"📁 已保存到 CSV：{file_path}")


if __name__ == "__main__":
    # 直接一次性请求大量期数
    # 先试 2000，若接口报错，可以改 1000 / 500 再试
    draws = fetch_draws(issue_count=2000, page_no=1)

    print(f"\n✅ 实际抓到期数：{len(draws)} 期\n")

    export_to_excel(draws, "ssq_history.xlsx")
    export_to_csv(draws, "ssq_history.csv")

    print(f"🎉 已保存 {len(draws)} 期双色球数据到 ssq_history.xlsx 和 ssq_history.csv")

