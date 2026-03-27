import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from modeling.evaluation import (  # noqa: E402
    classification_metrics,
    metric_value,
    primary_metric_higher_is_better,
    primary_metric_name,
    regression_metrics,
)
from modeling.contracts import TaskType  # noqa: E402


class MetricTests(unittest.TestCase):
    def test_regression_metrics(self) -> None:
        y_true = [1.0, -1.0, 2.0, -2.0]
        y_pred = [0.5, -0.5, 1.5, -1.0]
        metrics = regression_metrics(y_true, y_pred)
        self.assertAlmostEqual(metrics.mae, 0.625, places=6)
        self.assertAlmostEqual(metrics.rmse, 0.6614378277661477, places=6)
        self.assertIsNotNone(metrics.r2)
        self.assertAlmostEqual(metrics.directional_accuracy or 0.0, 1.0, places=6)

    def test_classification_metrics(self) -> None:
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 1, 1]
        y_score = [0.1, 0.7, 0.8, 0.9]
        metrics = classification_metrics(y_true, y_pred, y_score)
        self.assertAlmostEqual(metrics.accuracy, 0.75, places=6)
        self.assertAlmostEqual(metrics.precision or 0.0, 2.0 / 3.0, places=6)
        self.assertAlmostEqual(metrics.recall or 0.0, 1.0, places=6)
        self.assertAlmostEqual(metrics.f1 or 0.0, 0.8, places=6)
        self.assertIsNotNone(metrics.roc_auc)

    def test_primary_metric_helpers(self) -> None:
        self.assertEqual(primary_metric_name(TaskType.REGRESSION), "rmse")
        self.assertEqual(primary_metric_name(TaskType.CLASSIFICATION), "f1")
        self.assertFalse(primary_metric_higher_is_better(TaskType.REGRESSION))
        self.assertTrue(primary_metric_higher_is_better(TaskType.CLASSIFICATION))

        reg = regression_metrics([1.0, 2.0], [1.5, 2.5])
        self.assertAlmostEqual(metric_value(reg, "rmse") or 0.0, reg.rmse, places=6)


if __name__ == "__main__":
    unittest.main()
