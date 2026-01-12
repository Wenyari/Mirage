根据您提供的 Cloudflare Turnstile 官方文档（特别是关于**客户端渲染 (Client-side rendering)** 和 **SPA (Single Page Application)** 的部分），在 Vite + React 中使用的最佳方案是采用 **显式渲染 (Explicit Rendering)** 模式。

文档中明确指出：“显式渲染适用于动态内容、单页应用程序 (SPA)……”。

以下是基于文档内容的最佳实践方案：

### 1. 在 `index.html` 中引入脚本

在 Vite 项目的 `index.html` 文件中引入 Turnstile 脚本。
**关键点**：使用 `render=explicit` 参数，防止脚本加载后立即自动寻找元素渲染，交由 React 代码控制。

```html
<!doctype html>
<html lang="en">
  <head>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit" async defer></script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>

```

### 2. 创建封装组件 (`Turnstile.jsx` / `.tsx`)

利用文档中提到的 `turnstile.render` 和 `turnstile.remove` API，创建一个 React 组件。

这个组件解决了 React 开发中的两个核心问题：

1. **生命周期管理**：在组件挂载时渲染，卸载时销毁（防止内存泄漏）。
2. **React Strict Mode 兼容**：Strict Mode 会导致组件渲染两次，如果不清理，可能会出现重复的 widget。

```jsx
import { useEffect, useRef } from 'react';

const Turnstile = ({ siteKey, onVerify, onError, onExpire }) => {
  const containerRef = useRef(null);
  const widgetIdRef = useRef(null);

  useEffect(() => {
    // 确保 turnstile 对象存在
    if (!window.turnstile) {
      console.error('Turnstile script not loaded');
      return;
    }

    // 清理函数：防止组件重新挂载时产生重复 widget (React Strict Mode 常见问题)
    const cleanup = () => {
      if (widgetIdRef.current) {
        window.turnstile.remove(widgetIdRef.current);
        widgetIdRef.current = null;
      }
    };

    // 初始化渲染
    window.turnstile.ready(() => {
      // 如果容器不存在或已经渲染过，则跳过
      if (!containerRef.current || widgetIdRef.current) return;

      try {
        const id = window.turnstile.render(containerRef.current, {
          sitekey: siteKey, // 传入你的 Site Key
          callback: (token) => {
            // 成功回调，获取 token
            if (onVerify) onVerify(token);
          },
          'error-callback': (err) => {
            if (onError) onError(err);
          },
          'expired-callback': () => {
            if (onExpire) onExpire();
          },
          theme: 'auto', // 可选: light, dark, auto
        });
        widgetIdRef.current = id;
      } catch (e) {
        console.error('Turnstile render error:', e);
      }
    });

    // 组件卸载时调用清理函数
    return cleanup;
  }, [siteKey, onVerify, onError, onExpire]);

  return <div ref={containerRef} />;
};

export default Turnstile;

```

### 3. 在页面中使用

现在你可以在任何表单或页面中像使用普通组件一样使用它。

```jsx
import { useState } from 'react';
import Turnstile from './components/Turnstile';

function LoginForm() {
  const [token, setToken] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    // 将 token 发送到后端进行验证
    const formData = new FormData();
    formData.append('cf-turnstile-response', token);
    // ... fetch calls
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" placeholder="Username" />
      <input type="password" placeholder="Password" />
      
      {/* 插入 Turnstile 组件 */}
      <Turnstile 
        siteKey="你的_SITE_KEY" 
        onVerify={(token) => setToken(token)} 
      />
      
      <button type="submit" disabled={!token}>Login</button>
    </form>
  );
}

```

### 为什么这是最佳方案？

基于您提供的文档 URL，该方案遵循了以下原则：

1. **Explicit Rendering (显式渲染)**：文档明确指出这是 SPA 的推荐方式。它允许 React 控制何时渲染 widget，而不是依赖 HTML 结构扫描。
2. **Widget Lifecycle Management (生命周期管理)**：文档提到了 `turnstile.remove(widgetId)`。在 React 的 `useEffect` cleanup 中调用它至关重要，否则在路由切换或组件更新时，旧的 widget 可能会残留或报错。
3. **turnstile.ready()**：文档强调脚本是异步加载的，使用 `.ready()` 确保在调用 `.render()` 之前 API 已经完全就绪。