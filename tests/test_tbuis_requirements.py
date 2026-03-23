from reqtrace.ingest.requirements import load_requirement_catalog


def test_load_tbuis_requirements_file() -> None:
    catalog = load_requirement_catalog(
        "suts/tbuis/requirements/use-cases.json")

    assert len(catalog.requirements) == 3
    assert catalog.requirements[0].id == "UC.01"
    assert catalog.requirements[1].id == "UC.02"
    assert catalog.requirements[2].id == "UC.03"
