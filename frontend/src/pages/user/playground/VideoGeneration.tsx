import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { AlertCircle, Clock,History, Loader2, Lock, Play, Square, Upload, XCircle } from 'lucide-react';
import { useEffect, useRef,useState } from 'react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { ModelOption, TaskHistoryItem,taskService, TaskStatusResponse } from '@/services/tasks';

export default function VideoGeneration() {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('');
  const [duration, setDuration] = useState('5');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [history, setHistory] = useState<TaskHistoryItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 加载模型列表和历史记录
  useEffect(() => {
    const initData = async () => {
      try {
        setIsLoadingModels(true);
        const [modelsData, historyData] = await Promise.all([
          taskService.getAvailableModels(),
          taskService.getTaskHistory(1, 20)
        ]);
        
        setModels(modelsData || []);
        setHistory(historyData?.list || []);
        
        // 默认选中第一个可用模型
        const firstAvailable = (modelsData || []).find(m => m.is_available);
        if (firstAvailable) {
          setModel(firstAvailable.key);
        }
      } catch (error) {
        console.error('Failed to load initial data:', error);
        toast.error('加载数据失败');
      } finally {
        setIsLoadingModels(false);
      }
    };

    initData();
  }, []);

  // 刷新历史记录
  const refreshHistory = async () => {
    try {
      const historyData = await taskService.getTaskHistory(1, 20);
      setHistory(historyData?.list || []);
    } catch (error) {
      console.error('Failed to refresh history:', error);
    }
  };

  // 清理轮询定时器
  useEffect(() => {
    return () => {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
      }
    };
  }, []);

  // 轮询任务状态
  const startPolling = (id: string) => {
    if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);

    pollingTimerRef.current = setInterval(async () => {
      try {
        const status = await taskService.getTaskStatus(id);
        setTaskStatus(status);

        // 任务结束，停止轮询并刷新历史
        if (['success', 'failed', 'cancelled'].includes(status.status)) {
          if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
          refreshHistory();
          
          if (status.status === 'success') toast.success('视频生成成功！');
          if (status.status === 'failed') toast.error(`生成失败: ${status.fail_reason}`);
        }
      } catch (error) {
        console.error('Failed to poll task status:', error);
      }
    }, 3000); // 3秒轮询一次
  };

  // 提交任务
  const handleSubmit = async () => {
    if (!prompt) {
      toast.error('请输入提示词');
      return;
    }

    if (!model) {
      toast.error('请选择模型');
      return;
    }

    try {
      setIsSubmitting(true);
      setTaskStatus(null);
      
      const response = await taskService.createTask({
        model,
        prompt,
        params: { duration }
      });

      setTaskId(response.task_id);
      
      // 初始化状态
      setTaskStatus({
        id: response.task_id,
        status: 'pending',
        progress: 0,
        queue_info: {
          user_queue: 'normal',
          position: 1,
          vip_queue: 0,
          normal_queue: 1
        }
      });

      startPolling(response.task_id);
      toast.success('任务已提交');
      
      // 延迟刷新历史记录，确保新任务出现
      setTimeout(refreshHistory, 1000);
    } catch (error: any) {
      toast.error(error.message || '提交失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 取消任务
  const handleCancel = async () => {
    if (!taskId) return;

    try {
      await taskService.cancelTask(taskId);
      toast.success('任务已取消');
      // 立即刷新状态
      const status = await taskService.getTaskStatus(taskId);
      setTaskStatus(status);
      refreshHistory();
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    } catch (error: any) {
      toast.error(error.message || '取消失败');
    }
  };

  // 选择历史任务
  const handleSelectTask = (item: TaskHistoryItem) => {
    setTaskId(item.id);
    
    // 如果任务未完成，继续轮询
    if (['pending', 'processing'].includes(item.status)) {
      setTaskStatus({
        id: item.id,
        status: item.status,
        progress: 0, // 历史记录中可能没有实时进度，需要接口补充
        result_url: item.result_url,
      });
      startPolling(item.id);
    } else {
      // 已完成任务，直接显示
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
      setTaskStatus({
        id: item.id,
        status: item.status,
        progress: 100,
        result_url: item.result_url,
      });
    }
  };

  const selectedModelInfo = models.find(m => m.key === model);

  return (
    <div className="flex gap-6 p-6">
      {/* 历史记录列表 */}
      <div className="flex h-[calc(100vh-3.5rem-3rem)] w-[300px] shrink-0 flex-col gap-4 overflow-hidden rounded-xl border bg-muted/20">
        <div className="flex items-center gap-2 border-b p-4">
          <History className="size-5 text-muted-foreground" />
          <h3 className="font-semibold">历史记录</h3>
        </div>
        <ScrollArea className="flex-1 p-4 pt-0">
          <div className="flex flex-col gap-3">
            {(!history || history.length === 0) ? (
              <div className="py-8 text-center text-sm text-muted-foreground">
                暂无生成记录
              </div>
            ) : (
              history.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleSelectTask(item)}
                  className={cn(
                    "flex w-full flex-col gap-2 rounded-lg border p-3 text-left transition-colors hover:bg-muted",
                    taskId === item.id ? "border-primary bg-muted" : "bg-background"
                  )}
                >
                  <div className="flex w-full items-center justify-between">
                    <span className={cn(
                      "rounded-full px-2 py-0.5 text-[10px] font-medium uppercase",
                      item.status === 'success' && "bg-green-100 text-green-700",
                      item.status === 'failed' && "bg-red-100 text-red-700",
                      item.status === 'pending' && "bg-yellow-100 text-yellow-700",
                      item.status === 'processing' && "bg-blue-100 text-blue-700",
                      item.status === 'cancelled' && "bg-gray-100 text-gray-700",
                    )}>
                      {item.status}
                    </span>
                    <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                      <Clock className="size-3" />
                      {formatDistanceToNow(new Date(item.created_at), { addSuffix: true, locale: zhCN })}
                    </span>
                  </div>
                  <p className="line-clamp-2 text-xs text-muted-foreground">
                    {item.prompt}
                  </p>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground/70">
                    <span>{item.model}</span>
                  </div>
                </button>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* 中间配置区 */}
      <div className="flex h-[calc(100vh-3.5rem-3rem)] w-[400px] shrink-0 flex-col gap-6 overflow-y-auto pb-6">
        <div className="space-y-4">
          <h2 className="text-xl font-bold">Generate</h2>
          
          <div className="space-y-2">
            <Label>模型</Label>
            <Select value={model} onValueChange={setModel} disabled={isLoadingModels}>
              <SelectTrigger>
                <SelectValue placeholder={isLoadingModels ? "加载中..." : "选择模型"} />
              </SelectTrigger>
              <SelectContent>
                {models.map((m) => (
                  <SelectItem 
                    key={m.key} 
                    value={m.key} 
                    disabled={!m.is_available}
                    className="flex items-center justify-between"
                  >
                    <div className="flex w-full items-center gap-2">
                      <span>{m.name}</span>
                      {!m.is_available && (
                        <div className="ml-auto flex items-center gap-2">
                          <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                            {m.min_tier}
                          </span>
                          <Lock className="size-3 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedModelInfo && (
              <p className="text-xs text-muted-foreground">
                消耗: {selectedModelInfo.cost_per_call} 积分/次
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label>上传参考图 (可选)</Label>
            <div className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-muted-foreground transition-colors hover:bg-muted/50">
              <Upload className="mb-2 size-8" />
              <span className="text-sm">点击或拖拽上传</span>
            </div>
          </div>

          <div className="space-y-2">
            <Label>提示词</Label>
            <Textarea 
              placeholder="描述你想生成的内容..." 
              className="h-[200px] resize-none"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>时长</Label>
            <div className="flex gap-2">
              <Button 
                variant={duration === '5' ? 'default' : 'outline'} 
                onClick={() => setDuration('5')}
                className="flex-1"
              >
                5s
              </Button>
              <Button 
                variant={duration === '10' ? 'default' : 'outline'} 
                onClick={() => setDuration('10')}
                className="flex-1"
              >
                10s
              </Button>
            </div>
          </div>

          <Button 
            className="h-12 w-full text-lg" 
            onClick={handleSubmit}
            disabled={isSubmitting || (taskStatus && ['pending', 'processing'].includes(taskStatus.status))}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                提交中...
              </>
            ) : (
              <>
                <Play className="mr-2 size-4 fill-current" />
                生成视频 (20 积分)
              </>
            )}
          </Button>
        </div>
      </div>

      {/* 右侧预览区 */}
      <div className="flex flex-1 h-[calc(100vh-3.5rem-3rem)] flex-col items-center justify-center rounded-xl border border-dashed bg-muted/30 p-6 overflow-y-auto">
        {!taskStatus ? (
          <div className="text-center text-muted-foreground">
            <div className="mb-4 inline-block rounded-full bg-muted p-6">
              <Play className="ml-1 size-12" />
            </div>
            <h3 className="text-lg font-medium">预览区域</h3>
            <p>生成的内容将显示在这里</p>
          </div>
        ) : (
          <div className="w-full max-w-3xl space-y-6">
            {/* 状态展示 */}
            <Card className="p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <h3 className="flex items-center gap-2 text-lg font-semibold">
                      {taskStatus.status === 'pending' && '排队中...'}
                      {taskStatus.status === 'processing' && '正在生成...'}
                      {taskStatus.status === 'success' && '生成成功'}
                      {taskStatus.status === 'failed' && '生成失败'}
                      {taskStatus.status === 'cancelled' && '已取消'}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Task ID: {taskStatus.id}
                    </p>
                  </div>
                  {taskStatus.status === 'pending' && (
                    <Button variant="destructive" size="sm" onClick={handleCancel}>
                      <XCircle className="mr-2 size-4" />
                      取消任务
                    </Button>
                  )}
                </div>

                {/* 进度条 */}
                {(taskStatus.status === 'pending' || taskStatus.status === 'processing') && (
                  <div className="space-y-2">
                    <Progress value={taskStatus.progress || 0} className="h-2" />
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>
                        {taskStatus.status === 'pending' && (
                          <>
                            当前排在第 <span className="font-bold text-primary">{taskStatus.queue_info?.position}</span> 位
                            (通道: {taskStatus.queue_info?.user_queue === 'vip' ? '权益通道' : '普通通道'})
                          </>
                        )}
                        {taskStatus.status === 'processing' && `生成进度: ${taskStatus.progress}%`}
                      </span>
                      <span>{taskStatus.status === 'pending' ? '等待处理' : '处理中'}</span>
                    </div>
                  </div>
                )}

                {/* 失败原因 */}
                {taskStatus.status === 'failed' && (
                  <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-4 text-destructive">
                    <AlertCircle className="size-5" />
                    <span>{taskStatus.fail_reason || '未知错误'}</span>
                  </div>
                )}
              </div>
            </Card>

            {/* 视频结果 */}
            {taskStatus.status === 'success' && taskStatus.result_url && (
              <div className="aspect-video overflow-hidden rounded-lg bg-black shadow-xl">
                <video 
                  src={taskStatus.result_url} 
                  className="size-full" 
                  controls
                  autoPlay
                  loop
                >
                  您的浏览器不支持 HTML5 视频。
                </video>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
