import csv

import pytest

from continuum_bench import csv_utils


def _read(path):
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def test_write_dict_rows_uses_ordered_union_of_columns(tmp_path):
    output = tmp_path / "mixed.csv"

    csv_utils.write_dict_rows(
        output,
        [
            {"engine": "jena", "result_count": 1},
            {
                "engine": "rdflib",
                "result_count": 1,
                "result_digest": "",
            },
        ],
        empty_message="empty",
    )

    fieldnames, rows = _read(output)
    assert fieldnames == ["engine", "result_count", "result_digest"]
    assert rows[0]["result_digest"] == ""
    assert {row["engine"] for row in rows} == {"jena", "rdflib"}


def test_write_dict_rows_preserves_previous_file_on_failure(
    tmp_path,
    monkeypatch,
):
    output = tmp_path / "results.csv"
    output.write_text("previous\n", encoding="utf-8")

    class FailingWriter:
        def writeheader(self):
            pass

        def writerows(self, rows):
            raise RuntimeError("simulated writer failure")

    monkeypatch.setattr(
        csv_utils.csv,
        "DictWriter",
        lambda *args, **kwargs: FailingWriter(),
    )

    with pytest.raises(RuntimeError, match="simulated writer failure"):
        csv_utils.write_dict_rows(
            output,
            [{"engine": "jena"}],
            empty_message="empty",
        )

    assert output.read_text(encoding="utf-8") == "previous\n"
    assert list(tmp_path.glob(".results.csv.*.tmp")) == []
