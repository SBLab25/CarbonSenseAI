# CarbonSense AI — Carbon Scoring Engine Specification

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. Purpose

The Carbon Scoring Engine is the deterministic, AI-free calculation layer responsible for converting raw activity data (km driven, kWh consumed, kg food purchased) into kg CO₂ equivalent emissions. It is the single source of truth for all carbon calculations in the system.

**Key design decision:** The Carbon Engine has zero AI dependency. All calculations use hardcoded emission factors from peer-reviewed sources (IPCC, EPA, DEFRA, India CEA). This makes the engine independently testable, auditable, and trustworthy — critical for a sustainability tool.

---

## 2. Core Calculation Function

### Signature

```python
def calculate_activity_co2(category: str, activity_type: str, amount: float) -> float:
    """
    Calculate CO₂ emissions in kg for a given activity.
    
    Args:
        category: One of 'transport', 'energy', 'food', 'shopping'
        activity_type: Specific type within category (e.g., 'car_petrol', 'beef')
        amount: Raw quantity (km, kWh, kg, or item count)
    
    Returns:
        CO₂ equivalent in kg, rounded to 2 decimal places.
        Returns 0.0 for unknown types (graceful fallback).
    """
```

### Calculation Formula

```
co2_kg = emission_factor[category][activity_type] × amount
```

Where `emission_factor` is looked up from the appropriate category dictionary.

### Edge Cases

| Scenario | Behavior |
|---|---|
| `amount = 0` | Returns `0.0` — valid (zero-emission logging) |
| `amount < 0` | Rejected at Pydantic validation layer (never reaches engine) |
| Unknown `activity_type` | Returns `0.0` — graceful fallback, logged as warning |
| Unknown `category` | Returns `0.0` — graceful fallback, logged as warning |

---

## 3. Emission Factor Tables

### 3.1 Transport Factors (kg CO₂ per km)

| Activity Type | Factor | Source |
|---|---|---|
| `car_petrol` | 0.21 | DEFRA 2023 — Average medium car, petrol |
| `car_diesel` | 0.17 | DEFRA 2023 — Average medium car, diesel |
| `car_electric` | 0.05 | DEFRA 2023 — BEV (grid-averaged charging) |
| `car_hybrid` | 0.12 | DEFRA 2023 — Average PHEV, blended mode |
| `motorcycle` | 0.11 | DEFRA 2023 — Average motorcycle |
| `bus` | 0.089 | DEFRA 2023 — Average local bus |
| `train` | 0.041 | DEFRA 2023 — National rail average |
| `metro` | 0.033 | DEFRA 2023 — Light rail / metro |
| `auto_rickshaw` | 0.08 | India-specific estimate (CNG auto, urban) |
| `bicycle` | 0.0 | Zero emission |
| `walking` | 0.0 | Zero emission |
| `flight_domestic` | 0.255 | DEFRA 2023 — Domestic flight per passenger-km |
| `flight_international` | 0.195 | DEFRA 2023 — Long-haul economy per passenger-km |

### 3.2 Energy Factors (kg CO₂ per kWh or unit)

| Activity Type | Factor | Unit | Source |
|---|---|---|---|
| `electricity` | 0.708 | kWh | India CEA 2023 — Grid emission factor |
| `lpg_cooking` | 2.98 | kg (LPG) | IPCC — LPG combustion per kg |
| `natural_gas` | 2.0 | m³ | EPA — Natural gas per cubic meter |
| `solar` | 0.0 | kWh | Zero emission (own generation) |

### 3.3 Food Factors (kg CO₂ per kg food)

| Activity Type | Factor | Source |
|---|---|---|
| `beef` | 27.0 | Poore & Nemecek 2018 (Science) — Beef herd |
| `lamb` | 24.0 | Poore & Nemecek 2018 — Lamb & mutton |
| `pork` | 12.1 | Poore & Nemecek 2018 — Pig meat |
| `chicken` | 6.9 | Poore & Nemecek 2018 — Poultry meat |
| `fish` | 6.1 | Poore & Nemecek 2018 — Farmed fish |
| `dairy` | 3.2 | Poore & Nemecek 2018 — Milk |
| `eggs` | 4.8 | Poore & Nemecek 2018 — Eggs (per dozen→per kg) |
| `vegetables` | 2.0 | Poore & Nemecek 2018 — Average vegetables |
| `fruits` | 1.1 | Poore & Nemecek 2018 — Average fruits |
| `grains` | 1.4 | Poore & Nemecek 2018 — Wheat & Rice avg |
| `legumes` | 0.9 | Poore & Nemecek 2018 — Groundnuts avg |

### 3.4 Shopping Factors (kg CO₂ per item)

| Activity Type | Factor | Source |
|---|---|---|
| `clothing` | 10.0 | WRAP UK — Average garment (cotton T-shirt equivalent) |
| `electronics_small` | 25.0 | Apple Environmental Reports — Smartphone average |
| `electronics_large` | 300.0 | IEA/Dell — Laptop average lifecycle production |
| `furniture` | 50.0 | DEFRA 2023 — Average furniture item |
| `general_goods` | 5.0 | Estimate — Average consumer good |

