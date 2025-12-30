interface AdminUser {
    id: number;
    email: string;
    name: string;
    role: 'admin';
    avatar?: string;
}
interface AuthState {
    token: string | null;
    user: AdminUser | null;
    isAuthenticated: boolean;
    login: (token: string, user: AdminUser) => void;
    logout: () => void;
    setUser: (user: AdminUser) => void;
}
export declare const useAuthStore: import("zustand").UseBoundStore<Omit<import("zustand").StoreApi<AuthState>, "setState" | "persist"> & {
    setState(partial: AuthState | Partial<AuthState> | ((state: AuthState) => AuthState | Partial<AuthState>), replace?: false | undefined): unknown;
    setState(state: AuthState | ((state: AuthState) => AuthState), replace: true): unknown;
    persist: {
        setOptions: (options: Partial<import("zustand/middleware").PersistOptions<AuthState, {
            token: string | null;
            user: AdminUser | null;
            isAuthenticated: boolean;
        }, unknown>>) => void;
        clearStorage: () => void;
        rehydrate: () => Promise<void> | void;
        hasHydrated: () => boolean;
        onHydrate: (fn: (state: AuthState) => void) => () => void;
        onFinishHydration: (fn: (state: AuthState) => void) => () => void;
        getOptions: () => Partial<import("zustand/middleware").PersistOptions<AuthState, {
            token: string | null;
            user: AdminUser | null;
            isAuthenticated: boolean;
        }, unknown>>;
    };
}>;
export {};
