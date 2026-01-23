from app.sources.protocol import RateSource


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, RateSource] = {}

    def register(self, source: RateSource) -> None:
        self._sources[source.source_id] = source

    def get(self, source_id: str) -> RateSource | None:
        return self._sources.get(source_id)

    def all(self) -> list[RateSource]:
        return list(self._sources.values())

    def ids(self) -> list[str]:
        return list(self._sources.keys())
