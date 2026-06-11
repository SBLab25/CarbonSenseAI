# CarbonSense AI — Information Architecture

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## 1. Site Map

```
CarbonSense AI
│
├── / (Landing Page)                       [PUBLIC]
│   └── CTA → /onboarding
│
├── /onboarding (Onboarding Wizard)        [PUBLIC — redirects to /dashboard if session exists]
│   ├── Step 1: Personal Info
│   ├── Step 2: Transport Habits
│   ├── Step 3: Food Habits
│   └── Step 4: Energy Usage → Baseline Agent → /dashboard
│
├── /dashboard (Insights Dashboard)        [PROTECTED]
│   ├── Monthly Footprint Card
│   ├── Category Pie Chart (Recharts)
│   ├── Trend Line Chart (Recharts)
│   ├── Goal Progress Bar
│   ├── Top Emission Source Card
│   └── Eco Points Balance Card
│
├── /chat (AI Coach Chat)                  [PROTECTED]
│   ├── Chat Message History
│   ├── SSE Streaming Display
│   └── Message Input Box
│
├── /log (Activity Logger)                 [PROTECTED]
│   ├── Tab: Structured Form Input
│   ├── Tab: Natural Language Input
│   └── Activity History Table
│
└── /missions (Mission Center)             [PROTECTED]
    ├── Available Missions Panel
    ├── Active Missions Panel
    ├── Completed Missions Panel
    └── Eco Points Balance Display
```

---

## 2. Navigation Structure

### 2.1 Global Navigation (Persistent Header)

Present on all protected routes, rendered by `Layout.tsx`:

```
┌─────────────────────────────────────────────────────────────────┐
│  🌱 CarbonSense    Dashboard    Chat    Log    Missions   [🏆 245 pts · Seedling]  │
└─────────────────────────────────────────────────────────────────┘
```

| Element | Target | Visibility |
|---------|--------|------------|
| Logo/Brand | /dashboard | Always |
| Dashboard | /dashboard | Protected routes only |
| Chat | /chat | Protected routes only |
| Log | /log | Protected routes only |
| Missions | /missions | Protected routes only |
| Eco Points Badge | None (display only) | Protected routes only |

### 2.2 Contextual Navigation

| Page | Contextual Nav |
|------|---------------|
| Landing | "Get Started" CTA button → /onboarding |
| Onboarding | Step indicators (1/4, 2/4, 3/4, 4/4) with back/next buttons |
| Dashboard | Time range selector (7d / 30d / 90d) for trend chart; "Analyze My Footprint" button |
| Log | Tab switcher: "Form" | "Natural Language" |
| Missions | Panel filters: Available / Active / Completed |

### 2.3 Breadcrumbs

No breadcrumbs — flat navigation with 6 pages. Header links provide sufficient wayfinding. Focus management on route change moves focus to page `<h1>`.

---

## 3. Page-Level Information Architecture

### 3.1 Landing Page (`/`)

| Attribute | Value |
|-----------|-------|
| **URL** | `/` |
| **Entry Points** | Direct URL, first visit |
| **Exit Points** | "Get Started" CTA → /onboarding |
| **Primary Content** | Hero section with tagline, value proposition illustration |
| **Secondary Content** | Feature highlights (3–4 cards: Coach, Dashboard, Missions, NL Logging) |
| **Key Interactions** | Click "Get Started" button |

### 3.2 Onboarding Page (`/onboarding`)

| Attribute | Value |
|-----------|-------|
| **URL** | `/onboarding` |
| **Entry Points** | Landing CTA, redirect from protected route (no session) |
| **Exit Points** | Step 4 submit → /dashboard |
| **Primary Content** | 4-step wizard form |
| **Secondary Content** | Step progress indicator, helper text for each field |
| **Key Interactions** | Fill fields, click Next/Back, submit on Step 4 |

**Step Content:**

| Step | Fields | Validation |
|------|--------|------------|
| 1 — Personal Info | name (required), country, city, lifestyle_type (urban/suburban/rural) | name is required |
| 2 — Transport | primary_transport (dropdown), weekly_transport_km (number) | transport mode required |
| 3 — Food | diet_type (vegan/vegetarian/mixed/high_meat) | selection required |
| 4 — Energy | monthly_electricity_kwh (number), heating_type (LPG/electric/none) | kWh required |

### 3.3 Dashboard Page (`/dashboard`)

| Attribute | Value |
|-----------|-------|
| **URL** | `/dashboard` |
| **Entry Points** | Nav header, post-onboarding redirect, post-analysis redirect |
| **Exit Points** | Nav links to Chat, Log, Missions; "Analyze" button triggers pipeline |
| **Primary Content** | 6 dashboard widgets (see grid below) |
| **Secondary Content** | Time range selector, empty state CTA |
| **Key Interactions** | Switch time range, click "Analyze My Footprint", hover chart tooltips |

