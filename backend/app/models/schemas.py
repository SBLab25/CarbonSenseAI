from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class GeminiError(Exception):
    def __init__(self, user_message: str, log_detail: str = ""):
        super().__init__(user_message)
        self.user_message = user_message
        self.log_detail = log_detail

class UserCreate(BaseModel):
    id: Optional[str] = None
    name: str
    country: Optional[str] = None
    city: Optional[str] = None
    lifestyle_type: Optional[str] = None  # Urban / Suburban / Rural
    diet_type: Optional[str] = None       # Vegan / Vegetarian / Mixed / High Meat
    primary_transport: Optional[str] = None
    weekly_transport_km: float = 0.0
    monthly_electricity_kwh: float = 0.0
    heating_type: Optional[str] = None
    monthly_target_reduction_pct: float = 15.0

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserProfile(BaseModel):
    id: str
    name: str
    country: Optional[str] = None
    city: Optional[str] = None
    lifestyle_type: Optional[str] = None
    diet_type: Optional[str] = None
    primary_transport: Optional[str] = None
    weekly_transport_km: float = 0.0
    monthly_electricity_kwh: float = 0.0
    heating_type: Optional[str] = None
    baseline_footprint_kg: float = 0.0
    monthly_target_reduction_pct: float = 15.0
    eco_points: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ActivityCreate(BaseModel):
    user_id: str
    category: str
    type: str
    amount: float
    unit: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = ["transport", "energy", "food", "shopping"]
        val = v.lower().strip()
        if val not in allowed:
            raise ValueError(f"Category must be one of {allowed}")
        return val

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v < 0:
            return 0.0
        return v

class ActivityResponse(BaseModel):
    activity_id: int
    user_id: str
    category: str
    type: str
    amount: float
    unit: str
    co2_kg: float
    source: str
    notes: Optional[str] = None
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NLActivityRequest(BaseModel):
    user_id: str
    description: str

    model_config = ConfigDict(from_attributes=True)

class NLParseResponse(BaseModel):
    parsed: Dict[str, Any]
    activity_id: int
    co2_kg: float

    model_config = ConfigDict(from_attributes=True)

class CategoryBreakdown(BaseModel):
    kg: float
    pct: float

    model_config = ConfigDict(from_attributes=True)

class CarbonSummary(BaseModel):
    user_id: str
    period: str
    total_kg: float
    baseline_kg: float
    reduction_pct: float
    breakdown: Dict[str, CategoryBreakdown]
    vs_india_average_pct: float

    model_config = ConfigDict(from_attributes=True)

class CarbonTrend(BaseModel):
    date: str
    total_kg: float

    model_config = ConfigDict(from_attributes=True)

class ProgressReport(BaseModel):
    user_id: str
    baseline_kg: float
    current_kg: float
    reduction_pct: float

    model_config = ConfigDict(from_attributes=True)

class FootprintSummary(BaseModel):
    total_kg: float
    transport_kg: float
    energy_kg: float
    food_kg: float
    shopping_kg: float

    model_config = ConfigDict(from_attributes=True)

class HotspotDetail(BaseModel):
    category: str
    pct_of_total: float
    vs_baseline_change_pct: float
    key_behaviors: List[str]
    reduction_opportunity_kg: float

    model_config = ConfigDict(from_attributes=True)

class AnalysisResult(BaseModel):
    primary_hotspot: str
    hotspots: List[HotspotDetail]
    behavioral_patterns: List[str]
    quick_win_available: bool
    analysis_confidence: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("behavioral_patterns")
    @classmethod
    def validate_behavioral_patterns(cls, v: List[str]) -> List[str]:
        if len(v) > 3:
            return v[:3]
        return v

    @field_validator("analysis_confidence")
    @classmethod
    def validate_confidence(cls, v: str) -> str:
        allowed = ["high", "medium", "low"]
        val = v.lower().strip()
        if val not in allowed:
            raise ValueError(f"analysis_confidence must be one of {allowed}")
        return val

class ReductionStrategy(BaseModel):
    title: str
    action: str
    category: str
    monthly_saving_kg: float
    difficulty: str
    timeframe_days: int
    mission_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PlanResult(BaseModel):
    strategies: List[ReductionStrategy]
    total_potential_saving_kg: float
    recommended_goal_pct: float
    thirty_day_focus: str

    model_config = ConfigDict(from_attributes=True)

class UserContext(BaseModel):
    user_id: str
    profile: UserProfile
    baseline_footprint: FootprintSummary
    current_footprint: FootprintSummary
    recent_activities: List[Dict[str, Any]]
    active_goal: Optional[Dict[str, Any]] = None
    progress_pct: float

    model_config = ConfigDict(from_attributes=True)

class AnalyzeRequest(BaseModel):
    user_id: str

    model_config = ConfigDict(from_attributes=True)

class Mission(BaseModel):
    id: int
    user_id: str
    title: str
    description: str
    category: str
    target_reduction_kg: Optional[float] = None
    eco_points_reward: int = 100
    status: str
    created_at: datetime
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MissionCreate(BaseModel):
    user_id: str
    title: str
    description: str
    category: str
    target_reduction_kg: Optional[float] = None
    eco_points_reward: int = 100

    model_config = ConfigDict(from_attributes=True)

class MissionComplete(BaseModel):
    mission_id: int

    model_config = ConfigDict(from_attributes=True)

class ErrorResponse(BaseModel):
    detail: str

    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)

