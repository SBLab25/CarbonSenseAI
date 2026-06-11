# CarbonSense AI — API Contracts

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. API Overview

| Property | Value |
|----------|-------|
| **Base URL (development)** | `http://localhost:8000/api/v1` |
| **Base URL (production)** | `https://carbonsense-api.onrender.com/api/v1` |
| **Versioning** | Path-based: `/api/v1/` |
| **Authentication** | None (UUID-based sessions). User ID passed in request body or path parameter. |
| **Content-Type** | `application/json` for all JSON endpoints; `text/event-stream` for SSE endpoints |
| **CORS** | Allowed origins: `http://localhost:5173`, `https://carbonsense.vercel.app` |

---

## 2. Request/Response Conventions

### Error Envelope

All errors use a consistent JSON envelope:

```json
{
  "detail": "User-facing error message"
}
```

| HTTP Status | Meaning | When |
|---|---|---|
| 200 | Success | Normal response |
| 404 | Not Found | User/activity/mission not found |
| 422 | Validation Error | Pydantic validation failure |
| 429 | Rate Limited | Too many requests per rate limit window |
| 500 | Server Error | Gemini API failure or unexpected error |

### Pagination

Activity history uses `page` query parameter:

```
GET /activities/{user_id}?page=1&per_page=20
```

Response includes: `items`, `total`, `page`, `per_page`, `pages`.

---

## 3. Endpoint Reference

---

### 3.1 Health

#### `GET /health`

Health check for keepalive ping.

**Response (200):**
```json
{
  "status": "ok",
  "timestamp": "2026-06-09T10:00:00Z"
}
```

---

### 3.2 Users

#### `POST /users`

Create a new user during onboarding.

**Request Body:**
```json
{
  "name": "Alex",                          // required, max 100 chars
  "country": "India",                      // optional
  "city": "Bengaluru",                     // optional
  "lifestyle_type": "urban",              // optional: urban | suburban | rural
  "diet_type": "mixed",                   // required: vegan | vegetarian | mixed | high_meat
  "primary_transport": "car_petrol",      // required: transport type enum
  "weekly_transport_km": 80.0,            // required, >= 0
  "monthly_electricity_kwh": 150.0,       // required, >= 0
  "heating_type": "lpg"                   // required: lpg | electric | none
}
```

**Response (200):**
```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-06-09T10:00:00Z"
}
```

**Errors:**

| Status | Detail |
|---|---|
| 422 | `"name is required"` / `"diet_type must be one of: vegan, vegetarian, mixed, high_meat"` |

---

#### `GET /users/{user_id}`

Get user profile.

**Path Params:** `user_id` (UUID string)

