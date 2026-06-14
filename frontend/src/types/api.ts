export interface UserCreate {
  id?: string;
  name: string;
  country?: string;
  city?: string;
  lifestyle_type?: string;
  diet_type?: string;
  primary_transport?: string;
  weekly_transport_km?: number;
  monthly_electricity_kwh?: number;
  heating_type?: string;
  monthly_target_reduction_pct?: number;
}

export interface UserResponse {
  user_id: string;
  created_at: string;
}

export interface UserProfile {
  id: string;
  name: string;
  country?: string;
  city?: string;
  lifestyle_type?: string;
  diet_type?: string;
  primary_transport?: string;
  weekly_transport_km: number;
  monthly_electricity_kwh: number;
  heating_type?: string;
  baseline_footprint_kg: number;
  monthly_target_reduction_pct: number;
  eco_points: number;
  created_at: string;
  updated_at: string;
}

export interface ActivityCreate {
  user_id: string;
  category: string;
  type: string;
  amount: number;
  unit: string;
  notes?: string;
}

export interface ActivityResponse {
  activity_id: number;
  user_id: string;
  category: string;
  type: string;
  amount: number;
  unit: string;
  co2_kg: number;
  source: string;
  notes?: string;
  logged_at: string;
}

export interface NLActivityRequest {
  user_id: string;
  description: string;
}

export interface NLParseResponse {
  parsed: {
    category: string;
    type: string;
    amount: number;
    unit: string;
    confidence: string;
  };
  activity_id: number;
  co2_kg: number;
}

export interface CategoryBreakdown {
  kg: number;
  pct: number;
}

export interface CarbonSummary {
  user_id: string;
  period: string;
  total_kg: number;
  baseline_kg: number;
  reduction_pct: number;
  breakdown: Record<string, CategoryBreakdown>;
  vs_india_average_pct: number;
}

export interface CarbonTrend {
  date: string;
  total_kg: number;
}

export interface ProgressReport {
  user_id: string;
  baseline_kg: number;
  current_kg: number;
  reduction_pct: number;
}

export interface FootprintSummary {
  total_kg: number;
  transport_kg: number;
  energy_kg: number;
  food_kg: number;
  shopping_kg: number;
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
  analysis_confidence: string;
}

export interface ReductionStrategy {
  title: string;
  action: string;
  category: string;
  monthly_saving_kg: number;
  difficulty: string;
  timeframe_days: number;
  mission_type?: string | null;
}

export interface PlanResult {
  strategies: ReductionStrategy[];
  total_potential_saving_kg: number;
  recommended_goal_pct: number;
  thirty_day_focus: string;
}

export interface UserContext {
  user_id: string;
  profile: UserProfile;
  baseline_footprint: FootprintSummary;
  current_footprint: FootprintSummary;
  recent_activities: Record<string, any>[];
  active_goal?: Record<string, any> | null;
  progress_pct: number;
}

export interface AnalyzeRequest {
  user_id: string;
}

export interface Mission {
  id: number;
  user_id: string;
  title: string;
  description: string;
  category: string;
  target_reduction_kg?: number;
  eco_points_reward: number;
  status: string;
  created_at: string;
  accepted_at?: string;
  completed_at?: string;
  deadline?: string;
}

export interface MissionCreate {
  user_id: string;
  title: string;
  description: string;
  category: string;
  target_reduction_kg?: number;
  eco_points_reward: number;
}

export interface MissionComplete {
  mission_id: number;
}

export interface ErrorResponse {
  detail: string;
}

export interface ChatRequest {
  user_id: string;
  message: string;
  history: { role: string; content: string }[];
}
