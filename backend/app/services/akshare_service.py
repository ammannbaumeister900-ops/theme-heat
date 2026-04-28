from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from io import StringIO

import akshare as ak
import pandas as pd
import requests
from bs4 import BeautifulSoup
from py_mini_racer import py_mini_racer

from akshare.stock_feature.stock_board_concept_ths import _get_file_content_ths as get_concept_file_content_ths
from akshare.stock_feature.stock_board_industry_ths import _get_file_content_ths as get_industry_file_content_ths


logger = logging.getLogger(__name__)


class AKShareService:
    THEME_SOURCES_EM = {
        "industry": {
            "list": ak.stock_board_industry_name_em,
            "constituents": ak.stock_board_industry_cons_em,
        },
        "concept": {
            "list": ak.stock_board_concept_name_em,
            "constituents": ak.stock_board_concept_cons_em,
        },
    }
    THEME_SOURCES_THS = {
        "industry": {
            "list": ak.stock_board_industry_name_ths,
            "detail_prefix": "https://q.10jqka.com.cn/thshy/detail/code",
            "file_loader": get_industry_file_content_ths,
            "sample_url": "https://q.10jqka.com.cn/thshy/detail/code/881272/",
        },
        "concept": {
            "list": ak.stock_board_concept_name_ths,
            "detail_prefix": "https://q.10jqka.com.cn/gn/detail/code",
            "file_loader": get_concept_file_content_ths,
            "sample_url": "https://q.10jqka.com.cn/gn/detail/code/307822/",
        },
    }

    def __init__(self) -> None:
        self.request_timeout = 20
        self.max_retries = 3
        self.backoff_seconds = 1.5
        self.max_ths_pages = 5
        self._ths_cookie_value: str | None = None

    @staticmethod
    def normalize_symbol(value: str) -> str:
        text = str(value).strip()
        if "." in text:
            return text
        return text.zfill(6)

    def fetch_theme_list(self, theme_type: str) -> list[dict]:
        records = self._fetch_theme_list_from_em(theme_type)
        if records:
            return records
        logger.warning("falling back to Tonghuashun theme list for %s", theme_type)
        return self._fetch_theme_list_from_ths(theme_type)

    def fetch_theme_stocks(self, theme_type: str, theme_name: str, theme_code: str | None = None) -> list[dict]:
        records = self._fetch_theme_stocks_from_em(theme_type, theme_name)
        if records:
            return records
        logger.warning("falling back to Tonghuashun constituents for %s/%s", theme_type, theme_name)
        return self._fetch_theme_stocks_from_ths(theme_type, theme_name, theme_code)

    def fetch_stock_quotes(self, symbol: str, start_date: date, end_date: date) -> list[dict]:
        start = start_date.strftime("%Y%m%d")
        end = end_date.strftime("%Y%m%d")
        df = self._retry_call(
            lambda: ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq",
            ),
            operation=f"quote-em:{symbol}",
        )
        if df is not None:
            return self._normalize_em_quote_records(df)

        tx_symbol = self._to_market_symbol(symbol)
        df = self._retry_call(
            lambda: ak.stock_zh_a_hist_tx(
                symbol=tx_symbol,
                start_date=start,
                end_date=end,
                adjust="qfq",
                timeout=self.request_timeout,
            ),
            operation=f"quote-tx:{tx_symbol}",
        )
        if df is None:
            return []
        return self._normalize_tx_quote_records(df)

    def fetch_market_news(self, limit: int = 8) -> list[dict]:
        records = self._fetch_market_news_from_em(limit)
        if records:
            return records
        records = self._fetch_market_news_from_cls(limit)
        if records:
            return records
        return self._fetch_market_news_from_sina(limit)

    def _fetch_market_news_from_em(self, limit: int) -> list[dict]:
        df = self._retry_call(ak.stock_info_global_em, operation="market-news-em")
        if df is None or df.empty:
            return []
        records: list[dict] = []
        for _, row in df.head(limit).iterrows():
            title = str(row.get("标题") or "").strip()
            if not title:
                continue
            records.append(
                {
                    "title": title,
                    "summary": str(row.get("摘要") or "").strip() or None,
                    "published_at": str(row.get("发布时间") or "").strip() or None,
                    "source": "东方财富",
                    "url": str(row.get("链接") or "").strip() or None,
                }
            )
        return records

    def _fetch_market_news_from_cls(self, limit: int) -> list[dict]:
        df = self._retry_call(ak.stock_info_global_cls, operation="market-news-cls")
        if df is None or df.empty:
            return []
        records: list[dict] = []
        for _, row in df.head(limit).iterrows():
            title = str(row.get("标题") or "").strip()
            content = str(row.get("内容") or "").strip()
            records.append(
                {
                    "title": title or content[:48],
                    "summary": content or None,
                    "published_at": f"{row.get('发布日期') or ''} {row.get('发布时间') or ''}".strip() or None,
                    "source": "财联社",
                    "url": None,
                }
            )
        return [item for item in records if item["title"]]

    def _fetch_market_news_from_sina(self, limit: int) -> list[dict]:
        df = self._retry_call(ak.stock_info_global_sina, operation="market-news-sina")
        if df is None or df.empty:
            return []
        records: list[dict] = []
        for _, row in df.head(limit).iterrows():
            content = str(row.get("内容") or "").strip()
            if not content:
                continue
            records.append(
                {
                    "title": content[:48],
                    "summary": content,
                    "published_at": str(row.get("时间") or "").strip() or None,
                    "source": "新浪财经",
                    "url": None,
                }
            )
        return records

    def _normalize_em_quote_records(self, df: pd.DataFrame) -> list[dict]:
        records: list[dict] = []
        for _, row in df.iterrows():
            trade_date = pd.to_datetime(row["日期"]).date()
            turnover = row.get("成交额", 0) or 0
            records.append(
                {
                    "trade_date": trade_date,
                    "close_price": float(row.get("收盘", 0) or 0),
                    "pct_change": float(row.get("涨跌幅", 0) or 0),
                    "turnover_amount": float(turnover),
                }
            )
        return records

    def _normalize_tx_quote_records(self, df: pd.DataFrame) -> list[dict]:
        records: list[dict] = []
        previous_close: float | None = None
        for _, row in df.iterrows():
            close_price = float(row.get("close", 0) or 0)
            pct_change = 0.0
            if previous_close not in (None, 0):
                pct_change = ((close_price - previous_close) / previous_close) * 100
            records.append(
                {
                    "trade_date": pd.to_datetime(row["date"]).date(),
                    "close_price": close_price,
                    "pct_change": pct_change,
                    "turnover_amount": float(row.get("amount", 0) or 0),
                }
            )
            previous_close = close_price
        return records

    @staticmethod
    def _to_market_symbol(symbol: str) -> str:
        normalized = symbol.zfill(6)
        if normalized.startswith(("5", "6", "9")):
            return f"sh{normalized}"
        if normalized.startswith(("4", "8")):
            return f"bj{normalized}"
        return f"sz{normalized}"

    def get_quote_window(self, weeks: int = 8) -> tuple[date, date]:
        end_date = date.today()
        start_date = end_date - timedelta(days=7 * weeks)
        return start_date, end_date

    def is_trading_day(self, target_date: date) -> bool:
        if target_date.weekday() >= 5:
            return False

        df = self._retry_call(ak.tool_trade_date_hist_sina, operation="trade-calendar-sina")
        if df is None or df.empty:
            logger.warning("trade calendar unavailable; falling back to weekday for %s", target_date)
            return True

        for column in df.columns:
            parsed_dates = pd.to_datetime(df[column], errors="coerce").dt.date
            if target_date in set(parsed_dates.dropna()):
                return True
        return False

    def _retry_call(self, func, operation: str):
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return func()
            except Exception as exc:
                last_error = exc
                logger.warning("%s failed on attempt %s/%s: %s", operation, attempt, self.max_retries, exc)
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * attempt)
        logger.warning("%s exhausted retries: %s", operation, last_error)
        return None

    def _fetch_theme_list_from_em(self, theme_type: str) -> list[dict]:
        source = self.THEME_SOURCES_EM[theme_type]
        df = self._retry_call(source["list"], operation=f"{theme_type}-theme-list-em")
        if df is None:
            return []
        records: list[dict] = []
        for _, row in df.iterrows():
            records.append(
                {
                    "name": row.get("板块名称") or row.get("名称"),
                    "code": str(row.get("板块代码") or row.get("代码") or ""),
                    "theme_type": theme_type,
                    "source": "akshare-em",
                }
            )
        return [item for item in records if item["name"]]

    def _fetch_theme_list_from_ths(self, theme_type: str) -> list[dict]:
        source = self.THEME_SOURCES_THS[theme_type]
        records = self._retry_call(
            lambda: self._fetch_theme_list_from_ths_page(theme_type),
            operation=f"{theme_type}-theme-list-ths-page",
        )
        if records:
            return records

        df = self._retry_call(source["list"], operation=f"{theme_type}-theme-list-ths")
        if df is None:
            return []
        records: list[dict] = []
        for _, row in df.iterrows():
            records.append(
                {
                    "name": row.get("name") or row.get("名称"),
                    "code": str(row.get("code") or row.get("代码") or ""),
                    "theme_type": theme_type,
                    "source": "akshare-ths",
                }
            )
        return [item for item in records if item["name"]]

    def _fetch_theme_list_from_ths_page(self, theme_type: str) -> list[dict]:
        source = self.THEME_SOURCES_THS[theme_type]
        cookie_value = self._get_ths_cookie(source["file_loader"])
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Cookie": f"v={cookie_value}",
            "Referer": source["sample_url"],
        }
        response = requests.get(source["sample_url"], headers=headers, timeout=self.request_timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, features="lxml")
        container = soup.find(name="div", attrs={"class": "cate_inner"})
        if container is None:
            raise ValueError(f"cate_inner not found for {theme_type}")

        records: list[dict] = []
        for link in container.find_all("a"):
            href = link.get("href", "")
            parts = [part for part in href.split("/") if part]
            if len(parts) < 2:
                continue
            records.append(
                {
                    "name": link.get_text(strip=True),
                    "code": parts[-1] if parts[-1].isdigit() else parts[-2],
                    "theme_type": theme_type,
                    "source": "akshare-ths",
                }
            )
        return [item for item in records if item["name"]]

    def _fetch_theme_stocks_from_em(self, theme_type: str, theme_name: str) -> list[dict]:
        source = self.THEME_SOURCES_EM[theme_type]
        df = self._retry_call(
            lambda: source["constituents"](symbol=theme_name),
            operation=f"{theme_type}-theme-cons-em:{theme_name}",
        )
        if df is None:
            return []
        records: list[dict] = []
        for _, row in df.iterrows():
            symbol = row.get("代码") or row.get("股票代码") or row.get("证券代码")
            name = row.get("名称") or row.get("股票名称") or row.get("证券简称")
            if not symbol or not name:
                continue
            records.append(
                {
                    "symbol": self.normalize_symbol(str(symbol)),
                    "name": str(name),
                    "close_price": self._safe_float(row.get("最新价")),
                    "pct_change": self._safe_float(row.get("涨跌幅")),
                    "turnover_amount": self._safe_float(row.get("成交额")),
                }
            )
        return records

    def _fetch_theme_stocks_from_ths(self, theme_type: str, theme_name: str, theme_code: str | None = None) -> list[dict]:
        source = self.THEME_SOURCES_THS[theme_type]
        board_code = theme_code or self._resolve_ths_board_code(theme_type, theme_name)
        if not board_code:
            return []

        cookie_value = self._get_ths_cookie(source["file_loader"])
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Cookie": f"v={cookie_value}",
            "Referer": f"{source['detail_prefix']}/{board_code}/",
        }

        first_url = f"{source['detail_prefix']}/{board_code}/"
        first_response = self._retry_call(
            lambda: requests.get(first_url, headers=headers, timeout=self.request_timeout),
            operation=f"{theme_type}-theme-cons-ths:{theme_name}:page1",
        )
        if first_response is None or first_response.status_code != 200:
            return []

        page_total = min(self._extract_page_total(first_response.text), self.max_ths_pages)
        frames = [self._parse_ths_constituent_table(first_response.text)]

        for page in range(2, page_total + 1):
            page_url = f"{source['detail_prefix']}/{board_code}/page/{page}/ajax/1/"
            response = self._retry_call(
                lambda url=page_url: requests.get(url, headers=headers, timeout=self.request_timeout),
                operation=f"{theme_type}-theme-cons-ths:{theme_name}:page{page}",
            )
            if response is None or response.status_code != 200:
                continue
            if self._is_ths_login_redirect(response.text):
                logger.warning(
                    "Tonghuashun blocked pagination for %s/%s on page %s; using partial constituent list",
                    theme_type,
                    theme_name,
                    page,
                )
                break
            frame = self._parse_ths_constituent_table(response.text)
            if frame.empty:
                logger.warning(
                    "Tonghuashun returned no table for %s/%s on page %s; using partial constituent list",
                    theme_type,
                    theme_name,
                    page,
                )
                break
            frames.append(frame)
            time.sleep(0.5)

        if not frames:
            return []

        df = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True).drop_duplicates(subset=["代码"])
        records: list[dict] = []
        for _, row in df.iterrows():
            symbol = row.get("代码")
            name = row.get("名称")
            if pd.isna(symbol) or pd.isna(name):
                continue
            records.append(
                {
                    "symbol": self.normalize_symbol(str(symbol)),
                    "name": str(name),
                    "close_price": self._safe_float(row.get("现价")),
                    "pct_change": self._safe_float(row.get("涨跌幅(%)")),
                    "turnover_amount": self._parse_amount_value(row.get("成交额")),
                }
            )
        return records

    def _resolve_ths_board_code(self, theme_type: str, theme_name: str) -> str | None:
        for item in self._fetch_theme_list_from_ths(theme_type):
            if item["name"] == theme_name:
                return item["code"]
        return None

    def _get_ths_cookie(self, file_loader) -> str:
        if self._ths_cookie_value:
            return self._ths_cookie_value
        js_code = py_mini_racer.MiniRacer()
        js_code.eval(file_loader("ths.js"))
        self._ths_cookie_value = js_code.call("v")
        return self._ths_cookie_value

    @staticmethod
    def _extract_page_total(html: str) -> int:
        soup = BeautifulSoup(html, features="lxml")
        page_info = soup.find("span", attrs={"class": "page_info"})
        if page_info is None:
            return 1
        text = page_info.get_text(strip=True)
        if "/" not in text:
            return 1
        try:
            return max(int(text.split("/")[-1]), 1)
        except ValueError:
            return 1

    @staticmethod
    def _parse_ths_constituent_table(html: str) -> pd.DataFrame:
        try:
            tables = pd.read_html(StringIO(html))
        except ValueError:
            return pd.DataFrame(columns=["代码", "名称"])
        if not tables:
            return pd.DataFrame(columns=["代码", "名称"])
        return tables[0]

    @staticmethod
    def _is_ths_login_redirect(html: str) -> bool:
        return "upass.10jqka.com.cn/login" in html

    @staticmethod
    def _safe_float(value) -> float | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        text = str(value).strip().replace("%", "").replace(",", "")
        if not text or text == "--":
            return None
        try:
            return float(text)
        except ValueError:
            return None

    @classmethod
    def _parse_amount_value(cls, value) -> float | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        text = str(value).strip().replace(",", "")
        if not text or text == "--":
            return None
        multiplier = 1.0
        if text.endswith("亿"):
            multiplier = 100000000.0
            text = text[:-1]
        elif text.endswith("万"):
            multiplier = 10000.0
            text = text[:-1]
        try:
            return float(text) * multiplier
        except ValueError:
            return cls._safe_float(value)
