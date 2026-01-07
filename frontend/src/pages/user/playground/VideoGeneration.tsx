import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { AlertCircle, Clock, History, Loader2, Lock, Play, Upload, XCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription,DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import type { ModelOption, TaskHistoryItem, TaskHistoryResponse, TaskResponse, TaskStatusResponse } from '@/services/tasks';
import { taskService } from '@/services/tasks';

export default function VideoGeneration() {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('');
  // 使用 taskParams 存储动态参数
  const [taskParams, setTaskParams] = useState<Record<string, any>>({});
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [history, setHistory] = useState<TaskHistoryItem[]>([]);
  const pollingTimerRef = useRef<number | null>(null);

  // 加载模型列表和历史记录
  useEffect(() => {
    const initData = async () => {
      try {
        setIsLoadingModels(true);
        const [modelsResponse, historyResponse] = await Promise.all([
          taskService.getAvailableModels(),
          taskService.getTaskHistory(1, 20)
        ]);

        const allModels = modelsResponse as unknown as ModelOption[] || [];
        // 筛选包含 'video' 和 'generation' 标签的模型
        const modelsData = allModels.filter(m => 
          m.tags && 
          m.tags.includes('video') && 
          m.tags.includes('generation')
        );

        const historyData = historyResponse as unknown as TaskHistoryResponse;

        setModels(modelsData);
        setHistory(historyData.list || []);

        // 默认选中第一个可用模型
        const firstAvailable = modelsData.find((m: ModelOption) => m.is_available);
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
      const historyResponse = await taskService.getTaskHistory(1, 20);
      setHistory((historyResponse as unknown as TaskHistoryResponse).list || []);
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
        const statusResponse = await taskService.getTaskStatus(id);
        const status = statusResponse as unknown as TaskStatusResponse;
        if (status) {
          setTaskStatus(status);

          // 任务结束，停止轮询并刷新历史
          if (['success', 'failed', 'cancelled'].includes(status.status)) {
            if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
            refreshHistory();

            if (status.status === 'success') toast.success('视频生成成功！');
            if (status.status === 'failed') toast.error(`生成失败: ${status.fail_reason}`);
          }
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
        params: taskParams
      });

      const taskData = response as unknown as TaskResponse;
      if (taskData) {
        setTaskId(taskData.task_id);

        // 初始化状态
        setTaskStatus({
          id: taskData.task_id,
          status: 'pending',
          progress: 0,
          queue_info: {
            user_queue: 'normal',
            position: 1,
            vip_queue: 0,
            normal_queue: 1
          }
        });

        startPolling(taskData.task_id);
      }
      toast.success('任务已提交');
      
      // 延迟刷新历史记录，确保新任务出现
      setTimeout(refreshHistory, 1000);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
      const statusResponse = await taskService.getTaskStatus(taskId);
      const status = statusResponse as unknown as TaskStatusResponse;
      if (status) {
        setTaskStatus(status);
      }
      refreshHistory();
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      toast.error(error.message || '取消失败');
    }
  };

  // 选择历史任务
  const handleSelectTask = async (item: TaskHistoryItem) => {
    setTaskId(item.id);

    // 清理之前的轮询
    if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);

    // 直接从后端拉取该任务的完整详情（包含 prompt/input_file_url/params 等）
    try {
      const statusResponse = await taskService.getTaskStatus(item.id);
      const status = statusResponse as unknown as TaskStatusResponse;

      if (status) {
        setTaskStatus(status);

        // 若任务仍在运行，启动轮询以获取实时进度
        if (['pending', 'processing'].includes(status.status)) {
          startPolling(item.id);
        }
      } else {
        // 回退：使用历史记录的简略信息
        setTaskStatus({
          id: item.id,
          status: item.status,
          progress: item.status === 'success' ? 100 : 0,
          result_url: item.result_url,
        } as TaskStatusResponse);
      }
    } catch (error) {
      console.error('Failed to fetch task status:', error);
      // 回退到历史记录信息
      setTaskStatus({
        id: item.id,
        status: item.status,
        progress: item.status === 'success' ? 100 : 0,
        result_url: item.result_url,
      } as TaskStatusResponse);
    }
  };

  const selectedModelInfo = models.find(m => m.key === model);

  // 初始化动态参数
  useEffect(() => {
    if (selectedModelInfo?.params) {
      const defaultParams: Record<string, any> = {};
      Object.entries(selectedModelInfo.params).forEach(([key, value]) => {
        // 映射参数名: durations -> duration
        const paramName = key === 'durations' ? 'duration' : key;

        if (Array.isArray(value) && value.length > 0) {
          defaultParams[paramName] = value[0];
        } else if (typeof value === 'boolean') {
          defaultParams[paramName] = false; // 默认关闭？或者根据业务逻辑设为 value 本身如果它是默认值
          // 通常 params 定义的是 capability，例如 "hd_supported": true 表示支持 HD。
          // 此时默认值应该设为 false (不开启 HD) 或者 true? 
          // 假设 params 定义的是 capability，那么默认值设为 false 比较安全。
          // 如果 params 定义的是默认值，那就取 value。
          // 根据 "hd_supported": true 这种命名，它只是 capability。所以默认选 false。
          defaultParams[paramName] = false;
        } else {
          // 其他类型直接使用
          defaultParams[paramName] = value;
        }
      });
      setTaskParams(defaultParams);
    } else {
      setTaskParams({});
    }
  }, [model, selectedModelInfo]);

  // 渲染动态参数面板
  const renderDynamicParams = () => {
    if (!selectedModelInfo?.params) return null;

    const entries = Object.entries(selectedModelInfo.params);
    
    // 排序逻辑：布尔值 (Switch) -> 列表 (Select) -> Durations (Special)
    const sortedEntries = entries.sort(([keyA, valueA], [keyB, valueB]) => {
      // 1. Boolean 优先
      const isBoolA = typeof valueA === 'boolean';
      const isBoolB = typeof valueB === 'boolean';
      if (isBoolA && !isBoolB) return -1;
      if (!isBoolA && isBoolB) return 1;

      // 2. Select (非 duration 的数组) 其次
      const isSelectA = Array.isArray(valueA) && keyA !== 'durations';
      const isSelectB = Array.isArray(valueB) && keyB !== 'durations';
      if (isSelectA && !isSelectB) return -1;
      if (!isSelectA && isSelectB) return 1;

      // 3. Durations 最后 (或其他特殊UI)
      const isDurationA = keyA === 'durations';
      const isDurationB = keyB === 'durations';
      if (isDurationA && !isDurationB) return 1; // Duration 放后面
      if (!isDurationA && isDurationB) return -1;

      return 0;
    });

    return sortedEntries.map(([key, value]) => {
       // 参数名映射
       const paramName = key === 'durations' ? 'duration' : key;
       const currentValue = taskParams[paramName];

       // 1. Durations 特殊处理 (保持原有 UI 风格)
       if (key === 'durations' && Array.isArray(value)) {
         return (
          <div key={key} className="space-y-2">
            <Label>时长</Label>
            <div className="flex gap-2">
              {value.map((d: any) => (
                <Button
                  key={d}
                  variant={String(currentValue) === String(d) ? 'default' : 'outline'}
                  onClick={() => setTaskParams(prev => ({ ...prev, [paramName]: d }))}
                  className="flex-1"
                >
                  {d}s
                </Button>
              ))}
            </div>
          </div>
         );
       }

       // 2. 列表 -> Select
       if (Array.isArray(value)) {
         return (
          <div key={key} className="space-y-2">
            <Label className="capitalize">{key.replace(/_/g, ' ')}</Label>
            <Select 
              value={String(currentValue)} 
              onValueChange={(val) => setTaskParams(prev => ({ ...prev, [paramName]: val }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {value.map((opt: any) => (
                  <SelectItem key={String(opt)} value={String(opt)}>
                    {String(opt)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
         );
       }

       // 3. 布尔值 -> Switch
       if (typeof value === 'boolean') {
         if (!value) return null; // 如果 capability 为 false，不显示

         return (
          <div key={key} className="flex items-center justify-between rounded-lg border p-4">
            <Label className="cursor-pointer capitalize" htmlFor={`param-${key}`}>
              {key.replace(/_/g, ' ').replace('supported', '')}
            </Label>
            <Switch
              id={`param-${key}`}
              checked={Boolean(currentValue)}
              onCheckedChange={(checked) => setTaskParams(prev => ({ ...prev, [paramName]: checked }))}
            />
          </div>
         );
       }

       return null;
    });
  };

  return (
    <div className="flex gap-6 px-6 pt-6">
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

          {/* 动态参数面板 */}
          {renderDynamicParams()}

          <Button 
            className="h-12 w-full text-lg" 
            onClick={handleSubmit}
            disabled={isSubmitting || (taskStatus?.status && ['pending', 'processing'].includes(taskStatus.status))}
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
      <div className="flex min-w-[480px] flex-1 flex-col items-start overflow-y-auto rounded-xl border border-dashed bg-muted/30 p-6">
         <div className="mx-auto w-full max-w-3xl space-y-6">
           {!taskStatus ? (
             <div className="flex h-[60vh] w-full flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted/40 bg-transparent py-12">
               <div className="mb-4 inline-block rounded-full bg-muted p-6">
                 <Play className="ml-1 size-12" />
               </div>
               <h3 className="text-lg font-semibold">预览区域</h3>
               <p className="mt-2 text-sm text-muted-foreground">生成的内容将显示在这里。</p>
             </div>
           ) : (
            <>
            {/* 状态展示 */}
            <Card className="p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <h3 className="flex items-center gap-2 text-lg font-semibold">
                      {taskStatus?.status === 'pending' && '排队中...'}
                      {taskStatus?.status === 'processing' && '正在生成...'}
                      {taskStatus?.status === 'success' && '生成成功'}
                      {taskStatus?.status === 'failed' && '生成失败'}
                      {taskStatus?.status === 'cancelled' && '已取消'}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Task ID: {taskStatus?.id}
                    </p>
                  </div>
                  {taskStatus?.status === 'pending' && (
                    <Button variant="destructive" size="sm" onClick={handleCancel}>
                      <XCircle className="mr-2 size-4" />
                      取消任务
                    </Button>
                  )}
                  {/* Details dialog trigger */}
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="ml-2">
                        任务详情
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogTitle>任务详情</DialogTitle>
                      <DialogDescription>
                        以下为该任务的详细信息。
                      </DialogDescription>
                      <div className="mt-4 space-y-3">
                        <div>
                          <div className="text-sm text-muted-foreground">模型</div>
                          <div className="font-medium">{(taskStatus as any)?.model || selectedModelInfo?.name || '-'}</div>
                        </div>
                        <div>
                          <div className="text-sm text-muted-foreground">提示词</div>
                          <div className="whitespace-pre-wrap break-words rounded bg-muted/10 p-3">{(taskStatus as any)?.prompt || '-'}</div>
                        </div>
                        <div>
                          <div className="text-sm text-muted-foreground">参数</div>
                          <div className="font-medium">{JSON.stringify((taskStatus as any)?.params || {})}</div>
                        </div>
                        {(taskStatus as any)?.input_file_url && (
                          <div>
                            <div className="text-sm text-muted-foreground">输入文件</div>
                            <img src={(taskStatus as any).input_file_url} alt="input" className="max-h-48 max-w-full rounded object-contain" />
                          </div>
                        )}
                        <div>
                          <div className="text-sm text-muted-foreground">消耗积分</div>
                          <div className="font-medium">{(taskStatus as any)?.cost_points ?? '-'}</div>
                        </div>
                        <div>
                          <div className="text-sm text-muted-foreground">创建时间</div>
                          <div className="font-medium">{(taskStatus as any)?.created_at || '-'}</div>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>

                {/* 进度条 */}
                {(taskStatus?.status === 'pending' || taskStatus?.status === 'processing') && (
                <div className="space-y-2">
                    <Progress value={taskStatus?.progress || 0} className="h-2" />
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>
                        {taskStatus?.status === 'pending' && (
                          <>
                            当前排在第 <span className="font-bold text-primary">{taskStatus?.queue_info?.position}</span> 位
                            (通道: {taskStatus?.queue_info?.user_queue === 'vip' ? '权益通道' : '普通通道'})
                          </>
                        )}
                        {taskStatus?.status === 'processing' && `生成进度: ${taskStatus?.progress}%`}
                      </span>
                      <span>{taskStatus?.status === 'pending' ? '等待处理' : '处理中'}</span>
                    </div>
                  </div>
                )}

                {/* 失败原因 */}
                {taskStatus?.status === 'failed' && (
                  <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-4 text-destructive">
                    <AlertCircle className="size-5" />
                    <span>{taskStatus?.fail_reason || '未知错误'}</span>
                  </div>
                )}
              </div>
            </Card>

            {/* 视频结果 */}
            {taskStatus?.status === 'success' && taskStatus?.result_url && (
              <div className="w-full overflow-hidden rounded-lg bg-black shadow-xl">
                <video
                  src={taskStatus.result_url}
                  className="h-auto max-h-[65vh] w-full object-contain"
                  controls
                  autoPlay
                  loop
                >
                  <track kind="captions" srcLang="zh" label="中文字幕" default />
                  您的浏览器不支持 HTML5 视频。
                </video>
              </div>
            )}
            </>
           )}
          </div>
      </div>
    </div>
  );
}