**Widget Grid Layout:**

```
┌──────────────────────────────────────────────┐
│          Monthly Footprint Card               │  ← full width
│    142.3 kg CO₂  ↓24.1% vs baseline          │
├──────────────────────┬───────────────────────┤
│  Category Breakdown  │   Historical Trend     │  ← 2-column
│   (Pie Chart)        │   (Line Chart)         │
│                      │   [7d] [30d] [90d]     │
├──────────────────────┴───────────────────────┤
│          Goal Progress Bar                    │  ← full width
│    ████████████░░░░  15.0% of 15.0% target    │
├──────────────────────┬───────────────────────┤
│  Top Emission Source │   Eco Points Balance   │  ← 2-column
│  Transport · 47.9%   │   245 pts · Seedling    │
└──────────────────────┴───────────────────────┘
```

### 3.4 Chat Page (`/chat`)

| Attribute | Value |
|-----------|-------|
| **URL** | `/chat` |
| **Entry Points** | Nav header, post-analysis redirect |
| **Exit Points** | Nav links to Dashboard, Log, Missions |
| **Primary Content** | Chat message history with SSE streaming display |
| **Secondary Content** | Suggested prompts (for empty state) |
| **Key Interactions** | Type message, press Enter/Send, scroll history, abort stream |

**Layout:**

```
┌───────────────────────────────────────────┐
│  Chat Messages (scrollable)                │
│  ┌─────────────────────────────────────┐  │
│  │ 🧑 Why is my transport so high?     │  │
│  ├─────────────────────────────────────┤  │
│  │ 🤖 Based on your data, you logged   │  │
│  │    5 car trips this week totaling    │  │
│  │    120 km. That's 25.2 kg CO₂...    │  │
│  │    [streaming indicator ▌]          │  │
│  └─────────────────────────────────────┘  │
├───────────────────────────────────────────┤
│  [Type your message...            ] [Send] │
└───────────────────────────────────────────┘
```

### 3.5 Activity Log Page (`/log`)

| Attribute | Value |
|-----------|-------|
| **URL** | `/log` |
| **Entry Points** | Nav header, dashboard empty state CTA |
| **Exit Points** | Nav links; successful log → dashboard data refreshed |
| **Primary Content** | Tab switcher (Form / Natural Language) + input area |
| **Secondary Content** | Activity history table below input |
| **Key Interactions** | Switch tab, fill form, type NL description, submit, delete activity |

**Layout:**

```
┌───────────────────────────────────────────┐
│  [Form Input] | [Natural Language]  ← tabs │
├───────────────────────────────────────────┤
│  ┌─ Form Tab ──────────────────────────┐  │
│  │ Category: [Transport ▼]             │  │
│  │ Type:     [Car (petrol) ▼]          │  │
│  │ Amount:   [20]  Unit: [km ▼]       │  │
│  │ Notes:    [Morning commute]         │  │
│  │          [Log Activity]             │  │
│  └─────────────────────────────────────┘  │
├───────────────────────────────────────────┤
│  Activity History                         │
│  ┌────────┬──────────┬──────┬──────────┐ │
│  │ Date   │ Activity │ CO₂  │ Actions  │ │
│  ├────────┼──────────┼──────┼──────────┤ │
│  │ Jun 09 │ Car 20km │ 4.2  │ [Delete] │ │
│  │ Jun 09 │ Beef 1kg │ 27.0 │ [Delete] │ │
│  └────────┴──────────┴──────┴──────────┘ │
└───────────────────────────────────────────┘
```

### 3.6 Mission Center Page (`/missions`)

| Attribute | Value |
|-----------|-------|
| **URL** | `/missions` |
| **Entry Points** | Nav header, Coach Agent coaching message mention |
| **Exit Points** | Nav links |
| **Primary Content** | Three panels: Available, Active, Completed missions |
| **Secondary Content** | Eco Points balance, tier indicator |
| **Key Interactions** | Accept mission, mark complete, dismiss suggestion |

**Layout:**

```
┌───────────────────────────────────────────┐
│  Eco Points: 245 · Seedling 🌱            │
├───────────────────────────────────────────┤
│  Available Missions                       │
│  ┌────────────────────────────────────┐   │
│  │ 🚗 Green Commute Challenge         │   │
│  │    7 days · 150 pts · −8 kg CO₂    │   │
│  │    [Accept] [Dismiss]              │   │
│  └────────────────────────────────────┘   │
├───────────────────────────────────────────┤
│  Active Missions                          │
│  ┌────────────────────────────────────┐   │
│  │ 🥦 Meat-Free Week                  │   │
│  │    3 days left · 200 pts           │   │
│  │    [Mark Complete]                 │   │
│  └────────────────────────────────────┘   │
├───────────────────────────────────────────┤
│  Completed Missions                       │
│  ┌────────────────────────────────────┐   │
│  │ ⚡ Energy Audit Week ✓             │   │
│  │    Completed Jun 08 · +100 pts     │   │
│  └────────────────────────────────────┘   │
└───────────────────────────────────────────┘
```

