import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Calendar, CheckCircle, Clock, Gift, Loader2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { CURRENT_USER_QUERY_KEY } from '@/hooks/useCurrentUser';
import { checkin, claimActivity, getActivities, getCheckinStatus } from '@/services/activity';
import { Activity } from '@/types/activity';

// Constants
const DATE_FORMAT = 'yyyy-MM-dd HH:mm';
const MAX_STREAK_DAYS = 7;
const ACTIVITY_STATUS_ACTIVE = 'active';

export default function Events() {
  const { toast } = useToast();
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
      toast({
        title: '签到成功',
        description: `获得 ${data.points} 积分，已连续签到 ${data.consecutive_days} 天！`,
      });
      queryClient.invalidateQueries({ queryKey: ['checkinStatus'] });
      // Invalidate user balance
      queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
    },
    onError: (error: any) => {
      toast({
        variant: 'destructive',
        title: '签到失败',
        description: error.message || '请稍后重试',
      });
    },
  });

  const claimMutation = useMutation({
    mutationFn: claimActivity,
    onSuccess: (data) => {
      toast({
        title: '领取成功',
        description: `获得 ${data.points} 积分！`,
      });
      queryClient.invalidateQueries({ queryKey: ['activities'] });
      queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
    },
    onError: (error: any) => {
      toast({
        variant: 'destructive',
        title: '领取失败',
        description: error.message || '请稍后重试',
      });
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
    <div className="container max-w-5xl py-8">
      <div className="mb-8 space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">活动中心</h1>
        <p className="text-muted-foreground">
          参与每日签到和限时活动，获取更多积分奖励。
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-12">
        {/* Daily Check-in Section */}
        <div className="md:col-span-4">
          <Card className="h-full border-primary/20 bg-gradient-to-b from-primary/5 to-transparent">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="size-5 text-primary" />
                每日签到
              </CardTitle>
              <CardDescription>
                连续签到可获得更多奖励
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-col items-center justify-center space-y-4 py-4">
                <div className="text-center">
                  <div className="text-4xl font-bold text-primary">
                    {status?.consecutive_days || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">连续签到天数</div>
                </div>
                
                <div className="flex gap-1">
                  {Array.from({ length: MAX_STREAK_DAYS }).map((_, i) => {
                    const day = i + 1;
                    const isCompleted = (status?.consecutive_days || 0) >= day;
                    return (
                      <div
                        key={day}
                        className={`size-2 rounded-full ${
                          isCompleted ? 'bg-primary' : 'bg-muted'
                        }`}
                        title={`第 ${day} 天`}
                      />
                    );
                  })}
                </div>

                <div className="text-sm text-muted-foreground">
                   累计签到: <span className="font-medium text-foreground">{status?.total_checkin_days || 0}</span> 天
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button 
                className="w-full" 
                size="lg"
                onClick={handleCheckin}
                disabled={status?.has_checked_today || checkinMutation.isPending}
              >
                {checkinMutation.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
                {status?.has_checked_today ? '今日已签到' : '立即签到'}
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* Activities List Section */}
        <div className="space-y-6 md:col-span-8">
          <h2 className="flex items-center gap-2 text-xl font-semibold">
            <Gift className="size-5" />
            热门活动
          </h2>
          
          <div className="grid gap-4">
            {activityData?.list && activityData.list.length > 0 ? (
              activityData.list.map((activity: Activity) => (
                <Card key={activity.id} className="overflow-hidden">
                  <div className="flex flex-col sm:flex-row">
                    <div className="flex-1 p-6">
                      <div className="mb-2 flex items-center justify-between">
                        <Badge variant="secondary" className="mb-2 sm:mb-0">
                          {activity.code}
                        </Badge>
                        {activity.status === ACTIVITY_STATUS_ACTIVE && (
                           <Badge variant="outline" className="border-green-500 text-green-500">
                             进行中
                           </Badge>
                        )}
                      </div>
                      
                      <h3 className="mb-2 text-lg font-bold">{activity.name}</h3>
                      <p className="mb-4 text-sm text-muted-foreground">
                        {activity.description}
                      </p>

                      <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Gift className="size-3" />
                          <span>奖励: <span className="font-medium text-primary">{activity.points}</span> 积分</span>
                        </div>
                        {activity.end_at && (
                          <div className="flex items-center gap-1">
                            <Clock className="size-3" />
                            <span>结束: {format(new Date(activity.end_at), DATE_FORMAT)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-center bg-muted/50 p-6 sm:w-48 sm:border-l">
                      <Button 
                        onClick={() => handleClaim(activity.code)}
                        disabled={claimMutation.isPending || activity.status !== ACTIVITY_STATUS_ACTIVE}
                      >
                        {claimMutation.isPending && claimMutation.variables === activity.code ? (
                          <Loader2 className="mr-2 size-4 animate-spin" />
                        ) : (
                          <CheckCircle className="mr-2 size-4" />
                        )}
                        领取奖励
                      </Button>
                    </div>
                  </div>
                </Card>
              ))
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                  <Gift className="mb-4 size-12 opacity-20" />
                  <p>暂无可用活动</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
