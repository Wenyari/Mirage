import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Calendar, CheckCircle, Clock, Gift, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import { ActivityCard } from '@/components/activity/ActivityCard';
import { Badge } from '@/components/ui/badge';
import { CURRENT_USER_QUERY_KEY } from '@/hooks/useCurrentUser';
import { checkin, claimActivity, getActivities, getCheckinStatus } from '@/services/activity';
import { Activity } from '@/types/activity';

const ACTIVITY_STATUS_ACTIVE = 'active';

export default function Events() {

  const queryClient = useQueryClient();

  // Queries
  const { data: status, isLoading: isStatusLoading } = useQuery({
    queryKey: ['checkinStatus'],
    queryFn: getCheckinStatus,
  });

  const { data: activityData, isLoading: isActivitiesLoading } = useQuery({
    queryKey: ['activities'],
    queryFn: getActivities,
  });

  // Mutations
  const checkinMutation = useMutation({
    mutationFn: checkin,
    onSuccess: (data) => {
      toast.success(`签到成功！获得 ${data.points} 积分，已连续签到 ${data.consecutive_days} 天！`);
      queryClient.invalidateQueries({ queryKey: ['checkinStatus'] });
      // Invalidate user balance
      queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
    },
    onError: (error: any) => {
      toast.error(error.data.msg || '签到失败，请稍后重试');
    },
  });

  const claimMutation = useMutation({
    mutationFn: claimActivity,
    onSuccess: (data) => {
      toast.success(`领取成功！获得 ${data.points} 积分！`);
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
    },
    onError: (error: any) => {
      toast.error(error.data.msg || '领取失败，请稍后重试');
    },
  });

  const handleCheckin = () => {
    checkinMutation.mutate();
  };

  const handleClaim = (code: string) => {
    claimMutation.mutate(code);
  };

  if (isStatusLoading || isActivitiesLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-14xl container py-12">
      <div className="mb-10 space-y-4 pl-6">
        <h1 className="bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-4xl font-extrabold tracking-tight text-transparent lg:text-5xl">
          活动中心
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          每日签到、限时挑战，赢取海量积分奖励。
        </p>
      </div>

      <div className="my-8 grid gap-6 rounded-2xl border border-muted/50 bg-muted/20 p-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {/* 1. Daily Check-in Card (Always First) */}
        <ActivityCard
          variant="checkin"
          title="每日签到"
          description={`已连续签到 ${status?.consecutive_days || 0} 天。保持连胜，获取更多积分奖励！`}
          icon={Calendar}
          points={10 + (status?.consecutive_days || 0) * 5} // Approximate logic for display
          actionText={status?.has_checked_today ? "今日已签" : "立即签到"}
          onClick={handleCheckin}
          disabled={status?.has_checked_today || checkinMutation.isPending || isStatusLoading}
          status={
            status?.has_checked_today ? (
              <Badge variant="secondary" className="bg-green-100 text-green-700 hover:bg-green-100">
                <CheckCircle className="mr-1 size-3" /> 已完成
              </Badge>
            ) : (
              <Badge className="bg-orange-500 hover:bg-orange-600">
                待领取
              </Badge>
            )
          }
          footer={
            <div className="flex items-center gap-1">
              <span className="font-bold text-orange-500">
                {status?.consecutive_days || 0}
              </span>
              <span>天连签</span>
            </div>
          }
        />

        {/* 2. Other Activities */}
        {activityData?.list?.map((activity: Activity) => (
          <ActivityCard
            key={activity.id}
            title={activity.name}
            description={activity.description}
            icon={Gift}
            points={activity.points}
            actionText="领取奖励"
            onClick={() => handleClaim(activity.code)}
            disabled={claimMutation.isPending || activity.status !== ACTIVITY_STATUS_ACTIVE}
            status={
              activity.status === ACTIVITY_STATUS_ACTIVE ? (
                <Badge variant="outline" className="border-green-500 text-green-500">
                  进行中
                </Badge>
              ) : (
                <Badge variant="secondary">已结束</Badge>
              )
            }
            footer={
              activity.end_at && (
                <div className="flex items-center gap-1">
                  <Clock className="size-3" />
                  <span>{format(new Date(activity.end_at), 'MM-dd HH:mm')} 截止</span>
                </div>
              )
            }
          />
        ))}


      </div>
    </div>
  );
}
