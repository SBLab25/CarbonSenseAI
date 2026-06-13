# CarbonSense AI — User Stories and Acceptance Criteria

**Version:** 1.0  
**Competition:** PromptWars Virtual — Google for Developers × H2S | Challenge 3  
**Author:** Sovan Bhakta

---

## Overview

This document defines 8 user stories covering the full CarbonSense AI user journey:

```
Onboarding (Baseline Agent) → Activity Logging (NL or form) → Carbon Analysis (Analyst Agent)
→ Personalized Planning (Planner Agent) → AI Coaching (Coach Agent, streamed)
→ Dashboard (Recharts) → Mission Center (Eco Points)
```

Each story follows: standard format, 3–5 Gherkin acceptance criteria, and 1 edge case.

---

### US-01: New User Onboarding and Baseline Calculation

**Story:** As a new user, I want to complete a guided onboarding flow and receive my estimated carbon footprint so that I have a personalized baseline before I start logging activities.

#### Acceptance Criteria

```gherkin
Scenario: Complete onboarding successfully
  Given I am a new visitor with no UUID in localStorage
  When I navigate to any protected route (/dashboard, /chat, /log, /missions)
  Then I am redirected to /onboarding

Scenario: Step-by-step data collection
  Given I am on the /onboarding page
  When I complete Step 1 (name, country, city, lifestyle_type)
    And I complete Step 2 (primary_transport, weekly_transport_km)
    And I complete Step 3 (diet_type)
    And I complete Step 4 (monthly_electricity_kwh, heating_type)
    And I click "Calculate My Footprint"
  Then a POST /api/v1/users request creates my profile
    And a POST /api/v1/onboarding/baseline request runs the Baseline Agent
    And my UUID is stored in localStorage
    And I am redirected to /dashboard

Scenario: Baseline result displayed
  Given I have just completed onboarding
  When the /dashboard loads for the first time
  Then the Monthly Footprint card shows my baseline_footprint_kg
    And the Category Breakdown pie chart shows transport, energy, food, shopping shares

Scenario: Returning user skips onboarding
  Given I have a valid UUID in localStorage
  When I navigate to /onboarding
  Then I am redirected to /dashboard

Scenario: Required field validation
  Given I am on Step 1 of onboarding
  When I leave the "name" field empty and click "Next"
  Then a validation error is shown and I cannot proceed to Step 2
```

#### Edge Case

```gherkin
Scenario: Baseline Agent Gemini API failure
  Given I have completed all 4 onboarding steps
  When I click "Calculate My Footprint"
    And the Gemini API returns a 500 error
  Then a user-facing error message is displayed: "Unable to calculate baseline. Please try again."
    And the raw Gemini error is NOT shown to the user
    And my user profile is still saved (I can retry baseline without re-entering data)
```

---

### US-02: Natural Language Activity Logging

**Story:** As a user, I want to describe my activities in natural language (e.g., "I drove 25 km to work in my diesel car") so that logging feels effortless without filling complex forms.

#### Acceptance Criteria

```gherkin
Scenario: Parse natural language activity
  Given I am on the /log page with the "Natural Language" tab active
  When I type "I drove 25 km to the office in my diesel car" and click "Log Activity"
  Then a POST /api/v1/activities/parse-nl request is sent
    And Gemini function calling extracts: category=transport, type=car_diesel, amount=25, unit=km
    And the Carbon Engine calculates co2_kg = 4.25 (0.17 * 25)
    And the activity is saved to the database with source='natural_language'
    And the insight cache is invalidated for my user

Scenario: Parsed result confirmation
  Given the NL parsing has completed successfully
  When the response is received
  Then I see a confirmation card showing: "Car (Diesel) — 25 km — 4.25 kg CO₂"
    And the activity appears at the top of my activity history

Scenario: Confidence indicator
  Given I type an ambiguous description like "went somewhere today"
  When parsing completes
  Then the confidence field is "low"
    And a warning is shown: "We weren't sure about this one. Please verify."

Scenario: Rate limiting
  Given I have made 20 NL parse requests in the last minute
  When I submit another NL parse request
  Then the server returns HTTP 429
    And a message is shown: "Too many requests. Please wait before trying again."
```

#### Edge Case

```gherkin
Scenario: Unparseable input
  Given I am on the NL input tab
  When I type "hello world this is not an activity" and click "Log Activity"
  Then Gemini returns a parse with confidence="low" and a generic fallback
    And the user is prompted to use the structured form instead
```

---

### US-03: Structured Form Activity Logging

**Story:** As a user, I want to log activities via a structured form with dropdowns for category, type, and units so that I can accurately record specific activities.

#### Acceptance Criteria

