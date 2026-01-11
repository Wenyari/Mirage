import type { CheckinStatus, CheckinResult, ActivityListResponse, ClaimResult, MyClaimsResponse } from '@/types/activity';
/**
 * 获取签到状态
 */
export declare function getCheckinStatus(): Promise<CheckinStatus>;
/**
 * 每日签到
 */
export declare function checkin(): Promise<CheckinResult>;
/**
 * 获取可用活动列表
 */
export declare function getActivities(): Promise<ActivityListResponse>;
/**
 * 领取活动积分
 */
export declare function claimActivity(activityCode: string): Promise<ClaimResult>;
/**
 * 获取我的活动领取记录
 */
export declare function getMyClaims(page?: number, size?: number): Promise<MyClaimsResponse>;
