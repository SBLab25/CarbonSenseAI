import pytest
from pydantic import ValidationError
from datetime import datetime
from app.models.schemas import (
    ActivityCreate,
    CarbonSummary,
    CategoryBreakdown,
    AnalysisResult,
    HotspotDetail,
    PlanResult,
    ReductionStrategy,
    UserContext,
    UserProfile,
    FootprintSummary
)

def test_activity_create_valid():
    act = ActivityCreate(
        user_id="user-123",
        category="transport",
        type="car_petrol",
        amount=20.0,
        unit="km",
        notes="Commute to office"
    )
    assert act.category == "transport"
    assert act.amount == 20.0

def test_activity_create_invalid_category():
    with pytest.raises(ValidationError):
        ActivityCreate(
            user_id="user-123",
            category="invalid_category",
            type="car_petrol",
            amount=20.0,
            unit="km"
        )

def test_activity_create_negative_amount():
    act = ActivityCreate(
        user_id="user-123",
        category="transport",
        type="car_petrol",
        amount=-10.0,
        unit="km"
    )
    # Checks that validator converts negative amount to 0.0
    assert act.amount == 0.0

def test_carbon_summary_valid():
    breakdown = {
        "transport": CategoryBreakdown(kg=50.0, pct=50.0),
        "energy": CategoryBreakdown(kg=50.0, pct=50.0)
    }
    summary = CarbonSummary(
        user_id="user-123",
        period="2026-06",
        total_kg=100.0,
        baseline_kg=120.0,
        reduction_pct=16.67,
        breakdown=breakdown,
        vs_india_average_pct=63.3
    )
    assert summary.total_kg == 100.0
    assert summary.breakdown["transport"].pct == 50.0

def test_analysis_result_valid():
    hotspot = HotspotDetail(
        category="transport",
        pct_of_total=45.0,
        vs_baseline_change_pct=12.0,
        key_behaviors=["Drove a lot"],
        reduction_opportunity_kg=15.0
    )
    analysis = AnalysisResult(
        primary_hotspot="transport",
        hotspots=[hotspot],
        behavioral_patterns=["Commuting alone", "Eating meat", "High AC usage", "Excess shopping"], # validator trims to 3
        quick_win_available=True,
        analysis_confidence="high"
    )
    assert analysis.primary_hotspot == "transport"
    assert len(analysis.behavioral_patterns) == 3 # trimmed by validator
    assert analysis.analysis_confidence == "high"

def test_analysis_result_invalid_confidence():
    with pytest.raises(ValidationError):
        AnalysisResult(
            primary_hotspot="transport",
            hotspots=[],
            behavioral_patterns=[],
            quick_win_available=True,
            analysis_confidence="invalid_confidence"
        )

def test_plan_result_valid():
    strategy = ReductionStrategy(
        title="Eco diet",
        action="Eat less beef",
        category="food",
        monthly_saving_kg=15.0,
        difficulty="easy",
        timeframe_days=30
    )
    plan = PlanResult(
        strategies=[strategy],
        total_potential_saving_kg=15.0,
        recommended_goal_pct=12.5,
        thirty_day_focus="Diet"
    )
    assert len(plan.strategies) == 1
    assert plan.recommended_goal_pct == 12.5

def test_user_context_valid():
    profile = UserProfile(
        id="user-123",
        name="Test",
        weekly_transport_km=10.0,
        monthly_electricity_kwh=10.0,
        baseline_footprint_kg=100.0,
        monthly_target_reduction_pct=15.0,
        eco_points=10,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    baseline = FootprintSummary(total_kg=100.0, transport_kg=20.0, energy_kg=30.0, food_kg=30.0, shopping_kg=20.0)
    current = FootprintSummary(total_kg=90.0, transport_kg=15.0, energy_kg=25.0, food_kg=30.0, shopping_kg=20.0)
    
    ctx = UserContext(
        user_id="user-123",
        profile=profile,
        baseline_footprint=baseline,
        current_footprint=current,
        recent_activities=[],
        active_goal=None,
        progress_pct=10.0
    )
    assert ctx.user_id == "user-123"
    assert ctx.progress_pct == 10.0
