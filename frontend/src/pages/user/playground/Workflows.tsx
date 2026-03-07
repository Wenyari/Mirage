import { useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { ChevronLeft, ChevronRight, FilePlus, History, Image as ImageIcon, Loader2, Trash2, XCircle } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ImageUploader } from '@/components/ui/image-uploader';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { CURRENT_USER_QUERY_KEY } from '@/hooks/useCurrentUser';
import { cn } from '@/lib/utils';
import type { ModelOption, TaskHistoryItem, TaskHistoryResponse, TaskResponse, TaskStatusResponse } from '@/services/tasks';
import { taskService } from '@/services/tasks';

export default function Workflows() {
  const queryClient = useQueryClient();
  const [model, setModel] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [history, setHistory] = useState<TaskHistoryItem[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
  const pollingTimersRef = useRef<Map<string, number>>(new Map());
  const historyRefreshTimerRef = useRef<number | null>(null);

  // 加载 assets 目录下的图片
  const assetMap = useMemo(() => {
    const modules = (import.meta as any).glob('/src/assets/*.{png,jpg,jpeg,svg}', { eager: true, as: 'url' }) as Record<string, string>;
    const map: Record<string, string> = {};
    for (const p in modules) {
      const filename = p.split('/').pop() || '';
      const name = filename.replace(/\.(png|jpe?g|svg)$/, '');
      map[name] = modules[p];
    }
    return map;
  }, []);

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
        // 筛选包含 'image' 和 'generation' 标签的模型
        const modelsData = allModels.filter((m: ModelOption) =>
          m.tags &&
          m.tags.includes('workflow') &&
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
      // 清理所有轮询定时器
      pollingTimersRef.current.forEach((timerId) => {
        clearInterval(timerId);
      });
      pollingTimersRef.current.clear();

      if (historyRefreshTimerRef.current) {
        clearInterval(historyRefreshTimerRef.current);
      }
    };
  }, []);

  // 定期刷新历史记录
  useEffect(() => {
    historyRefreshTimerRef.current = setInterval(() => {
      refreshHistory();
    }, 10000) as any;

    return () => {
      if (historyRefreshTimerRef.current) {
        clearInterval(historyRefreshTimerRef.current);
      }
    };
  }, []);

  // 轮询任务状态
  const startPolling = (id: string) => {
    // 如果已经在轮询，不重复启动
    if (pollingTimersRef.current.has(id)) {
      return;
    }

    const timerId = setInterval(async () => {
      try {
        const statusResponse = await taskService.getTaskStatus(id);
        const status = statusResponse as unknown as TaskStatusResponse;
        if (status) {
          // 直接更新状态，如果是当前任务则显示
          setTaskStatus(prevStatus => {
            // 如果当前显示的是该任务，则更新
            if (!prevStatus || prevStatus.id === id) {
              return status;
            }
            // 否则保持不变
            return prevStatus;
          });

          // 任务结束，停止该任务的轮询
          if (['success', 'failed', 'cancelled'].includes(status.status)) {
            const timer = pollingTimersRef.current.get(id);
            if (timer) {
              clearInterval(timer);
              pollingTimersRef.current.delete(id);
            }

            refreshHistory();

            // toast 通知（只有当前显示的任务才通知）
            setTaskStatus(currentStatus => {
              if (currentStatus && currentStatus.id === id) {
                if (status.status === 'success') toast.success('图片处理成功！');
                if (status.status === 'failed') toast.error(`处理失败: ${status.fail_reason}`);
              }
              return currentStatus;
            });
          }
        }
      } catch (error) {
        console.error('Failed to poll task status:', error);
      }
    }, 3000);

    pollingTimersRef.current.set(id, timerId as any);
  };

  // 停止轮询某个任务
  const stopPolling = (id: string) => {
    const timer = pollingTimersRef.current.get(id);
    if (timer) {
      clearInterval(timer);
      pollingTimersRef.current.delete(id);
    }
  };

  // 删除任务
  const handleDeleteTask = async (e: React.MouseEvent, historyItem: TaskHistoryItem) => {
    e.stopPropagation();

    try {
      await taskService.deleteTask(historyItem.id);
      toast.success('删除成功');

      // If deleting currently viewed task, clear view
      if (historyItem.id === taskId) {
        setTaskId(null);
        setTaskStatus(null);
      }

      refreshHistory();
    } catch (error: any) {
      console.error('Delete failed:', error);
      toast.error(error.data?.msg || '删除失败');
    }
  };

  const selectedModelInfo = models.find(m => m.key === model);

  // 提交任务
  const handleSubmit = async () => {
    if (!model) {
      toast.error('请选择模型');
      return;
    }

    if (uploadedFiles.length === 0) {
      toast.error('请上传图片');
      return;
    }

    try {
      setIsSubmitting(true);
      setTaskStatus(null);

      const response = await taskService.createTask({
        model,
        prompt: 'Process this image',
        params: {},
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

      // Invalidate user balance
      queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      toast.error((error.data ? error.data.msg : error.message) || '提交失败');
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
      // 停止该任务的轮询
      stopPolling(taskId);

      // Invalidate user balance to reflect refund
      queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      toast.error((error.data ? error.data.msg : error.message) || '取消失败');
    }
  };

  // 选择历史任务
  const handleSelectTask = async (item: TaskHistoryItem) => {
    setTaskId(item.id);

    // 先清空当前上传的图片
    setUploadedFiles([]);

    try {
      const statusResponse = await taskService.getTaskStatus(item.id);
      const status = statusResponse as unknown as TaskStatusResponse;

      if (status) {
        setTaskStatus(status);

        if (status.model) setModel(status.model);

        // 加载任务的上传图片
        if ((status as any).input_file_url) {
          const inputFileUrl = (status as any).input_file_url;
          if (Array.isArray(inputFileUrl)) {
            setUploadedFiles(inputFileUrl);
          } else if (typeof inputFileUrl === 'string') {
            setUploadedFiles([inputFileUrl]);
          }
        }

        if (['pending', 'processing'].includes(status.status)) {
          startPolling(item.id);
        }
      } else {
        setTaskStatus({
          id: item.id,
          status: item.status,
          progress: item.status === 'success' ? 100 : 0,
          result_url: item.result_url,
        } as TaskStatusResponse);
      }
    } catch (error) {
      console.error('Failed to fetch task status:', error);
      setTaskStatus({
        id: item.id,
        status: item.status,
        progress: item.status === 'success' ? 100 : 0,
        result_url: item.result_url,
      } as TaskStatusResponse);
    }
  };

  // 创建新任务
  const handleNewTask = () => {
    // 清除选中状态
    setTaskId(null);
    setTaskStatus(null);

    // 重置表单
    setUploadedFiles([]);

    // 重置为默认模型
    const firstAvailable = models.find((m: ModelOption) => m.is_available);
    if (firstAvailable) {
      setModel(firstAvailable.key);
    }

    // 清理所有轮询
    pollingTimersRef.current.forEach(timer => clearInterval(timer));
    pollingTimersRef.current.clear();
  };

  // 过滤历史记录：只显示当前页面可用模型的记录
  const filteredHistory = history.filter(item =>
    models.some(m => m.key === item.model)
  );

  const HistoryList = () => (
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
            {/* Delete Button */}
            {['success', 'failed', 'cancelled'].includes(item.status) && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-2 top-2 z-20 size-6 rounded-md bg-white opacity-0 shadow-sm transition-opacity hover:bg-red-100 group-hover:opacity-100"
                onClick={(e) => handleDeleteTask(e, item)}
              >
                <Trash2 className="size-3 text-red-500" />
              </Button>
            )}

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
                <img src={item.thumbnail_url || item.result_url} className="size-full object-cover" alt="" />
                <div className="absolute inset-0 bg-gradient-to-r from-[#f2f3f7] to-transparent" />
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );

  return (
    <div className="flex flex-col h-[calc(100dvh-3.5rem)] md:h-[calc(100vh-3.5rem)] md:flex-row overflow-hidden relative">
      {/* Mobile/iPad History Sheet Button (visible on small screens) */}
      <div className="lg:hidden absolute top-4 right-4 z-40">
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2 bg-background/80 backdrop-blur-sm shadow-sm">
              <History className="size-4" />
              历史记录
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[85vw] sm:w-[350px] p-0 flex flex-col">
            <div className="flex flex-col border-b">
              <div className="flex items-center justify-between p-4">
                <div className="flex items-center gap-2">
                  <History className="size-5 text-muted-foreground" />
                  <div className="flex flex-col">
                    <h3 className="font-semibold leading-none">历史记录</h3>
                    <span className="text-[10px] text-muted-foreground">最多保存3天！</span>
                  </div>
                </div>
              </div>
              <div className="px-4 pb-3">
                <Button variant="outline" className="w-full" onClick={handleNewTask}>
                  <FilePlus className="mr-2 size-4" />
                  New
                </Button>
              </div>
            </div>
            <ScrollArea className="flex-1 p-4">
              <HistoryList />
            </ScrollArea>
          </SheetContent>
        </Sheet>
      </div>

      {/* 历史记录侧边栏 - Desktop Only (lg and above) */}
      <div
        className={cn(
          "hidden lg:flex flex-col border-r bg-background transition-all duration-300 ease-in-out",
          isHistoryOpen ? "w-[280px] xl:w-[300px]" : "w-0 opacity-0 overflow-hidden"
        )}
      >
        <div className="flex flex-col border-b">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center gap-2">
              <History className="size-5 text-muted-foreground" />
              <div className="flex flex-col">
                <h3 className="font-semibold leading-none">历史记录</h3>
                <span className="text-[10px] text-muted-foreground">最多保存3天！图片仅1天，请尽快保存！</span>
              </div>
            </div>
            <Button variant="ghost" size="icon" className="size-8" onClick={() => setIsHistoryOpen(false)}>
              <ChevronLeft className="size-4" />
            </Button>
          </div>
          <div className="px-4 pb-3">
            <Button
              variant="outline"
              className="w-full"
              onClick={handleNewTask}
            >
              <FilePlus className="mr-2 size-4" />
              New
            </Button>
          </div>
        </div>
        <ScrollArea className="flex-1 p-4">
          <HistoryList />
        </ScrollArea>
      </div>

      {/* 展开历史记录按钮 (当侧边栏关闭时显示) - Desktop Only */}
      {!isHistoryOpen && (
        <div className="absolute left-4 top-20 z-10 hidden lg:block">
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
      <div className={cn(
        "flex flex-1 flex-col md:flex-row lg:flex-row gap-4 md:gap-6 overflow-y-auto md:overflow-hidden p-4 md:p-6",
        !isHistoryOpen && "lg:pl-16"
      )}>
        {/* 中间配置区 - iPad/桌面适配 */}
        <div className="flex w-full md:w-[340px] lg:w-[360px] xl:w-[400px] shrink-0 flex-col gap-4 md:gap-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">图片处理工作流</h2>
          </div>

          <div className="flex-1 space-y-3 md:space-y-4 overflow-visible md:overflow-y-auto pb-4 md:pb-6 pl-1 pr-1 md:pr-2 lg:pr-4">
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
                        {assetMap[m.key] ? (
                          <img src={assetMap[m.key]} alt={m.name} className="size-5 object-contain" />
                        ) : m.icon_url ? (
                          <img src={m.icon_url} alt={m.name} className="size-5 object-contain" />
                        ) : null}
                        <span>{m.name}</span>
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

            {/* 上传图片 */}
            <div className="space-y-2">
              <Label>上传图片</Label>
              <ImageUploader
                value={uploadedFiles}
                onChange={setUploadedFiles}
                maxFiles={1}
                maxSizeMB={10}
              />
              <p className="text-xs text-muted-foreground">
                支持 JPG、PNG 格式，最大 10MB
              </p>
            </div>

            {/* 提交按钮 */}
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
                  <ImageIcon className="mr-2 size-4 fill-current" />
                  开始处理 ({selectedModelInfo?.cost_per_call || 0} 积分)
                </>
              )}
            </Button>
          </div>
        </div>

        {/* 右侧预览区 - iPad/桌面适配 */}
        <div className="flex w-full md:min-w-[400px] lg:min-w-[480px] flex-1 flex-col items-start overflow-visible md:overflow-y-auto rounded-xl border border-dashed bg-background p-4 md:p-6 min-h-[300px]">
          <div className="mx-auto w-full max-w-3xl space-y-6">
            {!taskStatus ? (
              <div className="flex h-[60vh] w-full flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted/40 bg-transparent py-12">
                <div className="mb-4 inline-block rounded-full bg-muted p-6">
                  <ImageIcon className="ml-1 size-12" />
                </div>
                <h3 className="text-lg font-semibold">预览区域</h3>
                <p className="mt-2 text-sm text-muted-foreground">处理后的图片将显示在这里。</p>
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
                          {taskStatus?.status === 'processing' && '正在处理...'}
                          {taskStatus?.status === 'success' && '处理成功'}
                          {taskStatus?.status === 'failed' && '处理失败'}
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
                      {taskStatus?.status === 'success' && (
                        <Button variant="outline" size="sm" onClick={handleNewTask}>
                          重新开始
                        </Button>
                      )}
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
                            {taskStatus?.status === 'processing' && `处理进度: ${taskStatus?.progress}%`}
                          </span>
                          <span>{taskStatus?.status === 'pending' ? '等待处理' : '处理中'}</span>
                        </div>
                      </div>
                    )}

                    {/* 失败原因 */}
                    {taskStatus?.status === 'failed' && (
                      <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-4 text-destructive">
                        <XCircle className="size-5" />
                        <span>{taskStatus?.fail_reason || '未知错误'}</span>
                      </div>
                    )}

                    {/* 取消原因 */}
                    {taskStatus?.status === 'cancelled' && (
                      <div className="flex items-center gap-2 rounded-md bg-muted/50 p-4 text-muted-foreground">
                        <XCircle className="size-5" />
                        <span>任务已取消</span>
                      </div>
                    )}
                  </div>
                </Card>

                {/* 图片结果 */}
                {taskStatus?.status === 'success' && taskStatus?.result_url && (
                  <div className="w-full overflow-hidden rounded-lg bg-black/5 shadow-xl">
                    <img
                      src={taskStatus.result_url}
                      alt="处理结果"
                      className="h-auto max-h-[65vh] w-full object-contain"
                    />
                  </div>
                )}

                {/* 成功状态下的操作按钮 */}
                {taskStatus?.status === 'success' && taskStatus?.result_url && (
                  <div className="flex w-full gap-3">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = taskStatus.result_url!;
                        link.download = 'processed-image.jpg';
                        link.click();
                      }}
                    >
                      <svg
                        className="mr-2 size-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      下载图片
                    </Button>
                    <Button className="flex-1" onClick={handleNewTask}>
                      <svg
                        className="mr-2 size-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                      </svg>
                      重新处理
                    </Button>
                  </div>
                )}

                {/* 失败状态下的重新开始按钮 */}
                {taskStatus?.status === 'failed' && (
                  <Button className="w-full" onClick={handleNewTask}>
                    重新开始
                  </Button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
