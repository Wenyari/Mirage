import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { AlertCircle, ChevronLeft, ChevronRight,Clock, History, Loader2, Lock, Play, Upload, XCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ImageUploader } from '@/components/ui/image-uploader';
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
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  // 使用 taskParams 存储动态参数
  const [taskParams, setTaskParams] = useState<Record<string, any>>({});
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [history, setHistory] = useState<TaskHistoryItem[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
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
        params: taskParams,
        input_file_url: uploadedFiles
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

        // 填充参数到当前面板
        if (status.model) setModel(status.model);
        if (status.prompt) setPrompt(status.prompt);
        // 注意：params 设置需要在 model 变化之后生效，或者在 useEffect 中处理
        // 这里直接设置 taskParams，但要小心 useEffect([model]) 的重置逻辑
        // 我们需要一个机制来避免重置，或者在重置后重新覆盖
        // 由于 useEffect 是异步的，这里先设置，如果 useEffect 执行了重置，会覆盖掉
        // 简单的方案：在 setTaskParams 时合并，或者延迟设置
        // 实际上 useEffect 依赖 model，如果 model 变了，会重置 params
        // 我们可以在设置 model 后，setTimeout 设置 params，虽然不太优雅但有效
        if (status.params) {
          // 使用 setTimeout 确保在 useEffect 重置之后执行
          setTimeout(() => {
            setTaskParams(status.params || {});
          }, 100);
        }

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
    // 只有当 taskParams 为空或者与当前模型不匹配时才重置
    // 但为了简化，切换模型时重置是合理的默认行为
    // handleSelectTask 中的 setTimeout 会覆盖这个重置
    if (selectedModelInfo?.params) {
      const defaultParams: Record<string, any> = {};
      Object.entries(selectedModelInfo.params).forEach(([key, value]) => {
        // 映射参数名: durations -> duration
        const paramName = key === 'durations' ? 'duration' : key;

        if (Array.isArray(value) && value.length > 0) {
          defaultParams[paramName] = value[0];
        } else if (typeof value === 'boolean') {
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
  }, [model]); // 移除 selectedModelInfo 依赖，因为它随 model 变化

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

  // 过滤历史记录：只显示当前页面可用模型的记录
  const filteredHistory = history.filter(item => 
    models.some(m => m.key === item.model)
  );

  return (
    <div className="flex h-[calc(100vh-3.5rem)] overflow-hidden">
      {/* 历史记录侧边栏 */}
      <div 
        className={cn(
          "flex flex-col border-r bg-background transition-all duration-300 ease-in-out",
          isHistoryOpen ? "w-[300px]" : "w-0 opacity-0 overflow-hidden"
        )}
      >
        <div className="flex items-center justify-between border-b p-4">
          <div className="flex items-center gap-2">
            <History className="size-5 text-muted-foreground" />
            <div className="flex flex-col">
              <h3 className="font-semibold leading-none">历史记录</h3>
              <span className="text-[10px] text-muted-foreground">最多保存3天！</span>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="size-8" onClick={() => setIsHistoryOpen(false)}>
            <ChevronLeft className="size-4" />
          </Button>
        </div>
        <ScrollArea className="flex-1 p-4">
          <div className="flex flex-col gap-3">
            {(!filteredHistory || filteredHistory.length === 0) ? (
              <div className="py-8 text-center text-sm text-muted-foreground">
                暂无相关记录
              </div>
            ) : (
              filteredHistory.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSelectTask(item)}
                  className={cn(
                    "group relative w-full cursor-pointer overflow-hidden rounded-xl border-[1.5px] p-4 transition-all duration-200 ease-in-out",
                    "bg-[#f2f3f7]",
                    "hover:border-[#1677ff]",
                    taskId === item.id ? "border-[#1677ff]" : "border-[#f2f3f7]"
                  )}
                >
                  <div className="relative z-10 flex gap-3">
                    <div className="pt-1.5">
                      <div className={cn(
                        "size-2.5 rounded-full",
                        item.status === 'success' && "bg-green-500",
                        item.status === 'failed' && "bg-red-500",
                        item.status === 'pending' && "bg-yellow-500",
                        item.status === 'processing' && "bg-blue-500",
                        item.status === 'cancelled' && "bg-gray-400"
                      )} />
                    </div>
                    <div className="flex flex-1 flex-col gap-1 pr-16">
                      <div className="text-sm text-[#333]">
                        <span className="font-semibold text-black">{item.model}</span>
                        <p className="mt-1 line-clamp-2 text-xs text-[#555]">{item.prompt}</p>
                      </div>
                      
                      <p className="text-xs text-[#777]">
                        {formatDistanceToNow(new Date(item.created_at), { addSuffix: true, locale: zhCN })}
                      </p>
                    </div>
                  </div>

                  {item.status === 'success' && (item.thumbnail_url || item.result_url) && (
                    <div className="absolute inset-y-0 right-0 w-28">
                      {item.thumbnail_url ? (
                        <img src={item.thumbnail_url} className="size-full object-cover" alt="" />
                      ) : (
                        <video 
                          src={`${item.result_url}#t=0.1`}
                          className="size-full object-cover" 
                          muted 
                          playsInline
                          preload="metadata"
                        />
                      )}
                      <div className="absolute inset-0 bg-gradient-to-r from-[#f2f3f7] to-transparent" />
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* 展开历史记录按钮 (当侧边栏关闭时显示) */}
      {!isHistoryOpen && (
        <div className="absolute left-4 top-20 z-10">
          <Button
            variant="outline"
            size="icon"
            className="size-8 rounded-full shadow-md"
            onClick={() => setIsHistoryOpen(true)}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}

      {/* 主内容区域 */}
      <div className={cn("flex flex-1 gap-6 overflow-hidden p-6", !isHistoryOpen && "pl-16")}>
        {/* 中间配置区 */}
        <div className="flex w-[400px] shrink-0 flex-col gap-6">
          <h2 className="text-xl font-bold">Generate Video</h2>
          <div className="flex-1 space-y-4 overflow-y-auto pb-6 pl-1 pr-4">
            
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
              <Label>上传参考图 (可选；最多2张, &lt; 1MB)</Label>
              <ImageUploader 
                value={uploadedFiles} 
                onChange={setUploadedFiles} 
                maxFiles={2} 
                maxSizeMB={1} 
              />
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
        <div className="flex min-w-[480px] flex-1 flex-col items-start overflow-y-auto rounded-xl border border-dashed bg-background p-6">
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
    </div>
  );
}
