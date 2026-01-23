from datetime import date

from app.sources.cnb import CnbSource, CNB_CURRENCIES, _parse_response


SAMPLE_CNB_RESPONSE = """20 Jan 2026 #15
Country|Currency|Amount|Code|Rate
Australia|dollar|1|AUD|16,021
Brazil|real|1|BRL|4,065
EMU|euro|1|EUR|25,555
Japan|yen|100|JPY|15,694
USA|dollar|1|USD|24,704
"""


class TestCnbSource:
    def test_source_id(self) -> None:
        source = CnbSource()
        assert source.source_id == "cnb"

    def test_available_symbols(self) -> None:
        source = CnbSource()
        symbols = source.available_symbols()
        assert len(symbols) == len(CNB_CURRENCIES)
        assert "EURCZK" in symbols
        assert "USDCZK" in symbols

    def test_available_symbols_format(self) -> None:
        source = CnbSource()
        symbols = source.available_symbols()
        for sym in symbols:
            # No .CNB suffix anymore
            assert not sym.endswith(".CNB")
            assert sym.endswith("CZK")

    def test_list_symbols(self) -> None:
        source = CnbSource()
        symbols = source.list_symbols()
        assert len(symbols) == len(CNB_CURRENCIES)
        # All should be forex type
        for sym in symbols:
            assert sym.type == "forex"
            assert sym.symbol.endswith("CZK")

    def test_fetch_rate(self) -> None:
        def mock_get(url: str) -> str:
            return SAMPLE_CNB_RESPONSE

        source = CnbSource(http_get=mock_get)
        rate = source.fetch_rate("EURCZK", date(2026, 1, 20))

        assert rate == 25.555

    def test_fetch_rate_not_found(self) -> None:
        def mock_get(url: str) -> str:
            return SAMPLE_CNB_RESPONSE

        source = CnbSource(http_get=mock_get)
        rate = source.fetch_rate("XYZCZK", date(2026, 1, 20))

        assert rate is None

    def test_fetch_history(self) -> None:
        def mock_get(url: str) -> str:
            return SAMPLE_CNB_RESPONSE

        source = CnbSource(http_get=mock_get)
        history = source.fetch_history(["EURCZK", "USDCZK"], days=2)

        assert "EURCZK" in history
        assert "USDCZK" in history
        # Should have entries for the days requested
        assert len(history["EURCZK"]) > 0


class TestParseResponse:
    def test_parses_basic_rates(self) -> None:
        rates = _parse_response(SAMPLE_CNB_RESPONSE)

        assert rates["AUDCZK"] == 16.021
        assert rates["BRLCZK"] == 4.065
        assert rates["EURCZK"] == 25.555
        assert rates["USDCZK"] == 24.704

    def test_handles_quantity_division(self) -> None:
        # JPY uses amount=100, so 15.694 / 100 = 0.15694
        rates = _parse_response(SAMPLE_CNB_RESPONSE)
        assert abs(rates["JPYCZK"] - 0.15694) < 0.0001

    def test_handles_comma_decimal_separator(self) -> None:
        rates = _parse_response(SAMPLE_CNB_RESPONSE)
        assert rates["EURCZK"] == 25.555

    def test_empty_response(self) -> None:
        rates = _parse_response("")
        assert rates == {}

    def test_malformed_lines_skipped(self) -> None:
        text = """20 Jan 2026 #15
Country|Currency|Amount|Code|Rate
Australia|dollar|1|AUD|16,021
bad line
USA|dollar|1|USD|24,704
"""
        rates = _parse_response(text)
        assert len(rates) == 2
        assert "AUDCZK" in rates
        assert "USDCZK" in rates


class TestFetchRatesIntegration:
    def test_constructs_correct_url(self) -> None:
        called_urls: list[str] = []

        def mock_get(url: str) -> str:
            called_urls.append(url)
            return SAMPLE_CNB_RESPONSE

        source = CnbSource(http_get=mock_get)
        source.fetch_rate("EURCZK", date(2026, 1, 20))

        assert len(called_urls) == 1
        assert "date=20.01.2026" in called_urls[0]

    def test_returns_empty_on_error(self) -> None:
        def failing_get(url: str) -> str:
            raise ConnectionError("Network error")

        source = CnbSource(http_get=failing_get)
        rate = source.fetch_rate("EURCZK", date(2026, 1, 20))
        assert rate is None