```gherkin
Scenario: Log transport activity via form
  Given I am on the /log page with the "Form" tab active
  When I select category="transport", type="car_petrol", enter amount=20, unit="km"
    And I click "Log Activity"
  Then a POST /api/v1/activities request is sent
    And the Carbon Engine calculates co2_kg = 4.2 (0.21 * 20)
    And the activity is saved with source='form'
    And the insight cache is invalidated

Scenario: Category-specific type options
  Given I am on the form input tab
  When I select category="food"
  Then the "type" dropdown shows: beef, lamb, pork, chicken, fish, dairy, eggs, vegetables, fruits, grains, legumes

Scenario: Immediate CO₂ display
  Given I have submitted a form activity
  When the response is received (within 500ms)
  Then the calculated co2_kg is displayed alongside the activity entry

Scenario: Activity history updated
  Given I have logged a new activity
  When I scroll to the activity history table
  Then the new activity appears at the top of the list
    And React Query has automatically refetched the activities and carbon summary
```

#### Edge Case

```gherkin
Scenario: Zero amount submitted
  Given I am on the form input tab
  When I enter amount=0 and click "Log Activity"
  Then the activity is saved with co2_kg = 0.0
    And no error is thrown (zero-emission logging is valid for tracking)
```

---

### US-04: Triggering the Full Agent Analysis Pipeline

**Story:** As a user, I want to trigger an AI analysis of my carbon footprint so that I receive a personalized assessment of my emission hotspots, a reduction plan, and coaching advice.

#### Acceptance Criteria

```gherkin
Scenario: Trigger full pipeline
  Given I am on the /dashboard page
  When I click the "Analyze My Footprint" button
  Then a POST /api/v1/agents/analyze request is sent
    And the AgentOrchestrator runs: AnalystAgent → PlannerAgent → CoachAgent
    And the Coach Agent response streams via SSE to the chat/dashboard UI
    And the sentinel "data: [PIPELINE_COMPLETE]\n\n" signals completion

Scenario: Cached insights reused
  Given I triggered an analysis 2 hours ago and have not logged any new activities
  When I click "Analyze My Footprint" again
  Then the orchestrator serves cached AnalysisResult and PlanResult
    And only the CoachAgent runs fresh (streaming response)
    And total response time is < 5 seconds

Scenario: Cache invalidated on new activity
  Given I have cached insights from a previous analysis
  When I log a new activity via POST /api/v1/activities
  Then all insight cache rows for my user are set to is_valid = 0
    And the next "Analyze" click runs the full pipeline fresh

Scenario: Rate limit enforcement
  Given I have triggered 3 analyses in the last hour
  When I click "Analyze" a 4th time
  Then the server returns HTTP 429 with message: "Too many analysis requests. Please wait before retrying."
```

#### Edge Case

```gherkin
Scenario: Analyst Agent returns malformed JSON
  Given I trigger the analysis pipeline
  When the AnalystAgent's Gemini function call returns JSON that fails Pydantic validation
  Then the orchestrator catches the validation error
    And streams an SSE error frame: "data: [ERROR] Analysis could not be completed. Please try again.\n\n"
    And the raw error is logged server-side but NOT exposed to the user
```

---

### US-05: Viewing the Insights Dashboard

**Story:** As a user, I want to view a dashboard with charts showing my monthly footprint, category breakdown, trend over time, and goal progress so that I can track whether my actions are making a real difference.

#### Acceptance Criteria

```gherkin
Scenario: Dashboard loads with data
  Given I have logged at least one activity
  When I navigate to /dashboard
  Then I see:
    | Widget                  | Content                                      |
    | Monthly Footprint Card  | total_kg this month, reduction_pct vs baseline |
    | Category Pie Chart      | Transport, Energy, Food, Shopping shares       |
    | Trend Line Chart        | Daily CO₂ totals for selected time range       |
    | Goal Progress Bar       | Current reduction % vs target reduction %      |
    | Eco Points Card         | Total accumulated points with tier label        |

Scenario: Time range selector
  Given I am on the dashboard
  When I switch the trend chart time range from "30 days" to "7 days"
  Then the chart re-renders with data for the last 7 days only
    And a GET /api/v1/carbon/trends/{user_id}?days=7 request is made

Scenario: Chart tooltips
  Given the Trend Line Chart is rendered
  When I hover over a data point
  Then a tooltip shows the exact date and kg CO₂ value for that day

Scenario: Empty state for new users
  Given I have completed onboarding but logged zero activities
  When I navigate to /dashboard
  Then the pie chart and trend chart show an empty state
    And a CTA is displayed: "Log your first activity to see your dashboard come alive"

Scenario: Accessibility compliance
  Given the dashboard is rendered
  Then every chart has an aria-label describing its content
    And all interactive elements are keyboard-navigable
    And color contrast ratios meet WCAG 2.1 AA (≥ 4.5:1)
```

#### Edge Case

```gherkin
Scenario: Sparse data (1-3 data points)
  Given I have logged activities on only 2 out of the last 30 days
  When the trend chart renders
  Then it shows data points for those 2 days connected by a line
    And days without data show 0 kg CO₂ (zero fill, not missing)
```

---

### US-06: Accepting and Completing a Mission