---

## 4. Implementation

### 4.1 Python Source (`app/services/carbon_engine.py`)

```python
"""
Carbon Scoring Engine — Deterministic emission calculations.
All factors sourced from IPCC, DEFRA, EPA, and peer-reviewed research.
This module has ZERO AI dependency.
"""

import logging

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------
# Source: DEFRA 2023 Greenhouse Gas Conversion Factors
# Unit: kg CO₂ per km
# -----------------------------------------------------------------
TRANSPORT_FACTORS: dict[str, float] = {
    "car_petrol": 0.21,
    "car_diesel": 0.17,
    "car_electric": 0.05,
    "car_hybrid": 0.12,
    "motorcycle": 0.11,
    "bus": 0.089,
    "train": 0.041,
    "metro": 0.033,
    "auto_rickshaw": 0.08,
    "bicycle": 0.0,
    "walking": 0.0,
    "flight_domestic": 0.255,
    "flight_international": 0.195,
}

# -----------------------------------------------------------------
# Sources: India CEA 2023 (electricity), IPCC (LPG), EPA (natural gas)
# Unit: kg CO₂ per kWh (or per kg/m³ for gas)
# -----------------------------------------------------------------
ENERGY_FACTORS: dict[str, float] = {
    "electricity": 0.708,
    "lpg_cooking": 2.98,
    "natural_gas": 2.0,
    "solar": 0.0,
}

# -----------------------------------------------------------------
# Source: Poore & Nemecek (2018), Science
# "Reducing food's environmental impacts through producers and consumers"
# Unit: kg CO₂ per kg of food product
# -----------------------------------------------------------------
FOOD_FACTORS: dict[str, float] = {
    "beef": 27.0,
    "lamb": 24.0,
    "pork": 12.1,
    "chicken": 6.9,
    "fish": 6.1,
    "dairy": 3.2,
    "eggs": 4.8,
    "vegetables": 2.0,
    "fruits": 1.1,
    "grains": 1.4,
    "legumes": 0.9,
}

# -----------------------------------------------------------------
# Sources: WRAP UK (clothing), Apple/IEA/Dell reports (electronics)
# Unit: kg CO₂ per item
# -----------------------------------------------------------------
SHOPPING_FACTORS: dict[str, float] = {
    "clothing": 10.0,
    "electronics_small": 25.0,
    "electronics_large": 300.0,
    "furniture": 50.0,
    "general_goods": 5.0,
}

# Master lookup table
EMISSION_FACTORS: dict[str, dict[str, float]] = {
    "transport": TRANSPORT_FACTORS,
    "energy": ENERGY_FACTORS,
    "food": FOOD_FACTORS,
    "shopping": SHOPPING_FACTORS,
}

# India national average: 1.9 tonnes CO₂/year ≈ 158.3 kg/month
INDIA_AVERAGE_MONTHLY_KG = 158.3


def calculate_activity_co2(
    category: str, activity_type: str, amount: float
) -> float:
    """Calculate kg CO₂ for a single activity."""
    category_factors = EMISSION_FACTORS.get(category)
    if category_factors is None:
        logger.warning(f"Unknown category: {category}")
        return 0.0

    factor = category_factors.get(activity_type)
    if factor is None:
        logger.warning(f"Unknown activity type: {activity_type} in {category}")
        return 0.0

    return round(factor * amount, 2)


def get_india_comparison(monthly_kg: float) -> float:
    """Return user's footprint as a percentage of India's national average."""
    if INDIA_AVERAGE_MONTHLY_KG == 0:
        return 0.0
    return round((monthly_kg / INDIA_AVERAGE_MONTHLY_KG) * 100.0, 1)
```

---

## 5. Aggregation Functions

### 5.1 Monthly Footprint by Category (SQL)

```sql
-- Used by: GET /carbon/summary/{user_id}
-- Returns: total kg per category for a given month
SELECT
    category,
    SUM(co2_kg) AS total_kg,
    ROUND(SUM(co2_kg) * 100.0 / NULLIF(
        (SELECT SUM(co2_kg) FROM activities
         WHERE user_id = :user_id AND strftime('%Y-%m', logged_at) = :month), 0
    ), 1) AS pct
FROM activities
WHERE user_id = :user_id
  AND strftime('%Y-%m', logged_at) = :month
GROUP BY category
ORDER BY total_kg DESC;
```

### 5.2 Daily Trend (SQL)

```sql
-- Used by: GET /carbon/trends/{user_id}?days={n}
-- Returns: daily CO₂ totals for the past N days
SELECT
    DATE(logged_at) AS date,
    SUM(co2_kg) AS total_kg
FROM activities
WHERE user_id = :user_id
  AND logged_at >= DATE('now', :offset || ' days')
GROUP BY DATE(logged_at)
ORDER BY date ASC;
```

