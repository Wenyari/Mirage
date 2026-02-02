import { useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { AlertCircle, ChevronLeft, ChevronRight, Coins, FilePlus, History, Loader2, Lock, Play, Trash2, XCircle } from 'lucide-react';
import { useEffect, useMemo,useRef, useState } from 'react';
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
import { CURRENT_USER_QUERY_KEY } from '@/hooks/useCurrentUser';
import { cn } from '@/lib/utils';
import type { ModelOption, TaskHistoryItem, TaskHistoryResponse, TaskResponse, TaskStatusResponse } from '@/services/tasks';
import { taskService } from '@/services/tasks';

export default function VideoGeneration() {
  const queryClient = useQueryClient();
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('');
  // 首帧和尾帧图片URL (用于支持frames的模型)
  const [firstFrameUrl, setFirstFrameUrl] = useState<string>('');
  const [lastFrameUrl, setLastFrameUrl] = useState<string>('');
  // 单张参考图URL (用于不支持frames的模型)
  const [referenceImageUrl, setReferenceImageUrl] = useState<string[]>([]);
  // 使用 taskParams 存储动态参数
  const [taskParams, setTaskParams] = useState<Record<string, any>>({});
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

  // 检查当前模型是否支持首尾帧
  const supportsFrames = () => {
    const selectedModel = models.find(m => m.key === model);
    return selectedModel?.tags?.includes('frames') || false;
  };

  const supportsMulti = () => {
    const selectedModel = models.find(m => m.key === model);
    return selectedModel?.tags?.includes('multi') || false;
  };

  // 生成图片prefix (XML格式)
  const generateImagePrefix = () => {
    const parts: string[] = [];
    if (firstFrameUrl) {
      parts.push(`首帧图片:<uri>${firstFrameUrl}</uri>`);
    }
    if (lastFrameUrl) {
      parts.push(`尾帧图片:<uri>${lastFrameUrl}</uri>`);
    }
    return parts.length > 0 ? `<prefix>${parts.join('，')}</prefix>` : '';
  };

  // 从完整prompt中剥离prefix，提取用户输入部分
  const stripImagePrefix = (fullPrompt: string): string => {
    // 匹配 <prefix>...</prefix> 标记及其内容
    const prefixPattern = /<prefix>.*?<\/prefix>/;
    return fullPrompt.replace(prefixPattern, '').trim();
  };

  // 从prefix中解析出首帧和尾帧URL
  const parseImagePrefixUrls = (fullPrompt: string): { firstFrame: string; lastFrame: string } => {
    const result = { firstFrame: '', lastFrame: '' };

    // 提取 <prefix>...</prefix> 内容
    const prefixMatch = fullPrompt.match(/<prefix>(.*?)<\/prefix>/);
    if (!prefixMatch) return result;

    const prefixContent = prefixMatch[1];

    // 提取首帧图片
    const firstFrameMatch = prefixContent.match(/首帧图片:<uri>(.*?)<\/uri>/);
    if (firstFrameMatch) {
      result.firstFrame = firstFrameMatch[1];
    }

    // 提取尾帧图片
    const lastFrameMatch = prefixContent.match(/尾帧图片:<uri>(.*?)<\/uri>/);
    if (lastFrameMatch) {
      result.lastFrame = lastFrameMatch[1];
    }

    return result;
  };

  // 检查模型类型
  const getModelType = (modelKey: string) => {
    if (!modelKey) return 'default';
    if (modelKey.includes('sora') || modelKey.includes('Sora')) return 'sora';
    if (modelKey.includes('veo') || modelKey.includes('Veo')) return 'veo';
    return 'default';
  };

  const getPromptPlaceholder = (modelKey: string) => {
    const modelType = getModelType(modelKey);
    switch (modelType) {
      case 'sora':
        return "不支持上传包含真实人物图像，涉及违规不返回积分";
      case 'veo':
        return "veo仅支持英文提示词，若要输入中文，请开启提示词优化自动翻译为英文";
      default:
        return "描述你想生成的内容...";
    }
  };

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

  // 定期刷新历史记录（解决多任务并行时状态不更新的问题）
  useEffect(() => {
    // 每 10 秒刷新一次历史记录
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

            // 刷新历史记录
            refreshHistory();

            // toast 通知（只有当前显示的任务才通知）
            setTaskStatus(currentStatus => {
              if (currentStatus && currentStatus.id === id) {
                if (status.status === 'success') toast.success('视频生成成功！');
                if (status.status === 'failed') toast.error(`生成失败: ${status.fail_reason}`);
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

      let fullPrompt = prompt;
      let inputFileUrls: string[] = [];

      if (supportsFrames()) {
        // 支持frames的模型：使用XML格式的prefix和首尾帧
        const imagePrefix = generateImagePrefix();
        fullPrompt = imagePrefix + prompt;

        // 构建input_file_url数组（顺序：首帧、尾帧）
        if (firstFrameUrl) inputFileUrls.push(firstFrameUrl);
        if (lastFrameUrl) inputFileUrls.push(lastFrameUrl);
      }
      else if (supportsMulti()) {
        if(referenceImageUrl) {
          inputFileUrls = [...referenceImageUrl];
        }
      }
      else {
        // 不支持frames的模型：直接使用原始prompt和单张参考图
        if (referenceImageUrl) {
          inputFileUrls.push(referenceImageUrl[0]);
        }
      }

      const response = await taskService.createTask({
        model,
        prompt: fullPrompt,
        params: taskParams,
        input_file_url: inputFileUrls
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

    // 先清空所有上传的图片
    setFirstFrameUrl('');
    setLastFrameUrl('');
    setReferenceImageUrl([]);

    // 直接从后端拉取该任务的完整详情
    try {
      const statusResponse = await taskService.getTaskStatus(item.id);
      const status = statusResponse as unknown as TaskStatusResponse;

      if (status) {
        setTaskStatus(status);

        // 填充参数到当前面板
        if (status.model) setModel(status.model);

        // 等待model设置完成，然后根据该模型是否支持frames来处理prompt和图片
        setTimeout(() => {
          const modelSupportsFrames = models.find(m => m.key === status.model)?.tags?.includes('frames') || false;

          if (status.prompt) {
            if (modelSupportsFrames) {
              // 支持frames：从prefix中解析图片URL，剥离prefix显示用户输入
              const userPrompt = stripImagePrefix(status.prompt);
              setPrompt(userPrompt);

              const { firstFrame, lastFrame } = parseImagePrefixUrls(status.prompt);
              if (firstFrame) setFirstFrameUrl(firstFrame);
              if (lastFrame) setLastFrameUrl(lastFrame);
            } else {
              // 不支持frames：直接显示原始prompt
              setPrompt(status.prompt);

              // 加载单张参考图
              if ((status as any).input_file_url) {
                const inputFileUrl = (status as any).input_file_url;
                if (Array.isArray(inputFileUrl) && inputFileUrl.length > 0) {
                  setReferenceImageUrl(inputFileUrl);
                } else if (typeof inputFileUrl === 'string') {
                  setReferenceImageUrl([inputFileUrl]);
                }
              }
            }
          }
        }, 100);

        if (status.params) {
          setTimeout(() => {
            setTaskParams(status.params || {});
          }, 100);
        }

        // 若任务仍在运行，确保已启动轮询
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
    setPrompt('');
    setFirstFrameUrl('');
    setLastFrameUrl('');
    setReferenceImageUrl([]);
    setTaskParams({});  // 重置任务参数

    // 重置为默认模型
    const firstAvailable = models.find((m: ModelOption) => m.is_available);
    if (firstAvailable) {
      setModel(firstAvailable.key);
    }

    // 清理所有轮询
    pollingTimersRef.current.forEach(timer => clearInterval(timer));
    pollingTimersRef.current.clear();
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
          defaultParams[paramName] = value; // 使用模型配置中的实际值
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
  // 参数名映射为中文显示
  const paramNameMap: Record<string, string> = {
    'enhance_prompt': '提示词优化',
    'enable_upsample': '分辨率提升',
    'hd': '高清',
    'aspect_ratio': '宽高比',
    'size': '宽高比',
    'image_size': '分辨率',
    'quality': '质量',
    'durations': '时长'
  };

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
        const displayName = paramNameMap[key] || key.replace(/_/g, ' ');
        return (
          <div key={key} className="space-y-2">
            <Label className="capitalize">{displayName}</Label>
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
        const displayName = paramNameMap[key] || key.replace(/_/g, ' ').replace('supported', '');
        return (
          <div key={key} className="flex items-center justify-between rounded-lg border p-4">
            <Label className="cursor-pointer capitalize" htmlFor={`param-${key}`}>
              {displayName}
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
        <div className="flex flex-col border-b">
          <div className="flex items-center justify-between p-4">
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
                        <p className="mt-1 line-clamp-2 text-xs text-[#555]">{stripImagePrefix(item.prompt)}</p>
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
                        {assetMap[m.key] ? (
                          <img src={assetMap[m.key]} alt={m.name} className="size-5 object-contain" />
                        ) : m.icon_url ? (
                          <img src={m.icon_url} alt={m.name} className="size-5 object-contain" />
                        ) : null}
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

            {supportsFrames() ? (
              <>
                <div className="space-y-2">
                  <Label>首帧参考图 (可选；&lt; 2MB)</Label>
                  <ImageUploader
                    value={firstFrameUrl ? [firstFrameUrl] : []}
                    onChange={(urls) => setFirstFrameUrl(urls[0] || '')}
                    maxFiles={1}
                    maxSizeMB={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label>尾帧参考图 (可选；&lt; 2MB)</Label>
                  <ImageUploader
                    value={lastFrameUrl ? [lastFrameUrl] : []}
                    onChange={(urls) => setLastFrameUrl(urls[0] || '')}
                    maxFiles={1}
                    maxSizeMB={2}
                  />
                </div>
              </>
            ) : supportsMulti() ? (
              <div className="space-y-2">
                <Label>参考图 (可选；&lt; 2MB; 最多3张;)</Label>
                <ImageUploader
                  value={referenceImageUrl ? referenceImageUrl : []}
                  onChange={(urls) => setReferenceImageUrl(urls || [])}
                  maxFiles={3}
                  maxSizeMB={2}
                />
              </div>
            ) : (
              <div className="space-y-2">
                <Label>参考图 (可选；&lt; 2MB)</Label>
                <ImageUploader
                  value={referenceImageUrl ? referenceImageUrl : []}
                  onChange={(urls) => setReferenceImageUrl(urls || [])}
                  maxFiles={1}
                  maxSizeMB={2}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label>提示词</Label>
              <Textarea
                placeholder={getPromptPlaceholder(model)}
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
                  生成视频 ({selectedModelInfo?.cost_per_call || 0} 积分)
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
                        <DialogContent className="max-w-2xl">
                          <DialogTitle className="text-xl font-bold">任务详情</DialogTitle>
                          <DialogDescription className="text-muted-foreground">
                            ID: {taskStatus?.id}
                          </DialogDescription>

                          <div className="space-y-4">
                            {/* 模型信息卡片 */}
                            <div className="rounded-lg border bg-muted/30 p-4">
                              <div className="mb-2 flex items-center gap-2">
                                <div className="flex size-8 items-center justify-center rounded-full bg-primary/10">
                                  <Play className="size-4 text-primary" />
                                </div>
                                <h3 className="font-semibold">模型</h3>
                              </div>
                              <p className="ml-10 text-sm">{(taskStatus as any)?.model || selectedModelInfo?.name || '-'}</p>
                            </div>

                            {/* 提示词卡片 */}
                            <div className="rounded-lg border bg-muted/30 p-4">
                              <div className="mb-2 flex items-center gap-2">
                                <div className="flex size-8 items-center justify-center rounded-full bg-blue-500/10">
                                  <svg className="size-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                  </svg>
                                </div>
                                <h3 className="font-semibold">提示词</h3>
                              </div>
                              <div className="ml-10 max-h-40 overflow-y-auto rounded-md bg-background/50 p-3 text-sm leading-relaxed">
                                {stripImagePrefix((taskStatus as any)?.prompt || '-')}
                              </div>
                            </div>

                            {/* 参数卡片 */}
                            {(taskStatus as any)?.params && Object.keys((taskStatus as any).params).length > 0 && (
                              <div className="rounded-lg border bg-muted/30 p-4">
                                <div className="mb-2 flex items-center gap-2">
                                  <div className="flex size-8 items-center justify-center rounded-full bg-purple-500/10">
                                    <svg className="size-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                                    </svg>
                                  </div>
                                  <h3 className="font-semibold">参数配置</h3>
                                </div>
                                <div className="ml-10 grid gap-2">
                                  {Object.entries((taskStatus as any)?.params || {}).map(([key, value]) => (
                                    <div key={key} className="flex items-center justify-between rounded-md bg-background/50 px-3 py-2 text-sm">
                                      <span className="text-muted-foreground">{key}</span>
                                      <span className="font-medium">{String(value)}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* 输入文件卡片 */}
                            {(taskStatus as any)?.input_file_url && (
                              <div className="rounded-lg border bg-muted/30 p-4">
                                <div className="mb-2 flex items-center gap-2">
                                  <div className="flex size-8 items-center justify-center rounded-full bg-green-500/10">
                                    <Play className="size-4 text-green-500" />
                                  </div>
                                  <h3 className="font-semibold">参考图片</h3>
                                </div>
                                <div className="ml-10">
                                  <img
                                    src={(taskStatus as any).input_file_url}
                                    alt="input"
                                    className="max-h-48 rounded-lg border object-contain shadow-sm"
                                  />
                                </div>
                              </div>
                            )}

                            {/* 底部信息 */}
                            <div className="grid grid-cols-2 gap-4">
                              <div className="rounded-lg border bg-muted/30 p-4">
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                  <Coins className="size-4" />
                                  <span>消耗积分</span>
                                </div>
                                <p className="mt-2 text-2xl font-bold text-primary">
                                  {(taskStatus as any)?.cost_points ?? '-'}
                                </p>
                              </div>

                              <div className="rounded-lg border bg-muted/30 p-4">
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                  <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                  <span>创建时间</span>
                                </div>
                                <p className="mt-2 text-sm font-medium">
                                  {(taskStatus as any)?.created_at ? new Date((taskStatus as any).created_at).toLocaleString('zh-CN') : '-'}
                                </p>
                              </div>
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