**Story:** As a user, I want to accept sustainability missions generated by the Planner Agent and earn Eco Points upon completion so that I stay motivated through gamified challenges.

#### Acceptance Criteria

```gherkin
Scenario: View available missions
  Given the Planner Agent has generated mission suggestions
  When I navigate to /missions
  Then I see panels for: Available Missions, Active Missions, Completed Missions
    And each mission card shows: title, description, category, eco_points_reward, deadline

Scenario: Accept a mission
  Given I see "Green Commute Challenge" in the Available Missions panel
  When I click "Accept"
  Then a PUT /api/v1/missions/{id}/accept request is sent
    And the mission moves from "Available" to "Active" panel
    And the deadline is set (e.g., 7 days from acceptance)
    And the status changes from 'pending' to 'active'

Scenario: Complete a mission
  Given I have an active mission "Meat-Free Week"
  When I click "Mark Complete"
  Then a POST /api/v1/missions/{id}/complete request is sent
    And Eco Points are awarded: eco_points += eco_points_reward
    And the mission moves to the "Completed" panel
    And the Eco Points balance in the nav header updates without page reload

Scenario: Eco Points tier system
  Given my total eco_points = 520
  Then my tier label displays "Sapling" (0–249: Seedling, 250–749: Sapling, 750–1499: Tree, 1500+: Forest)
```

#### Edge Case

```gherkin
Scenario: Mission expires before completion
  Given I accepted a mission 8 days ago with a 7-day deadline
  When the deadline passes
  Then the mission status is set to 'expired'
    And it moves to a "Past Missions" section (not deleted)
    And no Eco Points are awarded
```

---

### US-07: Chatting with the AI Coach

**Story:** As a user, I want to have a streaming conversation with the AI Coach so that I can ask follow-up questions and deepen my understanding of sustainable living at any time.

#### Acceptance Criteria

```gherkin
Scenario: Send a chat message and receive streamed response
  Given I am on the /chat page
  When I type "Why does meat consumption produce so much carbon?" and press Enter
  Then a POST /api/v1/chat/stream request is sent with my message and conversation history
    And the Coach Agent's response streams token-by-token via SSE
    And each token is appended to the chat display in real time
    And the "[PIPELINE_COMPLETE]" sentinel marks the end of the response

Scenario: Conversation history maintained
  Given I have sent 3 messages in the current session
  When I send a 4th message
  Then the request body includes the last 10 turns of conversation history
    And the Coach Agent references prior context in its response

Scenario: Rate limiting on chat
  Given I have sent 10 chat messages in the last minute
  When I attempt to send an 11th message
  Then the server returns HTTP 429
    And a message is shown: "Please wait a moment before sending another message."

Scenario: First token latency
  Given I send a chat message
  When the server begins processing
  Then the first response token is streamed within 2 seconds
```

#### Edge Case

```gherkin
Scenario: Network disconnection during streaming
  Given the Coach Agent is streaming a response
  When the network connection drops mid-stream
  Then the useStream hook catches the error (not AbortError)
    And displays: "Connection failed. Please try again."
    And the partial response is preserved in the chat (not discarded)
```

---

### US-08: Setting and Tracking a Reduction Goal

**Story:** As a user, I want to set a monthly carbon reduction goal so that the AI Coach can calibrate its recommendations to my specific target and I can track my progress toward it.

#### Acceptance Criteria

```gherkin
Scenario: Default goal set at onboarding
  Given I complete onboarding
  When my user profile is created
  Then a default goal is created: target_reduction_pct = 15%, baseline_kg = my baseline
    And status = 'active'

Scenario: View goal progress on dashboard
  Given I have an active goal of 15% reduction
    And my current monthly footprint is 159.3 kg (baseline was 187.4 kg)
  When I view the dashboard
  Then the Goal Progress Bar shows: 15.0% achieved out of 15.0% target
    And a label indicates: "You've reached your goal!"

Scenario: Update goal target
  Given I am on the dashboard
  When I click "Adjust Goal" and set target_reduction_pct to 20%
  Then a PUT /api/v1/users/{user_id} request updates the target
    And the Goal Progress Bar re-renders with the new target

Scenario: Goal referenced in coaching
  Given I have an active goal of 15% reduction
  When the Coach Agent generates a coaching message
  Then the message references my specific goal percentage and progress toward it

Scenario: Compare against India average
  Given my current monthly footprint is 142.3 kg
  When I view the carbon summary
  Then I see: "Your footprint is 89.4% of the India national average (158 kg/month)"
```

#### Edge Case

```gherkin
Scenario: Goal achieved — Coach celebrates and suggests a stretch goal
  Given my reduction_pct has crossed my target_reduction_pct
  When the Coach Agent runs next
  Then the coaching message acknowledges the achievement
    And suggests a new, higher target based on the Planner Agent's recommended_goal_pct
    And the goal status can be updated to 'achieved' if the user accepts a new goal
```

---

*Document ends.*
