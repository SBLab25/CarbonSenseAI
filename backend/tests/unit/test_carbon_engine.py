import pytest
import datetime
from app.services.carbon_engine import (
    calculate_activity_co2,
    calculate_monthly_summary,
    calculate_category_breakdown,
    calculate_trend,
    calculate_progress,
    get_vs_india_average
)
from app.models.schemas import FootprintSummary

def test_car_petrol_20km():
    assert calculate_activity_co2("transport", "car_petrol", 20.0) == pytest.approx(4.2, rel=0.01)

def test_car_diesel_25km():
    assert calculate_activity_co2("transport", "car_diesel", 25.0) == pytest.approx(4.25, rel=0.01)

def test_car_electric_100km():
    assert calculate_activity_co2("transport", "car_electric", 100.0) == pytest.approx(5.0, rel=0.01)

def test_train_100km():
    assert calculate_activity_co2("transport", "train", 100.0) == pytest.approx(4.1, rel=0.01)

def test_flight_domestic_500km():
    assert calculate_activity_co2("transport", "flight_domestic", 500.0) == pytest.approx(127.5, rel=0.01)

def test_electricity_100kwh():
    assert calculate_activity_co2("energy", "electricity", 100.0) == pytest.approx(70.8, rel=0.01)

def test_beef_1kg():
    assert calculate_activity_co2("food", "beef", 1.0) == pytest.approx(27.0, rel=0.01)

def test_vegetables_5kg():
    assert calculate_activity_co2("food", "vegetables", 5.0) == pytest.approx(10.0, rel=0.01)

def test_bicycle_zero_emission():
    assert calculate_activity_co2("transport", "bicycle", 10.0) == pytest.approx(0.0, rel=0.01)

def test_unknown_type_returns_zero():
    assert calculate_activity_co2("transport", "invalid_type", 10.0) == pytest.approx(0.0, rel=0.01)
    assert calculate_activity_co2("invalid_category", "beef", 10.0) == pytest.approx(0.0, rel=0.01)

def test_zero_amount_returns_zero():
    assert calculate_activity_co2("transport", "car_petrol", 0.0) == pytest.approx(0.0, rel=0.01)

def test_negative_amount():
    assert calculate_activity_co2("transport", "car_petrol", -5.0) == pytest.approx(0.0, rel=0.01)

def test_monthly_summary_aggregates_correctly():
    activities = [
        {"category": "transport", "co2_kg": 10.5},
        {"category": "transport", "co2_kg": 5.5},
        {"category": "energy", "co2_kg": 20.0},
        {"category": "food", "co2_kg": 15.0},
        {"category": "shopping", "co2_kg": 30.0},
        {"category": "unknown", "co2_kg": 100.0}  # Should be ignored
    ]
    summary = calculate_monthly_summary(activities, 100.0)
    assert summary.total_kg == pytest.approx(81.0, rel=0.01)
    assert summary.transport_kg == pytest.approx(16.0, rel=0.01)
    assert summary.energy_kg == pytest.approx(20.0, rel=0.01)
    assert summary.food_kg == pytest.approx(15.0, rel=0.01)
    assert summary.shopping_kg == pytest.approx(30.0, rel=0.01)

def test_category_breakdown_percentages_sum_to_100():
    summary = FootprintSummary(total_kg=100.0, transport_kg=25.0, energy_kg=35.0, food_kg=20.0, shopping_kg=20.0)
    breakdown = calculate_category_breakdown(summary)
    assert breakdown["transport"].pct == pytest.approx(25.0, rel=0.01)
    assert breakdown["energy"].pct == pytest.approx(35.0, rel=0.01)
    assert breakdown["food"].pct == pytest.approx(20.0, rel=0.01)
    assert breakdown["shopping"].pct == pytest.approx(20.0, rel=0.01)
    
    total_pct = sum(item.pct for item in breakdown.values())
    assert total_pct == pytest.approx(100.0, rel=0.01)

def test_category_breakdown_zero_total():
    summary = FootprintSummary(total_kg=0.0, transport_kg=0.0, energy_kg=0.0, food_kg=0.0, shopping_kg=0.0)
    breakdown = calculate_category_breakdown(summary)
    for cat, item in breakdown.items():
        assert item.kg == 0.0
        assert item.pct == 0.0

def test_trend_fills_missing_days_with_zero():
    today = datetime.date.today()
    day_minus_1 = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    daily_totals = {day_minus_1: 15.0}
    trends = calculate_trend(daily_totals, 3)
    
    assert len(trends) == 3
    assert trends[0].total_kg == 0.0  # day - 2
    assert trends[1].total_kg == 15.0 # day - 1
    assert trends[2].total_kg == 0.0  # today

def test_progress_calculation_positive_reduction():
    assert calculate_progress(80.0, 100.0) == pytest.approx(20.0, rel=0.01)
    assert calculate_progress(120.0, 100.0) == pytest.approx(-20.0, rel=0.01)
    assert calculate_progress(50.0, 0.0) == pytest.approx(0.0, rel=0.01)

def test_india_average_comparison():
    assert get_vs_india_average(158.0) == pytest.approx(100.0, rel=0.01)
    assert get_vs_india_average(79.0) == pytest.approx(50.0, rel=0.01)
