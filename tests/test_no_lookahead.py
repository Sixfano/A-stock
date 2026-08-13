import pytest
from data.validator import assert_point_in_time

def test_future_data_is_rejected():
    with pytest.raises(ValueError):
        assert_point_in_time("2026-01-02", "2026-01-03 10:00", "2026-01-02 15:00")
