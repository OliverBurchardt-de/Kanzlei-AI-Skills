from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from merge_parallel_results import consolidate_person_proposals, merge
from prepare_parallel_batches import assign_batches, prepare


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def result_for_batch(batch_input: dict, duplicate_signature: bool) -> dict:
    transactions = []
    mappings = []
    for index, source_id in enumerate(batch_input["allowed_source_ids"], start=1):
        transaction_id = f"{batch_input['id_namespace']['transaction_prefix']}{index:06d}"
        reference = "GLOBAL-DUP" if duplicate_signature and index == 1 else source_id
        partner = "Global Partner" if duplicate_signature and index == 1 else f"Partner {source_id}"
        transactions.append(
            {
                "transaction_id": transaction_id,
                "partner": partner,
                "recognized_date": "2026-08-01",
                "total_amount": "10.00",
                "bookings": [{"document_field_1": reference}],
            }
        )
        mappings.append(
            {
                "transaction_id": transaction_id,
                "source_id": source_id,
                "role": "primary_invoice",
            }
        )
    first_transaction = transactions[0]["transaction_id"]
    return {
        "schema_version": "1.2",
        "batch_id": batch_input["batch_id"],
        "inventory_fingerprint": batch_input["inventory_fingerprint"],
        "transactions": transactions,
        "transaction_sources": mappings,
        "clarification_cases": [],
        "handoffs": [],
        "profile_suggestions": [],
        "accrual_candidates": [],
        "person_account_proposals": [
            {
                "partner": "Neuer Lieferant GmbH",
                "account_type": "creditor",
                "vat_id": "DE123456789",
                "banks": [],
                "transaction_ids": [first_transaction],
            }
        ],
        "batch_notes": [],
    }


def expect_failure(action, needle: str) -> None:
    try:
        action()
    except ValueError as exc:
        if needle not in str(exc):
            raise AssertionError(f"Fehler enthält {needle!r} nicht: {exc}") from exc
    else:
        raise AssertionError(f"Erwarteter Fehler blieb aus: {needle}")


