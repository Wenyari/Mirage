import { useEffect, useRef, useState } from 'react';

declare global {
    interface Window {
        initGeetest: (config: any, callback: (captchaObj: any) => void) => void;
    }
}

interface GeetestCaptchaProps {
    onVerify: (params: {
        lot_number: string;
        captcha_output: string;
        pass_token: string;
        gen_time: string;
    }) => void;
    onError?: (error: any) => void;
}

// 这里的 ID 应该从环境变量获取，暂时硬编码或者通过 props 传入
// 为了方便，建议使用环境变量 VITE_GEETEST_ID
const CAPTCHA_ID = '***REMOVED***';

const GeetestCaptcha = ({ onVerify, onError }: GeetestCaptchaProps) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const captchaRef = useRef<any>(null); // 保存 captchaObj 实例
    const [isScriptLoaded, setIsScriptLoaded] = useState(false);

    // 加载 gt4.js 脚本
    useEffect(() => {
        if (window.initGeetest) {
            setIsScriptLoaded(true);
            return;
        }

        const scriptId = 'geetest-gt4-script';
        if (document.getElementById(scriptId)) {
            setIsScriptLoaded(true);
            return;
        }

        console.log('[Geetest] Loading gt4.js...');
        const script = document.createElement('script');
        script.id = scriptId;
        script.src = 'https://static.geetest.com/v4/gt4.js';
        script.async = true;
        script.onload = () => {
            console.log('[Geetest] Script loaded');
            setIsScriptLoaded(true);
        };
        script.onerror = (e) => {
            console.error('[Geetest] Script load failed:', e);
            if (onError) onError(e);
        };
        document.body.appendChild(script);

        return () => {
            // 脚本通常不需要移除
        };
    }, [onError]);

    // 初始化 Geetest
    useEffect(() => {
        if (!isScriptLoaded) {
            return;
        }
        if (captchaRef.current) {
            return;
        }

        // 定义初始化函数
        const init = () => {
            // 检查可能的全局变量名
            const initFn = window.initGeetest || (window as any).initGeetest4;

            if (!initFn) {
                // 调试日志：打印所有相关全局变量，仅在第一次失败时打印
                if (!window['__logged_geetest_debug']) {
                    const keys = Object.keys(window).filter(k => k.toLowerCase().includes('geetest'));
                    console.log('[Geetest] Debug - Available keys:', keys);
                    window['__logged_geetest_debug'] = true;
                }
                return false;
            }
            try {
                initFn(
                    {
                        captchaId: CAPTCHA_ID,
                        product: 'float',
                        language: 'zho',
                        nativeButton: { width: '100%', height: '44px' },
                        rem: 1,
                    },
                    (captchaObj: any) => {
                        captchaRef.current = captchaObj;

                        captchaObj.onSuccess(() => {
                            const result = captchaObj.getValidate();
                            if (result) {
                                onVerify({
                                    lot_number: result.lot_number,
                                    captcha_output: result.captcha_output,
                                    pass_token: result.pass_token,
                                    gen_time: result.gen_time,
                                });
                            }
                        });

                        captchaObj.onError((error: any) => {
                            console.error('[Geetest] Error:', error);
                            if (onError) onError(error);
                        });

                        captchaObj.onReady(() => {
                            console.log('[Geetest] Ready');
                        });

                        if (containerRef.current) {
                            console.log('[Geetest] Appending to container');
                            captchaObj.appendTo(containerRef.current);
                        }
                    }
                );
                return true;
            } catch (e) {
                console.error('[Geetest] Exception during init:', e);
                return false;
            }
        };

        // 尝试立即初始化
        if (init()) return;

        // 如果失败，开启轮询
        console.log('[Geetest] init function not found, polling...');
        const intervalId = setInterval(() => {
            if (init()) {
                clearInterval(intervalId);
                console.log('[Geetest] Initialized via polling');
            }
        }, 500); // 增加间隔到 500ms，减少日志干扰

        // 20秒后停止轮询 (给中国大陆网络更多时间)
        const timeoutId = setTimeout(() => {
            clearInterval(intervalId);
            console.error('[Geetest] Timed out waiting for initGeetest. keys:', Object.keys(window).filter(k => k.toLowerCase().includes('geetest')));
        }, 20000);

        return () => {
            clearInterval(intervalId);
            clearTimeout(timeoutId);
        };
    }, [isScriptLoaded, onVerify, onError]);

    return <div ref={containerRef} className="w-full min-h-[44px]" />;
};

export default GeetestCaptcha;
