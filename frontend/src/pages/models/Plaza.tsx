import { useEffect, useState, useMemo } from 'react';
import api from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Image as ImageIcon, Video as VideoIcon } from 'lucide-react';

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
      const res: any = await api.get('/models?page=1&size=50');
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
      <div className="max-w-6xl mx-auto space-y-6">
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
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-medium flex items-center gap-2">
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

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 justify-center">
                    {list.map((item: any) => {
                      const m = item.model;
                      const cfg = item.config;
                      // small secondary lines
                      const line1 = cfg?.cost_per_call ? `价格：${cfg.cost_per_call} 积分` : '';
                      const line2 = m.description || '';
                      return (
                        <Card
                          key={m.key}
                          className="w-full max-w-[520px] h-28 p-4 rounded-xl border flex items-center gap-4 hover:shadow-md transition overflow-hidden"
                          onClick={() => (window.location.href = `/models/${m.key}`)}
                        >
                          <div className="w-14 h-14 rounded-md flex items-center justify-center text-white shrink-0" style={{ background: m.color || '#eef2ff' }}>
                            { (m.icon_url || assetMap[m.key]) ? (
                              <img src={m.icon_url || assetMap[m.key]} alt={m.name} className="w-10 h-10 object-contain" />
                            ) : (
                              <span className="font-semibold">{(m.name || '').charAt(0).toUpperCase()}</span>
                            )}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="font-semibold truncate">{m.name}</div>
                            <div className="text-sm text-muted-foreground mt-1 truncate">{line1}</div>
                            {line2 && (
                              <div
                                className="text-sm text-muted-foreground mt-1"
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


