import { Image as ImageIcon, Video as VideoIcon } from 'lucide-react';
import { useEffect, useMemo,useState } from 'react';

import { Card } from '@/components/ui/card';
import api from '@/lib/api';

const CATEGORY_ORDER = ['text', 'image', 'video', 'other'];
const CATEGORY_LABEL: Record<string, string> = {
  text: '文本模型',
  image: '生图模型',
  video: '视频模型',
  other: '其他模型',
};

function detectCategoryFromTags(tags: string[] = []): string {
  if (!tags || tags.length === 0) return 'other';
  const lower = tags.map((t) => t.toLowerCase());
  if (lower.includes('text') || lower.includes('chat')) return 'text';
  if (lower.includes('image') ||  lower.includes('img')) return 'image';
  if (lower.includes('video')) return 'video';
  return 'other';
}

export default function ModelPlaza() {
  const [models, setModels] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  // preload assets in /src/assets
  const assetMap = useMemo(() => {
    // import all assets as URLs (Vite). cast import.meta to any to access glob in TS
    const modules = (import.meta as any).glob('/src/assets/*.{png,jpg,jpeg,svg}', { eager: true, as: 'url' }) as Record<string, string>;
    const map: Record<string, string> = {};
    for (const p in modules) {
      const filename = p.split('/').pop() || '';
      const name = filename.replace(/\.(png|jpe?g|svg)$/, '');
      map[name] = modules[p];
    }
    return map;
  }, []);

  const fetchModels = async () => {
    setIsLoading(true);
    try {
      const res: any = await api.get('/models/?page=1&size=50');
      const list = res?.data?.list || [];
      setModels(list);
    } catch (e) {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const grouped = useMemo(() => {
    const map: Record<string, any[]> = { text: [], image: [], video: [], other: [] };
    for (const item of models) {
      const tags = item.model?.tags || [];
      const cat = detectCategoryFromTags(tags);
      map[cat] = map[cat] || [];
      map[cat].push(item);
    }
    return map;
  }, [models]);

  return (
    <div className="p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">模型广场</h1>
          <div className="text-sm text-muted-foreground">{models.length} 个模型</div>
        </div>

      <div>
        {isLoading ? (
          <div className="text-muted-foreground">加载中...</div>
        ) : (
          <>
            {CATEGORY_ORDER.map((cat) => {
              const list = grouped[cat] || [];
              if (list.length === 0) return null;
              return (
                <section key={cat} className="mb-8">
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="flex items-center gap-2 text-lg font-medium">
                      {cat === 'image' ? (
                        <ImageIcon className="size-4 text-muted-foreground" />
                      ) : cat === 'video' ? (
                        <VideoIcon className="size-4 text-muted-foreground" />
                      ) : (
                        <span className="text-muted-foreground">▢</span>
                      )}
                      {CATEGORY_LABEL[cat]}
                    </h2>
                    <div className="text-sm text-muted-foreground">{list.length} 个</div>
                  </div>

                  <div className="grid grid-cols-1 justify-center gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                    {list.map((item: any) => {
                      const m = item.model;
                      const cfg = item.config;
                      // small secondary lines
                      const line1 = cfg?.cost_per_call ? `价格：${cfg.cost_per_call} 积分` : '';
                      const line2 = m.description || '';
                      return (
                        <Card
                          key={m.key}
                          className="flex h-28 w-full max-w-[520px] items-center gap-4 overflow-hidden rounded-xl border p-4 transition hover:shadow-md"
                          onClick={() => (window.location.href = `/models/${m.key}`)}
                        >
                          <div className={`flex size-14 shrink-0 items-center justify-center rounded-md text-white ${(m.icon_url || assetMap[m.key]) ? '' : ''}`} style={{ background: (m.icon_url || assetMap[m.key]) ? 'transparent' : (m.color || '#eef2ff') }}>
                            { (m.icon_url || assetMap[m.key]) ? (
                              <img src={m.icon_url || assetMap[m.key]} alt={m.name} className="size-10 object-contain" />
                            ) : (
                              <span className="font-semibold">{(m.name || '').charAt(0).toUpperCase()}</span>
                            )}
                          </div>

                          <div className="min-w-0 flex-1">
                            <div className="truncate font-semibold">{m.name}</div>
                            <div className="mt-1 truncate text-sm text-muted-foreground">{line1}</div>
                            {line2 && (
                              <div
                                className="mt-1 text-sm text-muted-foreground"
                                style={{
                                  display: '-webkit-box',
                                  WebkitLineClamp: 2,
                                  WebkitBoxOrient: 'vertical',
                                  overflow: 'hidden',
                                }}
                              >
                                {line2}
                              </div>
                            )}
                          </div>
                        </Card>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </>
        )}
      </div>
      </div>
    </div>
  );
}


