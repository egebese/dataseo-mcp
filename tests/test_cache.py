from pathlib import Path

from seo_mcp.cache import SignatureCache, iso_to_timestamp


def test_signature_cache_saves_and_loads_valid_record(tmp_path: Path) -> None:
    cache = SignatureCache(tmp_path)

    assert cache.save("example.com", "sig", "2099-01-01T00:00:00Z", {"dr": 42})

    record = cache.load("example.com")
    assert record is not None
    assert record.signature == "sig"
    assert record.overview_data == {"dr": 42}


def test_signature_cache_ignores_expired_record(tmp_path: Path) -> None:
    cache = SignatureCache(tmp_path)
    cache.save("example.com", "sig", "2000-01-01T00:00:00Z", {"dr": 42})

    assert cache.load("example.com") is None


def test_signature_cache_ignores_corrupt_json(tmp_path: Path) -> None:
    cache = SignatureCache(tmp_path)
    cache.cache_dir.mkdir(parents=True, exist_ok=True)
    cache.path.write_text("{not-json", encoding="utf-8")

    assert cache.load("example.com") is None


def test_iso_to_timestamp_handles_zulu_time() -> None:
    assert iso_to_timestamp("2099-01-01T00:00:00Z") > 0
