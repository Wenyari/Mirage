export const USER_NAVIGATION = {
  HOME: {
    label: '主页',
    path: '/',
  },
  MODEL_SQUARE: {
    label: '模型广场',
    path: '/models',
  },
  EXPLORE: {
    label: '探索',
    path: '/explore',
    children: {
      PROMPTS: {
        label: '提示词',
        path: '/explore/prompts',
      },
      AGENTS: {
        label: '智能体',
        path: '/explore/agents',
      },
      WORKFLOWS: {
        label: '工作流',
        path: '/explore/workflows',
      },
    },
  },
  PLAYGROUND: {
    label: '体验场',
    path: '/playground',
    children: {
      CHAT: {
        label: '对话',
        path: '/playground/chat',
      },
      VIDEO_GENERATION: {
        label: '生成视频',
        path: '/playground/video',
      },
    },
  },
  SETTINGS: {
    label: '设置',
    path: '/setting',
    children: {
      CREDITS: {
        label: '充值与兑换',
        path: '/setting/credits',
      },
    },
  },
  MORE: {
    label: '更多',
    path: '/more',
    children: {
      UPDATES: {
        label: '最新更新',
        path: '/more/updates',
      },
      EVENTS: {
        label: '活动',
        path: '/more/events',
      },
      COMMUNITY: {
        label: '社群',
        path: '/more/community',
      },
    },
  },
  AUTH: {
    LOGIN: {
      label: '登录',
      path: '/login',
    },
    REGISTER: {
      label: '注册',
      path: '/register',
    },
  },
} as const;