---

## 4. User Flow Diagrams

### 4.1 First-Time User Flow

```
┌──────────┐     ┌─────────────┐     ┌─────────────────┐     ┌───────────┐
│  Direct   │────▶│   Landing   │────▶│   Onboarding    │────▶│ Dashboard │
│  Visit    │     │   Page (/)  │     │ (/onboarding)   │     │           │
└──────────┘     │             │     │  Steps 1–4      │     │ Baseline  │
                  │ "Get Started"│     │  ↓               │     │ displayed │
                  └─────────────┘     │ POST /users      │     └───────────┘
                                      │ POST /baseline   │
                                      │ UUID → localStorage│
                                      └─────────────────┘
```

### 4.2 Daily Usage Flow

```
┌───────────┐     ┌───────────┐     ┌──────────────────┐     ┌───────────┐
│ Dashboard │────▶│ Log Page  │────▶│ Submit Activity   │────▶│ Dashboard │
│ (review)  │     │ (/log)    │     │ (form or NL)      │     │ (updated) │
└───────────┘     └───────────┘     │                    │     │           │
                                     │ Carbon Engine calc │     │ New totals│
                                     │ Cache invalidated  │     │ New charts│
                                     └──────────────────┘     └───────────┘
```

### 4.3 AI Analysis Flow

```
┌───────────┐     ┌──────────────┐     ┌─────────────────────┐     ┌──────────┐
│ Dashboard │────▶│ Click        │────▶│ Agent Pipeline       │────▶│ Chat or  │
│           │     │ "Analyze"    │     │ Analyst → Planner    │     │ Dashboard│
└───────────┘     └──────────────┘     │ → Coach (SSE stream) │     │ (results)│
                                        │                       │     └──────────┘
                                        │ data: {tokens...}     │
                                        │ data: [PIPELINE_COMPLETE]│
                                        └─────────────────────┘
```

### 4.4 Mission Completion Flow

```
┌───────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│ Missions  │────▶│ Accept       │────▶│ Complete     │────▶│ Points Updated │
│ Page      │     │ Mission      │     │ Mission      │     │ Tier Checked   │
└───────────┘     │              │     │              │     │ Nav Badge      │
                   │ status:      │     │ status:      │     │ Refreshed      │
                   │ pending→active│    │ active→done  │     └────────────────┘
                   │ deadline set │     │ eco_points += │
                   └──────────────┘     │ reward        │
                                        └──────────────┘
```

---

## 5. Content Inventory

| Content Type | Owner | Storage | Update Trigger |
|-------------|-------|---------|----------------|
| User profile data | User (onboarding input) | `users` table | Onboarding, profile edit |
| Activity entries | User (form or NL input) | `activities` table | Every log submission |
| CO₂ calculations | System (Carbon Engine) | `activities.co2_kg` | Calculated at log time |
| Baseline footprint | AI (Baseline Agent) | `users.baseline_footprint_kg` | Once at onboarding |
| Analysis results | AI (Analyst Agent) | `insights_cache` | On pipeline trigger |
| Reduction plans | AI (Planner Agent) | `insights_cache` | On pipeline trigger |
| Coaching messages | AI (Coach Agent) | Streamed (SSE) | On pipeline trigger or chat |
| Mission definitions | AI (Planner Agent) | `missions` table | On mission generation |
| Mission status | User (accept/complete) | `missions` table | User action |
| Eco Points balance | System | `users.eco_points` | Mission completion |
| Goal definition | System + User | `goals` table | Onboarding, user edit |
| Dashboard charts | System (aggregation) | Computed from `activities` | On page load |
| Chat history | User + AI | Client-side (session) | Each message exchange |

---

## 6. Protected vs Public Routes

| Route | Access | Guard |
|-------|--------|-------|
| `/` | **Public** | None — Landing page visible to all |
| `/onboarding` | **Public** | Redirects to `/dashboard` if UUID exists in localStorage |
| `/dashboard` | **Protected** | `ProtectedRoute` — redirects to `/onboarding` if no UUID |
| `/chat` | **Protected** | `ProtectedRoute` — redirects to `/onboarding` if no UUID |
| `/log` | **Protected** | `ProtectedRoute` — redirects to `/onboarding` if no UUID |
| `/missions` | **Protected** | `ProtectedRoute` — redirects to `/onboarding` if no UUID |

**Guard Implementation:**

```typescript
// components/ProtectedRoute.tsx
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  useEffect(() => {
    if (!hasSession()) navigate('/onboarding', { replace: true });
  }, [navigate]);
  return hasSession() ? <>{children}</> : null;
}
```

---

*Document ends.*
