from datetime import date

import pytest

from solver.profiles import EXAMPLE_PROFILE_3_SHIFT
from solver.types import Nurse, SolveRequest


@pytest.fixture
def example_profile():
    return EXAMPLE_PROFILE_3_SHIFT


@pytest.fixture
def make_request(example_profile):
    """Küçük, çözülebilir bir senaryo kurmak için varsayılanlarla bir SolveRequest üretir."""

    def _make(
        nurse_count: int = 6,
        period_days: int = 7,
        default_requirements: dict | None = None,
        **overrides,
    ) -> SolveRequest:
        nurses = tuple(Nurse(id=f"H{i + 1}", is_experienced=(i % 2 == 0)) for i in range(nurse_count))
        requirements = default_requirements or {"07-15": 2, "15-23": 2, "23-07": 1}
        kwargs = dict(
            profile=example_profile,
            nurses=nurses,
            period_start=date(2026, 9, 1),
            period_days=period_days,
            default_requirements=requirements,
            time_limit_seconds=10.0,
        )
        kwargs.update(overrides)
        return SolveRequest(**kwargs)

    return _make
