import hashlib
import json
from pathlib import Path


def test_tbuis_evidence_manifest_matches_retained_artifacts() -> None:
    repository = Path(__file__).resolve().parents[3]
    evidence = repository / "benchmarks/tbuis/evidence"
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert isinstance(manifest["artifacts"], list)

    listed_paths: set[str] = set()
    requirement_ids: set[str] = set()
    for artifact in manifest["artifacts"]:
        requirement_id = artifact["requirement_id"]
        assert requirement_id not in requirement_ids
        requirement_ids.add(requirement_id)

        for field in ("amp", "state_model"):
            entry = artifact[field]
            relative_path = entry["path"]
            assert relative_path not in listed_paths
            listed_paths.add(relative_path)

            path = evidence / relative_path
            content = path.read_bytes()
            assert len(content) == entry["bytes"]
            assert hashlib.sha256(content).hexdigest() == entry["sha256"]

    retained_paths = {
        path.name
        for path in evidence.iterdir()
        if path.is_file() and path.name != "manifest.json"
    }
    assert listed_paths == retained_paths
