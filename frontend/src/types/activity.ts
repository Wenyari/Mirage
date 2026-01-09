export interface CheckinStatus {
  has_checked_today: boolean;
  consecutive_days: number;
  total_checkin_days: number;
  last_checkin_at: string | null;
  next_reward: number;
}

export interface CheckinResult {
  points: number;
  consecutive_days: number;
  total_checkin_days: number;
  current_activity_balance: number;
  total_balance: number;
}

export interface Activity {
  id: number;
  code: string;
  name: string;
  description: string;
  points: number;
  expire_days: number | null;
  required_level: number | null;
  start_at: string | null;
  end_at: string | null;
  status: 'active' | 'paused' | 'ended';
}

export interface ClaimResult {
  points: number;
  expire_at: string;
  current_activity_balance: number;
  total_balance: number;
}

export interface MyClaim {
  id: number;
  user_id: number;
  activity_id: number;
  activity_name: string;
  activity_code: string;
  points_granted: number;
  expire_at: string;
  status: 'active' | 'expired' | 'used';
  claimed_at: string;
  expired_at: string | null;
}

export interface ActivityListResponse {
  list: Activity[];
}

export interface MyClaimsResponse {
  list: MyClaim[];
  total: number;
  page: number;
  size: number;
}
