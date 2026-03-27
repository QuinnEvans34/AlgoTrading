"""Chronological split helpers for ML dataset artifacts."""

from __future__ import annotations

from typing import Sequence

from .contracts import DatasetSplits, MLDatasetRow, SplitPartition, SplitSpec
from .validation import validate_split_spec


def _indices(start: int, end: int) -> tuple[int, ...]:
    return tuple(range(max(0, start), max(0, end)))


def build_chronological_splits(
    rows: Sequence[MLDatasetRow],
    *,
    split_spec: SplitSpec,
) -> DatasetSplits:
    validate_split_spec(split_spec)
    n = len(rows)
    if n == 0:
        raise ValueError("Cannot split an empty dataset")

    train_end = int(n * split_spec.train_fraction)
    validation_end = train_end + int(n * split_spec.validation_fraction)
    if validation_end > n:
        validation_end = n

    gap = split_spec.gap_bars
    validation_start = min(n, train_end + gap)
    validation_end = min(n, validation_end)
    test_start = min(n, validation_end + gap)

    train_indices = _indices(0, train_end)
    validation_indices = _indices(validation_start, validation_end)
    test_indices = _indices(test_start, n)

    first_gap = _indices(train_end, validation_start)
    second_gap = _indices(validation_end, test_start)
    gap_indices = tuple(sorted(set(first_gap + second_gap)))

    if split_spec.train_fraction > 0 and len(train_indices) == 0:
        raise ValueError("Train split resolved to zero rows")
    if split_spec.validation_fraction > 0 and len(validation_indices) == 0:
        raise ValueError("Validation split resolved to zero rows")
    if split_spec.test_fraction > 0 and len(test_indices) == 0:
        raise ValueError("Test split resolved to zero rows")

    overlap = set(train_indices) & set(validation_indices)
    overlap |= set(train_indices) & set(test_indices)
    overlap |= set(validation_indices) & set(test_indices)
    if overlap:
        raise ValueError("Chronological splits overlap, which is invalid")

    return DatasetSplits(
        train=SplitPartition(
            name="train",
            indices=train_indices,
            rows=tuple(rows[i] for i in train_indices),
        ),
        validation=SplitPartition(
            name="validation",
            indices=validation_indices,
            rows=tuple(rows[i] for i in validation_indices),
        ),
        test=SplitPartition(
            name="test",
            indices=test_indices,
            rows=tuple(rows[i] for i in test_indices),
        ),
        dropped_gap_indices=gap_indices,
    )

