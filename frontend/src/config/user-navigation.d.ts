export declare const USER_NAVIGATION: {
    readonly HOME: {
        readonly label: "主页";
        readonly path: "/";
    };
    readonly MODEL_SQUARE: {
        readonly label: "模型广场";
        readonly path: "/models";
    };
    readonly EXPLORE: {
        readonly label: "探索";
        readonly path: "/explore";
        readonly children: {
            readonly PROMPTS: {
                readonly label: "提示词";
                readonly path: "/explore/prompts";
            };
            readonly AGENTS: {
                readonly label: "智能体";
                readonly path: "/explore/agents";
            };
            readonly WORKFLOWS: {
                readonly label: "工作流";
                readonly path: "/explore/workflows";
            };
        };
    };
    readonly PLAYGROUND: {
        readonly label: "体验场";
        readonly path: "/playground";
        readonly children: {
            readonly CHAT: {
                readonly label: "对话";
                readonly path: "/playground/chat";
            };
            readonly VIDEO_GENERATION: {
                readonly label: "生成视频";
                readonly path: "/playground/video";
            };
            readonly IMAGE_GENERATION: {
                readonly label: "生成图片";
                readonly path: "/playground/image";
            };
        };
    };
    readonly SETTINGS: {
        readonly label: "设置";
        readonly path: "/setting";
        readonly children: {
            readonly CREDITS: {
                readonly label: "充值与兑换";
                readonly path: "/setting/credits";
            };
        };
    };
    readonly MORE: {
        readonly label: "更多";
        readonly path: "/more";
        readonly children: {
            readonly UPDATES: {
                readonly label: "最新更新";
                readonly path: "/more/updates";
            };
            readonly EVENTS: {
                readonly label: "活动";
                readonly path: "/more/events";
            };
            readonly COMMUNITY: {
                readonly label: "社群";
                readonly path: "/more/community";
            };
        };
    };
    readonly AUTH: {
        readonly LOGIN: {
            readonly label: "登录";
            readonly path: "/login";
        };
        readonly REGISTER: {
            readonly label: "注册";
            readonly path: "/register";
        };
    };
};