### 5.3 Progress vs Baseline (SQL)

```sql
-- Used by: GET /carbon/progress/{user_id}
-- Returns: current month total, baseline, and reduction percentage
SELECT
    u.baseline_footprint_kg,
    COALESCE(SUM(a.co2_kg), 0) AS current_month_kg,
    CASE
        WHEN u.baseline_footprint_kg > 0
        THEN ROUND((1.0 - COALESCE(SUM(a.co2_kg), 0) / u.baseline_footprint_kg) * 100, 1)
        ELSE 0
    END AS reduction_pct
FROM users u
LEFT JOIN activities a ON a.user_id = u.id
    AND strftime('%Y-%m', a.logged_at) = strftime('%Y-%m', 'now')
WHERE u.id = :user_id
GROUP BY u.id;
```

---

## 6. Eco Points Tier System

### 6.1 Tier Definitions

| Tier | Range | Badge |
|---|---|---|
| Seedling 🌱 | 0 – 249 points | 🌱 |
| Sapling 🌿 | 250 – 749 points | 🌿 |
| Tree 🌳 | 750 – 1,499 points | 🌳 |
| Forest 🌲 | 1,500+ points | 🌲 |

### 6.2 Point Award Rules

| Event | Points | Trigger |
|---|---|---|
| Complete a mission | `eco_points_reward` (100–300 per mission) | `POST /missions/{id}/complete` |

### 6.3 Tier Calculation

```python
def get_eco_tier(points: int) -> str:
    """Return tier label based on Eco Points balance."""
    if points >= 1500:
        return "Forest"
    elif points >= 750:
        return "Tree"
    elif points >= 250:
        return "Sapling"
    else:
        return "Seedling"
```

---

## 7. Baseline Calculation Flow

The Baseline Agent uses Gemini function calling to estimate a monthly footprint from onboarding profile data:

```
User Profile Input:
  ├── primary_transport: "car_petrol"
  ├── weekly_transport_km: 80
  ├── diet_type: "mixed"
  ├── monthly_electricity_kwh: 150
  └── heating_type: "lpg"
         │
         ▼ Gemini function call (BaselineAgent schema)
         │
  BaselineResult:
  ├── monthly_baseline_kg: 187.4
  ├── breakdown:
  │   ├── transport: 95.2   (car_petrol: 0.21 × 80 km × 4.33 weeks ≈ 72.7 + overhead)
  │   ├── energy: 42.8      (electricity: 0.708 × 150 = 106.2 + LPG + overhead)
  │   ├── food: 38.1        (mixed diet estimate ≈ ~2 kg meat, dairy, vegetables per week)
  │   └── shopping: 11.3    (estimated monthly shopping footprint)
  ├── vs_india_average_pct: 118.5
  ├── primary_hotspot: "transport"
  └── confidence: "medium"
```

**Note:** The Baseline Agent uses Gemini to provide a holistic estimate, not a simple multiplication. It considers lifestyle_type (urban vs rural patterns), regional factors, and diet composition. The Carbon Engine handles individual activity calculations; the Baseline Agent handles the initial profile-based estimation.

---

## 8. Test Coverage Requirements

| Test | Assertion | Expected |
|---|---|---|
| `test_car_petrol_calculation` | `calculate_activity_co2("transport", "car_petrol", 100)` | `≈ 21.0` |
| `test_bicycle_zero_emission` | `calculate_activity_co2("transport", "bicycle", 50)` | `0.0` |
| `test_electricity_india_grid` | `calculate_activity_co2("energy", "electricity", 100)` | `≈ 70.8` |
| `test_beef_high_emission` | `calculate_activity_co2("food", "beef", 1.0)` | `≈ 27.0` |
| `test_unknown_type_returns_zero` | `calculate_activity_co2("transport", "rocket_ship", 100)` | `0.0` |
| `test_zero_amount` | `calculate_activity_co2("transport", "car_petrol", 0)` | `0.0` |
| `test_all_transport_factors_positive_or_zero` | All values in `TRANSPORT_FACTORS` | `≥ 0.0` |
| `test_india_comparison` | `get_india_comparison(158.3)` | `100.0` |
| `test_india_comparison_below` | `get_india_comparison(100.0)` | `≈ 63.2` |
| `test_india_comparison_above` | `get_india_comparison(200.0)` | `≈ 126.3` |
| `test_eco_tier_seedling` | `get_eco_tier(100)` | `"Seedling"` |
| `test_eco_tier_sapling` | `get_eco_tier(500)` | `"Sapling"` |
| `test_eco_tier_tree` | `get_eco_tier(1000)` | `"Tree"` |
| `test_eco_tier_forest` | `get_eco_tier(2000)` | `"Forest"` |
| `test_eco_tier_boundary_250` | `get_eco_tier(250)` | `"Sapling"` |

**Target:** ≥ 90% line coverage on `carbon_engine.py`.

---

*Document ends.*
