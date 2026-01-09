
import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, RefreshCw, Calendar, Gift, Trash2, Edit } from 'lucide-react';
import { toast } from 'sonner';

import {
    getActivities,
    createActivity,
    updateActivity,
    deleteActivity,
    getCheckinConfig,
    updateCheckinConfig,
    type Activity,
    type CheckinConfig
} from '@/services/admin/activities';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';

export default function ActivityManager() {
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState('activities');

    // Activity List State
    const [page] = useState(1);
    const [activityDialogOpen, setActivityDialogOpen] = useState(false);
    const [editingActivity, setEditingActivity] = useState<Activity | null>(null);

    // Queries
    const { data: activitiesData, isLoading: isActivitiesLoading } = useQuery({
        queryKey: ['adminActivities', page],
        queryFn: () => getActivities({ page, size: 20 }),
    });

    const { data: checkinData, isLoading: isCheckinLoading } = useQuery({
        queryKey: ['adminCheckinConfig'],
        queryFn: getCheckinConfig,
    });

    // Mutations
    const createMutation = useMutation({
        mutationFn: createActivity,
        onSuccess: () => {
            toast.success('活动创建成功');
            setActivityDialogOpen(false);
            queryClient.invalidateQueries({ queryKey: ['adminActivities'] });
            setEditingActivity(null);
        },
        onError: (error: any) => toast.error(error.message || '创建失败'),
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: Partial<Activity> }) =>
            updateActivity(id, data),
        onSuccess: () => {
            toast.success('活动更新成功');
            setActivityDialogOpen(false);
            queryClient.invalidateQueries({ queryKey: ['adminActivities'] });
            setEditingActivity(null);
        },
        onError: (error: any) => toast.error(error.message || '更新失败'),
    });

    const deleteMutation = useMutation({
        mutationFn: deleteActivity,
        onSuccess: () => {
            toast.success('活动删除成功');
            queryClient.invalidateQueries({ queryKey: ['adminActivities'] });
        },
        onError: (error: any) => toast.error(error.message || '删除失败，可能仍有相关数据'),
    });

    const updateCheckinMutation = useMutation({
        mutationFn: updateCheckinConfig,
        onSuccess: () => {
            toast.success('签到配置已更新');
            queryClient.invalidateQueries({ queryKey: ['adminCheckinConfig'] });
        },
        onError: (error: any) => toast.error(error.message || '更新失败'),
    });

    // Handlers
    const handleEdit = (activity: Activity) => {
        setEditingActivity(activity);
        setActivityDialogOpen(true);
    };

    const handleDelete = (id: number) => {
        if (confirm('确定要删除该活动吗？此操作不可恢复。')) {
            deleteMutation.mutate(id);
        }
    };

    const handleCreateSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const data = {
            code: formData.get('code') as string,
            name: formData.get('name') as string,
            description: formData.get('description') as string,
            points: Number(formData.get('points')),
            expire_days: formData.get('expire_days') ? Number(formData.get('expire_days')) : null,
            max_claims_per_user: Number(formData.get('max_claims_per_user')),
            required_level: Number(formData.get('required_level')),
            status: formData.get('status') as Activity['status'],
        };

        if (editingActivity) {
            updateMutation.mutate({ id: editingActivity.id, data });
        } else {
            createMutation.mutate(data);
        }
    };

    const handleCheckinSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const configs: Partial<CheckinConfig>[] = [];

        // Assuming 7 days
        for (let i = 1; i <= 7; i++) {
            configs.push({
                day: i,
                points: Number(formData.get(`points-${i}`)),
                is_active: formData.get(`active-${i}`) === 'on'
            });
        }

        updateCheckinMutation.mutate(configs);
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">活动管理</h1>
                <p className="text-muted-foreground">
                    配置营销活动、积分奖励及每日签到规则
                </p>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                    <TabsTrigger value="activities" className="flex items-center gap-2">
                        <Gift className="size-4" />
                        活动列表
                    </TabsTrigger>
                    <TabsTrigger value="checkin" className="flex items-center gap-2">
                        <Calendar className="size-4" />
                        签到配置
                    </TabsTrigger>
                </TabsList>

                {/* Activity List Content */}
                <TabsContent value="activities" className="space-y-4 pt-4">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>营销活动</CardTitle>
                                <CardDescription>管理所有的积分赠送活动</CardDescription>
                            </div>
                            <div className="flex gap-2">
                                <Button variant="outline" size="sm" onClick={() => queryClient.invalidateQueries({ queryKey: ['adminActivities'] })}>
                                    <RefreshCw className="mr-2 size-4" />
                                    刷新
                                </Button>
                                <Dialog open={activityDialogOpen} onOpenChange={(open) => {
                                    setActivityDialogOpen(open);
                                    if (!open) setEditingActivity(null);
                                }}>
                                    <DialogTrigger asChild>
                                        <Button size="sm">
                                            <Plus className="mr-2 size-4" />
                                            创建活动
                                        </Button>
                                    </DialogTrigger>
                                    <DialogContent className="max-w-xl">
                                        <DialogHeader>
                                            <DialogTitle>{editingActivity ? '编辑活动' : '创建新活动'}</DialogTitle>
                                            <DialogDescription>
                                                {editingActivity ? '修改现有活动配置' : '填写表单以创建新的积分活动'}
                                            </DialogDescription>
                                        </DialogHeader>
                                        <form onSubmit={handleCreateSubmit} className="space-y-4">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-2">
                                                    <Label htmlFor="code">活动代码 (Code)</Label>
                                                    <Input id="code" name="code" defaultValue={editingActivity?.code} required disabled={!!editingActivity} placeholder="如：SPRING2024" />
                                                </div>
                                                <div className="space-y-2">
                                                    <Label htmlFor="name">活动名称</Label>
                                                    <Input id="name" name="name" defaultValue={editingActivity?.name} required placeholder="如：新春福利" />
                                                </div>
                                            </div>
                                            <div className="space-y-2">
                                                <Label htmlFor="description">描述</Label>
                                                <Textarea id="description" name="description" defaultValue={editingActivity?.description} placeholder="活动详情描述" />
                                            </div>
                                            <div className="grid grid-cols-3 gap-4">
                                                <div className="space-y-2">
                                                    <Label htmlFor="points">赠送积分</Label>
                                                    <Input id="points" name="points" type="number" defaultValue={editingActivity?.points || 100} required />
                                                </div>
                                                <div className="space-y-2">
                                                    <Label htmlFor="required_level">最低等级要求</Label>
                                                    <Select name="required_level" defaultValue={String(editingActivity?.required_level || 1)}>
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="选择等级" />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem value="1">Lv.1</SelectItem>
                                                            <SelectItem value="2">Lv.2</SelectItem>
                                                            <SelectItem value="3">Lv.3</SelectItem>
                                                            <SelectItem value="4">Lv.4</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                                <div className="space-y-2">
                                                    <Label htmlFor="max_claims_per_user">每人限领次数</Label>
                                                    <Input id="max_claims_per_user" name="max_claims_per_user" type="number" defaultValue={editingActivity?.max_claims_per_user || 1} required />
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-2">
                                                    <Label htmlFor="expire_days">积分有效期(天)</Label>
                                                    <Input id="expire_days" name="expire_days" type="number" defaultValue={editingActivity?.expire_days || 30} placeholder="留空为永久" />
                                                </div>
                                                <div className="space-y-2">
                                                    <Label htmlFor="status">状态</Label>
                                                    <Select name="status" defaultValue={editingActivity?.status || 'active'}>
                                                        <SelectTrigger>
                                                            <SelectValue />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem value="active">进行中</SelectItem>
                                                            <SelectItem value="paused">已暂停</SelectItem>
                                                            <SelectItem value="ended">已结束</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                            </div>
                                            <DialogFooter>
                                                <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                                                    {createMutation.isPending || updateMutation.isPending ? '提交中...' : '保存'}
                                                </Button>
                                            </DialogFooter>
                                        </form>
                                    </DialogContent>
                                </Dialog>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>代码</TableHead>
                                        <TableHead>名称</TableHead>
                                        <TableHead>积分/人</TableHead>
                                        <TableHead>等级要求</TableHead>
                                        <TableHead>有效期</TableHead>
                                        <TableHead>状态</TableHead>
                                        <TableHead className="text-right">操作</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {isActivitiesLoading ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="h-24 text-center">加载中...</TableCell>
                                        </TableRow>
                                    ) : activitiesData?.data?.list?.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={7} className="h-24 text-center">暂无活动</TableCell>
                                        </TableRow>
                                    ) : (
                                        activitiesData?.data?.list?.map((activity: Activity) => (
                                            <TableRow key={activity.id}>
                                                <TableCell className="font-medium">{activity.code}</TableCell>
                                                <TableCell>{activity.name}</TableCell>
                                                <TableCell>{activity.points.toFixed(0)}</TableCell>
                                                <TableCell>Lv.{activity.required_level}</TableCell>
                                                <TableCell>{activity.expire_days ? `${activity.expire_days}天` : '永久'}</TableCell>
                                                <TableCell>
                                                    <Badge variant={activity.status === 'active' ? 'default' : 'secondary'}>
                                                        {activity.status === 'active' ? '进行中' : activity.status === 'paused' ? '暂停' : '已结束'}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="text-right space-x-2">
                                                    <Button variant="ghost" size="icon" onClick={() => handleEdit(activity)}>
                                                        <Edit className="size-4" />
                                                    </Button>
                                                    <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive" onClick={() => handleDelete(activity.id)}>
                                                        <Trash2 className="size-4" />
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Check-in Config Content */}
                <TabsContent value="checkin" className="space-y-4 pt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>签到配置</CardTitle>
                            <CardDescription>设置连续签到 7 天的每日奖励积分</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isCheckinLoading ? (
                                <div className="py-8 text-center text-muted-foreground">加载中...</div>
                            ) : (
                                <form onSubmit={handleCheckinSubmit}>
                                    <div className="space-y-6">
                                        <div className="grid gap-4 md:grid-cols-7">
                                            {(checkinData?.data?.list || Array.from({ length: 7 }, (_, i) => ({ day: i + 1, points: 10, is_active: true }))).map((config: CheckinConfig, index: number) => (
                                                <div key={config.day || index} className="flex flex-col gap-2 rounded-lg border p-4 text-center">
                                                    <div className="font-semibold text-lg text-primary">第 {config.day} 天</div>
                                                    <div className="flex flex-col gap-2">
                                                        <Label htmlFor={`points-${config.day}`} className="sr-only">积分</Label>
                                                        <Input
                                                            id={`points-${config.day}`}
                                                            name={`points-${config.day}`}
                                                            type="number"
                                                            defaultValue={config.points}
                                                            className="text-center"
                                                        />
                                                        <div className="flex items-center justify-center gap-2 pt-2">
                                                            <Switch name={`active-${config.day}`} defaultChecked={config.is_active} id={`active-switch-${config.day}`} />
                                                            <Label htmlFor={`active-switch-${config.day}`} className="text-xs text-muted-foreground">启用</Label>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                        <div className="flex justify-end">
                                            <Button type="submit" disabled={updateCheckinMutation.isPending}>
                                                {updateCheckinMutation.isPending ? '保存中...' : '保存配置'}
                                            </Button>
                                        </div>
                                    </div>
                                </form>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
