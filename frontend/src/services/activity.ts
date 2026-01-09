import api from '@/lib/api';
import type { 
  CheckinStatus, 
  CheckinResult, 
  ActivityListResponse, 
  ClaimResult, 
  MyClaimsResponse 
} from '@/types/activity';

/**
 * 获取签到状态
 */
export async function getCheckinStatus(): Promise<CheckinStatus> {
  const response = await api.get('/activities/checkin/status');
  return response.data;
}

/**
 * 每日签到
 */
export async function checkin(): Promise<CheckinResult> {
  const response = await api.post('/activities/checkin');
  return response.data;
}

/**
 * 获取可用活动列表
 */
export async function getActivities(): Promise<ActivityListResponse> {
  const response = await api.get('/activities/list');
  return response.data;
}

/**
 * 领取活动积分
 */
export async function claimActivity(activityCode: string): Promise<ClaimResult> {
  const response = await api.post('/activities/claim', { activity_code: activityCode });
  return response.data;
}

/**
 * 获取我的活动领取记录
 */
export async function getMyClaims(page = 1, size = 20): Promise<MyClaimsResponse> {
  const response = await api.get('/activities/my-claims', { params: { page, size } });
  return response.data;
}
