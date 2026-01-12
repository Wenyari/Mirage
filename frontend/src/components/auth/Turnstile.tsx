import { useEffect, useRef, useState } from 'react';

interface TurnstileProps {
  siteKey: string;
  onVerify?: (token: string) => void;
  onError?: (error: any) => void;
  onExpire?: () => void;
  theme?: 'light' | 'dark' | 'auto';
}

declare global {
  interface Window {
    turnstile: {
      render: (container: HTMLElement, options: any) => string;
      remove: (widgetId: string) => void;
    };
  }
}

const Turnstile = ({ siteKey, onVerify, onError, onExpire, theme = 'auto' }: TurnstileProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetIdRef = useRef<string | null>(null);
  const [isScriptLoaded, setIsScriptLoaded] = useState(false);

  // 使用 ref 存储回调函数，避免依赖变化导致重新渲染
  const onVerifyRef = useRef(onVerify);
  const onErrorRef = useRef(onError);
  const onExpireRef = useRef(onExpire);

  // 更新回调函数 ref
  useEffect(() => {
    onVerifyRef.current = onVerify;
    onErrorRef.current = onError;
    onExpireRef.current = onExpire;
  }, [onVerify, onError, onExpire]);

  // 检测脚本加载状态
  useEffect(() => {
    const checkTurnstile = () => {
      if (window.turnstile) {
        setIsScriptLoaded(true);
        return true;
      }
      return false;
    };

    // 立即检查
    if (checkTurnstile()) return;

    // 如果还没加载，定期检查
    const interval = setInterval(() => {
      if (checkTurnstile()) {
        clearInterval(interval);
      }
    }, 100);

    // 超时保护
    const timeout = setTimeout(() => {
      clearInterval(interval);
      console.error('Turnstile script failed to load');
    }, 10000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, []);

  // 渲染 Turnstile widget
  useEffect(() => {
    if (!isScriptLoaded || !containerRef.current) return;

    // 如果已经渲染过，不再重复渲染
    if (widgetIdRef.current) return;

    // 渲染 widget
    try {
      const id = window.turnstile.render(containerRef.current, {
        sitekey: siteKey,
        callback: (token: string) => {
          if (onVerifyRef.current) onVerifyRef.current(token);
        },
        'error-callback': (err: any) => {
          if (onErrorRef.current) onErrorRef.current(err);
        },
        'expired-callback': () => {
          if (onExpireRef.current) onExpireRef.current();
        },
        theme: theme,
      });
      widgetIdRef.current = id;
    } catch (e) {
      console.error('Turnstile render error:', e);
    }

    // 清理函数
    return () => {
      if (widgetIdRef.current && window.turnstile) {
        try {
          window.turnstile.remove(widgetIdRef.current);
        } catch (e) {
          console.error('Error removing turnstile widget:', e);
        }
        widgetIdRef.current = null;
      }
    };
  }, [isScriptLoaded, siteKey, theme]);

  return <div ref={containerRef} />;
};

export default Turnstile;