**Response (200):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Alex",
  "country": "India",
  "city": "Bengaluru",
  "lifestyle_type": "urban",
  "diet_type": "mixed",
  "primary_transport": "car_petrol",
  "weekly_transport_km": 80.0,
  "monthly_electricity_kwh": 150.0,
  "heating_type": "lpg",
  "baseline_footprint_kg": 187.4,
  "monthly_target_reduction_pct": 15.0,
  "eco_points": 245,
  "created_at": "2026-06-09T10:00:00Z",
  "updated_at": "2026-06-09T10:00:00Z"
}
```

**Errors:**

| Status | Detail |
|---|---|
| 404 | `"User not found"` |

---

#### `PUT /users/{user_id}`

Update user profile (partial update).

**Request Body:** Any subset of user fields (same schema as POST, all optional).

**Response (200):** Updated user object (same as GET response).

**Errors:**

| Status | Detail |
|---|---|
| 404 | `"User not found"` |
| 422 | Pydantic validation errors |

---

### 3.3 Onboarding

#### `POST /onboarding/baseline`

Run Baseline Agent to calculate initial footprint estimate.

**Request Body:**
```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"  // required
}
```

**Response (200):**
```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "monthly_baseline_kg": 187.4,
  "breakdown": {
    "transport": 95.2,
    "energy": 42.8,
    "food": 38.1,
    "shopping": 11.3
  },
  "vs_india_average_pct": 118.5,
  "primary_hotspot": "transport",
  "confidence": "medium"
}
```

**Errors:**

| Status | Detail |
|---|---|
| 404 | `"User not found"` |
| 500 | `"Baseline calculation failed. Please try again."` |

---

### 3.4 Activities

#### `POST /activities`

Log a structured activity (form input).

**Request Body:**
```json
{
  "user_id": "a1b2c3d4...",       // required, UUID
  "category": "transport",        // required: transport | energy | food | shopping
  "type": "car_petrol",          // required: specific activity type
  "amount": 20.0,                // required, >= 0
  "unit": "km",                  // required: km | kWh | kg | item
  "notes": "Morning commute"    // optional
}
```

**Response (200):**
```json
{
  "activity_id": 42,
  "co2_kg": 4.2,
  "category": "transport",
  "type": "car_petrol",
  "amount": 20.0,
  "unit": "km",
  "logged_at": "2026-06-09T08:30:00Z"
}
```

**Errors:**

| Status | Detail |
|---|---|
| 404 | `"User not found"` |
| 422 | `"category must be one of: transport, energy, food, shopping"` |

---

#### `POST /activities/parse-nl`

Parse natural language description → structured activity → auto-log.

**Request Body:**
```json
{
  "user_id": "a1b2c3d4...",                                          // required
  "description": "I drove 25 km to the office in my diesel car"     // required, max 500 chars
}
```

**Response (200):**
```json
{
  "parsed": {
    "category": "transport",
    "type": "car_diesel",
    "amount": 25.0,
    "unit": "km",
    "confidence": "high"
  },
  "activity_id": 43,
  "co2_kg": 4.25
}
```

**Errors:**

| Status | Detail |
|---|---|
| 404 | `"User not found"` |
| 429 | `"Too many parse requests. Please wait before trying again."` |
| 500 | `"Could not parse activity. Please try the form input instead."` |

---

#### `GET /activities/{user_id}`

Get paginated activity history.

**Query Params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max 100) |
| `category` | string | null | Filter by category |

**Response (200):**
```json
{
  "items": [
    {
      "id": 43,
      "category": "transport",
      "type": "car_diesel",
      "amount": 25.0,
      "unit": "km",
      "co2_kg": 4.25,
      "source": "natural_language",
      "notes": null,
      "logged_at": "2026-06-09T08:30:00Z"
    }
  ],
  "total": 47,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

#### `DELETE /activities/{id}`

Delete an activity entry.

**Response (200):**
```json
{
  "deleted": true,
  "activity_id": 43
}
```

**Errors:**

| Status | Detail |
|---|---|
| 404 | `"Activity not found"` |

---

### 3.5 Carbon Calculations

#### `GET /carbon/summary/{user_id}`

Monthly footprint summary with category breakdown.

**Response (200):**
```json
{
  "user_id": "a1b2c3d4...",
  "period": "2026-06",
  "total_kg": 142.3,
  "baseline_kg": 187.4,
  "reduction_pct": 24.1,
  "breakdown": {
    "transport": { "kg": 68.1, "pct": 47.9 },
    "energy":    { "kg": 35.4, "pct": 24.9 },
    "food":      { "kg": 27.2, "pct": 19.1 },
    "shopping":  { "kg": 11.6, "pct": 8.2 }
  },
  "vs_india_average_pct": 89.4,
  "target_reduction_pct": 15.0
}
```

---

#### `GET /carbon/trends/{user_id}`

Daily CO₂ totals for trend chart.

**Query Params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `days` | int | 30 | Number of days (7, 30, or 90) |

**Response (200):**
```json
[
  { "date": "2026-06-01", "total_kg": 12.4 },
  { "date": "2026-06-02", "total_kg": 8.7 },
  { "date": "2026-06-03", "total_kg": 0.0 },
  { "date": "2026-06-04", "total_kg": 15.2 }
]
```

---

#### `GET /carbon/progress/{user_id}`

Progress vs baseline and India average.

**Response (200):**
```json
{
  "baseline_kg": 187.4,
  "current_monthly_kg": 142.3,
  "reduction_pct": 24.1,
  "vs_india_average_pct": 89.4,
  "india_average_monthly_kg": 158.3,
  "on_track": true
}
```

---

### 3.6 Agent Pipeline

#### `POST /agents/analyze`

Run full Analyst → Planner → Coach pipeline. Returns SSE stream.

**Request Body:**
```json
{
  "user_id": "a1b2c3d4..."  // required
}
```

**Response:** `text/event-stream`

```
data: Transportation is your largest emission source at 47.9% of your total footprint.

data: Based on your 80 km weekly commute, switching 3 days to train

data: could reduce your transport emissions by approximately 14 kg CO₂ per month.

data: [PIPELINE_COMPLETE]

```

**Errors (SSE frame):**
```
data: [ERROR] An error occurred during analysis. Please try again.

```

**HTTP Errors:**

| Status | Detail |
|---|---|
| 404 | `"User not found"` |
| 429 | `"Too many analysis requests. Please wait before retrying."` |

---

#### `GET /agents/insights/{user_id}`

Return cached latest analysis + plan (no AI call).

**Response (200):**
```json
{
  "analysis": {
    "primary_hotspot": "transport",
    "hotspots": [
      {
        "category": "transport",
        "pct_of_total": 47.9,
        "vs_baseline_change_pct": -5.2,
        "key_behaviors": ["Daily car commute", "Weekend road trips"],
        "reduction_opportunity_kg": 14.0
      }
    ],
    "behavioral_patterns": ["Consistent weekday commuting", "Low weekend activity"],
    "quick_win_available": true,
    "analysis_confidence": "high"
  },
  "plan": {
    "strategies": [
      {
        "title": "Train Commute Switch",
        "action": "Replace 3 of 5 weekly car commutes with train",
        "category": "transport",
        "monthly_saving_kg": 14.0,
        "difficulty": "medium",
        "timeframe_days": 7,
        "mission_type": "green_commute"
      }
    ],
    "total_potential_saving_kg": 22.5,
    "recommended_goal_pct": 20,
    "thirty_day_focus": "Switch to train for weekday commutes"
  },
  "cached_at": "2026-06-09T10:00:00Z",
  "valid_until": "2026-06-10T10:00:00Z"
}
```

**Errors:**

| Status | Detail |
|---|---|
| 404 | `"No cached insights found. Run an analysis first."` |

---

### 3.7 Chat

#### `POST /chat/stream`

Send message to Coach Agent, stream response via SSE.

**Request Body:**
```json
{
  "user_id": "a1b2c3d4...",                                            // required
  "message": "Why does meat consumption produce so much carbon?",      // required, max 1000 chars
  "history": [                                                          // optional, max 10 turns
    { "role": "user", "content": "Tell me about my footprint" },
    { "role": "assistant", "content": "Based on your data..." }
  ]
}
```

**Response:** `text/event-stream` (same frame format as `/agents/analyze`)

**Errors:**

| Status | Detail |
|---|---|
| 429 | `"Please wait a moment before sending another message."` |
| 500 | `"Chat service is temporarily unavailable."` |

---

### 3.8 Missions

#### `GET /missions/{user_id}`

Get all missions for user.

**Response (200):**
```json
{
  "missions": [
    {
      "id": 1,
      "title": "Green Commute Challenge",
      "description": "Replace 3 car trips with public transport this week",
      "category": "transport",
      "target_reduction_kg": 8.0,
      "eco_points_reward": 150,
      "status": "active",
      "created_at": "2026-06-09T10:00:00Z",
      "accepted_at": "2026-06-09T10:05:00Z",
      "completed_at": null,
      "deadline": "2026-06-16T10:05:00Z"
    }
  ],
  "eco_points_total": 245,
  "tier": "Seedling"
}
```

---

#### `POST /missions/generate`

Generate new mission suggestions from Planner Agent output.

**Request Body:**
```json
{
  "user_id": "a1b2c3d4..."  // required
}
```

**Response (200):**
```json
{
  "missions_created": 3,
  "missions": [
    {
      "id": 5,
      "title": "Meat-Free Week",
      "description": "Eat no meat for 7 days",
      "category": "food",
      "target_reduction_kg": 5.0,
      "eco_points_reward": 200,
      "status": "pending"
    }
  ]
}
```

---

#### `PUT /missions/{mission_id}/accept`

Accept a pending mission.

**Response (200):**
```json
{
  "id": 5,
  "status": "active",
  "accepted_at": "2026-06-09T12:00:00Z",
  "deadline": "2026-06-16T12:00:00Z"
}
```

**Errors:**

| Status | Detail |
|---|---|
| 404 | `"Mission not found"` |
| 422 | `"Mission is not in pending status"` |

---

#### `POST /missions/{mission_id}/complete`

Mark mission as completed, award Eco Points.

**Response (200):**
```json
{
  "id": 5,
  "status": "completed",
  "completed_at": "2026-06-12T15:00:00Z",
  "eco_points_awarded": 200,
  "new_total_eco_points": 445,
  "new_tier": "Sapling"
}
```

**Errors:**

| Status | Detail |
|---|---|
| 404 | `"Mission not found"` |
| 422 | `"Mission is not in active status"` |

---

## 4. SSE Streaming Protocol

### Frame Format

```
data: {text content}\n\n
```

Each SSE frame contains one `data:` line followed by two newlines.

### Sentinel Values

| Sentinel | Meaning |
|---|---|
| `data: [PIPELINE_COMPLETE]\n\n` | Agent pipeline has finished; all data streamed |
| `data: [ERROR] {message}\n\n` | Error occurred; `{message}` is user-safe |

### Response Headers

```
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no
```

`X-Accel-Buffering: no` disables Nginx/proxy buffering on Render for real-time streaming.

---

## 5. Rate Limits

| Endpoint | Limit | Window | Key |
|---|---|---|---|
| `POST /agents/analyze` | 3 requests | per hour | `{user_id}:analyze` |
| `POST /chat/stream` | 10 requests | per minute | `{user_id}:chat` |
| `POST /activities/parse-nl` | 20 requests | per minute | `{user_id}:nl_parse` |

Rate limiter is an in-memory sliding window counter. On limit exceeded, returns HTTP 429 with:

```json
{
  "detail": "Too many requests. Please wait before trying again."
}
```

---

## 6. Error Code Reference

| HTTP Status | Code | User-Facing Message |
|---|---|---|
| 404 | `not_found` | "User not found" / "Activity not found" / "Mission not found" |
| 422 | `validation_error` | Specific Pydantic validation message |
| 429 | `rate_limited` | "Too many requests. Please wait before trying again." |
| 500 | `gemini_error` | "AI service is temporarily unavailable. Please try again." |
| 500 | `pipeline_error` | "Analysis could not be completed. Please try again." |
| 500 | `parse_error` | "Could not parse activity. Please try the form input instead." |
| 500 | `internal_error` | "An unexpected error occurred." |

---

## 7. TypeScript Type Definitions

```ts
// ============================
// Users
// ============================

export interface CreateUserRequest {
  name: string;
  country?: string;
  city?: string;
  lifestyle_type?: 'urban' | 'suburban' | 'rural';
  diet_type: 'vegan' | 'vegetarian' | 'mixed' | 'high_meat';
  primary_transport: string;
  weekly_transport_km: number;
  monthly_electricity_kwh: number;
  heating_type: 'lpg' | 'electric' | 'none';
}

export interface CreateUserResponse {
  user_id: string;
  created_at: string;
}

export interface User {
  id: string;
  name: string;
  country: string | null;
  city: string | null;
  lifestyle_type: string | null;
  diet_type: string | null;
  primary_transport: string | null;
  weekly_transport_km: number | null;
  monthly_electricity_kwh: number | null;
  heating_type: string | null;
  baseline_footprint_kg: number;
  monthly_target_reduction_pct: number;
  eco_points: number;
  created_at: string;
  updated_at: string;
}

// ============================
// Onboarding
// ============================

export interface BaselineRequest {
  user_id: string;
}

export interface BaselineResult {
  user_id: string;
  monthly_baseline_kg: number;
  breakdown: CategoryBreakdown;
  vs_india_average_pct: number;
  primary_hotspot: string;
  confidence: 'high' | 'medium' | 'low';
}

export interface CategoryBreakdown {
  transport: number;
  energy: number;
  food: number;
  shopping: number;
}

// ============================
// Activities
// ============================

export type ActivityCategory = 'transport' | 'energy' | 'food' | 'shopping';
export type ActivityUnit = 'km' | 'kWh' | 'kg' | 'item';
export type ActivitySource = 'form' | 'natural_language';

export interface ActivityCreate {
  user_id: string;
  category: ActivityCategory;
  type: string;
  amount: number;
  unit: ActivityUnit;
  notes?: string;
}

export interface ActivityResponse {
  activity_id: number;
  co2_kg: number;
  category: ActivityCategory;
  type: string;
  amount: number;
  unit: ActivityUnit;
  logged_at: string;
}

export interface NLActivityRequest {
  user_id: string;
  description: string;
}

export interface NLParseResponse {
  parsed: {
    category: ActivityCategory;
    type: string;
    amount: number;
    unit: ActivityUnit;
    confidence: 'high' | 'medium' | 'low';
  };
  activity_id: number;
  co2_kg: number;
}

export interface ActivityHistoryItem {
  id: number;
  category: ActivityCategory;
  type: string;
  amount: number;
  unit: ActivityUnit;
  co2_kg: number;
  source: ActivitySource;
  notes: string | null;
  logged_at: string;
}

export interface ActivityHistory {
  items: ActivityHistoryItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// ============================
// Carbon
// ============================

export interface CarbonSummary {
  user_id: string;
  period: string;
  total_kg: number;
  baseline_kg: number;
  reduction_pct: number;
  breakdown: {
    transport: { kg: number; pct: number };
    energy: { kg: number; pct: number };
    food: { kg: number; pct: number };
    shopping: { kg: number; pct: number };
  };
  vs_india_average_pct: number;
  target_reduction_pct: number;
}

export interface CarbonTrend {
  date: string;
  total_kg: number;
}

export interface CarbonProgress {
  baseline_kg: number;
  current_monthly_kg: number;
  reduction_pct: number;
  vs_india_average_pct: number;
  india_average_monthly_kg: number;
  on_track: boolean;
}

// ============================
// Agents
// ============================

export interface AnalyzeRequest {
  user_id: string;
}

export interface HotspotDetail {
  category: string;
  pct_of_total: number;
  vs_baseline_change_pct: number;
  key_behaviors: string[];
  reduction_opportunity_kg: number;
}

export interface AnalysisResult {
  primary_hotspot: string;
  hotspots: HotspotDetail[];
  behavioral_patterns: string[];
  quick_win_available: boolean;
  analysis_confidence: 'high' | 'medium' | 'low';
}

export interface ReductionStrategy {
  title: string;
  action: string;
  category: string;
  monthly_saving_kg: number;
  difficulty: 'easy' | 'medium' | 'hard';
  timeframe_days: number;
  mission_type: string | null;
}

export interface PlanResult {
  strategies: ReductionStrategy[];
  total_potential_saving_kg: number;
  recommended_goal_pct: number;
  thirty_day_focus: string;
}

export interface InsightsResponse {
  analysis: AnalysisResult;
  plan: PlanResult;
  cached_at: string;
  valid_until: string;
}

// ============================
// Chat
// ============================

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatStreamRequest {
  user_id: string;
  message: string;
  history?: ChatMessage[];
}

// ============================
// Missions
// ============================

export type MissionStatus = 'pending' | 'active' | 'completed' | 'expired';
export type EcoTier = 'Seedling' | 'Sapling' | 'Tree' | 'Forest';

export interface Mission {
  id: number;
  title: string;
  description: string;
  category: ActivityCategory;
  target_reduction_kg: number | null;
  eco_points_reward: number;
  status: MissionStatus;
  created_at: string;
  accepted_at: string | null;
  completed_at: string | null;
  deadline: string | null;
}

export interface MissionsResponse {
  missions: Mission[];
  eco_points_total: number;
  tier: EcoTier;
}

export interface MissionCompleteResponse {
  id: number;
  status: 'completed';
  completed_at: string;
  eco_points_awarded: number;
  new_total_eco_points: number;
  new_tier: EcoTier;
}
```

---

*Document ends.*