def main() -> None:
    distinct_partners, partner_conflicts = consolidate_person_proposals(
        [
            {
                "partner": "Müller GmbH",
                "account_type": "creditor",
                "banks": [],
                "transaction_ids": ["B001-V000001"],
            },
            {
                "partner": "Möller GmbH",
                "account_type": "creditor",
                "banks": [],
                "transaction_ids": ["B002-V000001"],
            },
        ]
    )
    assert len(distinct_partners) == 2
    assert partner_conflicts == []

    with tempfile.TemporaryDirectory(prefix="bk_parallel_contract_") as temp_name:
        temp = Path(temp_name)
        input_dir = temp / "input"
        work_dir = temp / "work"
        input_dir.mkdir()
        context_file = temp / "context.json"
        write_json(
            context_file,
            {
                "mandant": "12345",
                "target_periods": ["2026-08"],
                "datev_checked_at": "2026-08-19T12:00:00+02:00",
            },
        )
        for index in range(1, 205):
            (input_dir / f"beleg_{index:03d}.pdf").write_bytes(
                b"%PDF-1.4\n" + f"invoice-{index}".encode("ascii")
            )
        (input_dir / "beleg_205.pdf").write_bytes((input_dir / "beleg_001.pdf").read_bytes())
        (input_dir / "SKILL.md").write_text("not an invoice", encoding="utf-8")
        (input_dir / "AGENTS.md").write_text("not an invoice", encoding="utf-8")
        (input_dir / "plugin_bundle.zip").write_bytes(b"not an invoice")
        with zipfile.ZipFile(input_dir / "archive.zip", "w") as archive:
            archive.writestr("package/.codex-plugin/plugin.json", "{}")

        inventory = prepare(
            input_dir,
            work_dir,
            context_file,
            batch_size=100,
        )
        assert len(inventory["source_files"]) == 205
        assert len(inventory["batches"]) == 3
        assert len(inventory["excluded_control_artifacts"]) == 4
        assert len(inventory["duplicate_hash_groups"]) == 1
        duplicate_ids = set(inventory["duplicate_hash_groups"][0]["source_ids"])
        duplicate_batches = {
            source["batch_id"]
            for source in inventory["source_files"]
            if source["source_id"] in duplicate_ids
        }
        assert len(duplicate_batches) == 1
        expect_failure(
            lambda: prepare(input_dir, input_dir / "nested-output", context_file, 100),
            "darf nicht im Eingabeordner liegen",
        )
        synthetic_sources = [
            {
                "source_id": f"S{index:06d}",
                "sha256": f"{index:064x}",
                "size_bytes": 1,
                "estimated_work_units": 1 if index % 10 else 25,
            }
            for index in range(1, 1201)
        ]
        synthetic_batches, _ = assign_batches(synthetic_sources, 100)
        assert len(synthetic_batches) == 12
        assert all(len(batch["source_files"]) == 100 for batch in synthetic_batches)

        grouped_sources = []
        for group_number in range(1, 11):
            grouped_sources.extend(
                {
                    "source_id": f"G{group_number:02d}-{item_number:03d}",
                    "sha256": f"{group_number:064x}",
                    "size_bytes": 1,
                    "estimated_work_units": 1,
                }
                for item_number in range(1, 61)
            )
        grouped_batches, _ = assign_batches(grouped_sources, 100)
        assert len(grouped_batches) == 10
        assert all(len(batch["source_files"]) == 60 for batch in grouped_batches)

        base_run = temp / "base_run.json"
        write_json(
            base_run,
            {
                "run": {"mandantennummer": "12345"},
                "scope": {},
                "_parallel_context_fingerprint": inventory["shared_context_fingerprint"],
            },
        )
        batch_inputs = []
        for batch_number in range(1, 4):
            batch_input = json.loads(
                (work_dir / f"batch_{batch_number:03d}_input.json").read_text(encoding="utf-8")
            )
            batch_inputs.append(batch_input)
            write_json(
                work_dir / f"batch_{batch_number:03d}_result.json",
                result_for_batch(batch_input, duplicate_signature=batch_number <= 2),
            )

        merged = merge(work_dir / "inventory.json", base_run, work_dir)
        assert len(merged["source_files"]) == 205
        assert len(merged["transactions"]) == 205
        assert len(merged["person_account_proposals"]) == 1
        assert merged["_parallel_review"]["global_reconciliation_required"] is True
        assert len(merged["_parallel_review"]["logical_duplicate_candidates"]) == 1
        assert merged["_parallel_review"]["completed_batches"] == ["B001", "B002", "B003"]

        wrong_base_run = temp / "wrong_base_run.json"
        write_json(
            wrong_base_run,
            {
                "run": {"mandantennummer": "99999"},
                "scope": {},
                "_parallel_context_fingerprint": "0" * 64,
            },
        )
        expect_failure(
            lambda: merge(work_dir / "inventory.json", wrong_base_run, work_dir),
            "gehört nicht zum verifizierten Arbeitskontext",
        )

        invalid = result_for_batch(batch_inputs[0], duplicate_signature=False)
        invalid["person_account_proposals"][0]["account"] = "70001"
        write_json(work_dir / "batch_001_result.json", invalid)
        expect_failure(
            lambda: merge(work_dir / "inventory.json", base_run, work_dir),
            "keine neue Kontonummer",
        )

        stale = result_for_batch(batch_inputs[0], duplicate_signature=False)
        stale["inventory_fingerprint"] = "0" * 64
        write_json(work_dir / "batch_001_result.json", stale)
        expect_failure(
            lambda: merge(work_dir / "inventory.json", base_run, work_dir),
            "gehört nicht zur aktuellen Inventur",
        )

        foreign_accrual = result_for_batch(batch_inputs[0], duplicate_signature=False)
        foreign_accrual["accrual_candidates"] = [
            {
                "accrual_id": "B999-A000001",
                "transaction_ids": [foreign_accrual["transactions"][0]["transaction_id"]],
            }
        ]
        write_json(work_dir / "batch_001_result.json", foreign_accrual)
        expect_failure(
            lambda: merge(work_dir / "inventory.json", base_run, work_dir),
            "ungültige Abgrenzungs-ID",
        )

        duplicate_accrual = result_for_batch(batch_inputs[0], duplicate_signature=False)
        first_transaction = duplicate_accrual["transactions"][0]["transaction_id"]
        duplicate_accrual["accrual_candidates"] = [
            {"accrual_id": "B001-A000001", "transaction_ids": [first_transaction]},
            {"accrual_id": "B001-A000001", "transaction_ids": [first_transaction]},
        ]
        write_json(work_dir / "batch_001_result.json", duplicate_accrual)
        expect_failure(
            lambda: merge(work_dir / "inventory.json", base_run, work_dir),
            "doppelte Abgrenzungs-ID",
        )

    print("parallel processing contract: OK")


if __name__ == "__main__":
    main()
