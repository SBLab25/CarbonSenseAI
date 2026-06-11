import datetime
from app.models.schemas import FootprintSummary, CategoryBreakdown, CarbonTrend

# TRANSPORT_FACTORS (kg CO2/km)
# Source: UK DEFRA Conversion Factors 2023, IPCC AR6
TRANSPORT_FACTORS = {
    "car_petrol": 0.21,
    "car_diesel": 0.17,
    "car_electric": 0.05,
    "bus": 0.089,
    "train": 0.041,
    "flight_domestic": 0.255,
    "flight_international": 0.195,
    "motorcycle": 0.114,
    "bicycle": 0.0,
    "walking": 0.0
}

# ENERGY_FACTORS (kg CO2/kWh)
# Source: IEA 2023, India CEA grid emission factor
ENERGY_FACTORS = {
    "electricity": 0.708,
    "natural_gas": 0.202,
    "lpg": 0.214
}

# FOOD_FACTORS (kg CO2/kg food)
# Source: Poore & Nemecek, Science (2018)
FOOD_FACTORS = {
    "beef": 27.0,
    "lamb": 39.2,
    "pork": 12.1,
    "chicken": 6.9,
    "fish": 6.1,
    "dairy": 3.2,
    "eggs": 4.8,
    "vegetables": 2.0,
    "fruits": 1.1,
    "grains": 1.4,
    "legumes": 0.9
}

# SHOPPING_FACTORS (kg CO2/item)
# Source: Berners-Lee, How Bad Are Bananas? (2020)
SHOPPING_FACTORS = {
    "electronics": 70.0,
    "clothing": 10.0,
    "household_item": 15.0
}

INDIA_MONTHLY_AVERAGE_KG = 158.0  # 1.9 tonnes/year ÷ 12

FACTORS_MAP = {
    "transport": TRANSPORT_FACTORS,
    "energy": ENERGY_FACTORS,
    "food": FOOD_FACTORS,
    "shopping": SHOPPING_FACTORS
}

def calculate_activity_co2(category: str, activity_type: str, amount: float) -> float:
    if amount <= 0:
        return 0.0
    
    cat = category.lower().strip()
    act = activity_type.lower().strip()
    
    if cat not in FACTORS_MAP:
        return 0.0
    
    factors = FACTORS_MAP[cat]
    if act not in factors:
        return 0.0
        
    factor = factors[act]
    return round(factor * amount, 4)

def calculate_monthly_summary(activities: list[dict], baseline_kg: float) -> FootprintSummary:
    transport_kg = 0.0
    energy_kg = 0.0
    food_kg = 0.0
    shopping_kg = 0.0
    
    for act in activities:
        cat = act.get("category", "").lower().strip()
        co2 = act.get("co2_kg", 0.0)
        if cat == "transport":
            transport_kg += co2
        elif cat == "energy":
            energy_kg += co2
        elif cat == "food":
            food_kg += co2
        elif cat == "shopping":
            shopping_kg += co2
            
    total_kg = transport_kg + energy_kg + food_kg + shopping_kg
    return FootprintSummary(
        total_kg=round(total_kg, 4),
        transport_kg=round(transport_kg, 4),
        energy_kg=round(energy_kg, 4),
        food_kg=round(food_kg, 4),
        shopping_kg=round(shopping_kg, 4)
    )

def calculate_category_breakdown(summary: FootprintSummary) -> dict[str, CategoryBreakdown]:
    total = summary.total_kg
    if total <= 0:
        return {
            "transport": CategoryBreakdown(kg=0.0, pct=0.0),
            "energy": CategoryBreakdown(kg=0.0, pct=0.0),
            "food": CategoryBreakdown(kg=0.0, pct=0.0),
            "shopping": CategoryBreakdown(kg=0.0, pct=0.0)
        }
    
    return {
        "transport": CategoryBreakdown(kg=summary.transport_kg, pct=round((summary.transport_kg / total) * 100, 2)),
        "energy": CategoryBreakdown(kg=summary.energy_kg, pct=round((summary.energy_kg / total) * 100, 2)),
        "food": CategoryBreakdown(kg=summary.food_kg, pct=round((summary.food_kg / total) * 100, 2)),
        "shopping": CategoryBreakdown(kg=summary.shopping_kg, pct=round((summary.shopping_kg / total) * 100, 2))
    }

def calculate_trend(daily_totals: dict[str, float], days: int) -> list[CarbonTrend]:
    today = datetime.date.today()
    trends = []
    for i in range(days):
        d = today - datetime.timedelta(days=days - 1 - i)
        d_str = d.strftime("%Y-%m-%d")
        val = daily_totals.get(d_str, 0.0)
        trends.append(CarbonTrend(date=d_str, total_kg=round(val, 4)))
    return trends

def calculate_progress(current_kg: float, baseline_kg: float) -> float:
    if baseline_kg <= 0:
        return 0.0
    return round(((baseline_kg - current_kg) / baseline_kg) * 100, 2)

def get_vs_india_average(monthly_kg: float) -> float:
    return round((monthly_kg / INDIA_MONTHLY_AVERAGE_KG) * 100, 2)
