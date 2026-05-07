/**
 * DeepTutor Auth Store
 * 
 * 用户认证状态管理
 * 功能：登录、注册、Token 管理、权限检查
 */

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { apiClient, TokenManager } from '../services/api/client'

// ==================== 类型定义 ====================

export interface User {
  id: string;
  name: string;
  email: string;
  roles: string[];
  permissions?: string[];
  disabled: boolean;
  // 用户详细信息
  department?: string;
  position?: string;
  phone?: string;
  description?: string;
  // Back-compat fields
  user_id?: string;
  username?: string;
  avatar?: string;
  role?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}

export interface AuthState {
  // 用户信息
  user: User | null;
  
  // Token (主要用于组件状态，实际存储在 localStorage)
  accessToken: string | null;
  refreshToken: string | null;
  
  // 状态
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  
  // 权限
  permissions: string[];
  
  // Actions
  login: (credentials: LoginCredentials) => Promise<User | null>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
  
  // 权限检查
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  
  // 清理
  clearError: () => void;
  reset: () => void;
  
  // 内部方法：用于响应事件
  _setTokens: (accessToken: string, refreshToken: string) => void;
}

// ==================== Store 实现 ====================

// Cookie helpers for middleware auth
function setAuthCookie(token: string, maxAgeDays = 7): void {
  const expires = new Date(Date.now() + maxAgeDays * 86400 * 1000).toUTCString();
  document.cookie = `access_token=${encodeURIComponent(token)}; path=/; expires=${expires}; SameSite=Lax`;
}
function clearAuthCookie(): void {
  document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax';
}

export const useAuthStore = create<AuthState>()(
  devtools(
    (set, get) => {
      // 从 TokenManager 初始化状态
      const tm = TokenManager.getInstance();
      const accessToken = tm.getAccessToken();
      const refreshToken = tm.getRefreshToken();
      const isAuthenticated = !!accessToken;
      
      // Sync token from localStorage → cookie so middleware sees it on next navigation
      if (typeof window !== 'undefined' && accessToken) {
        setAuthCookie(accessToken);
      }
      
      // 监听全局 Auth 事件
      if (typeof window !== 'undefined') {
        window.addEventListener('auth:token-refreshed', (e: any) => {
            const { accessToken, refreshToken } = e.detail || {};
            if (accessToken && refreshToken) {
                setAuthCookie(accessToken);
                get()._setTokens(accessToken, refreshToken);
            }
        });
        
        window.addEventListener('auth:logout', () => {
            get().logout();
        });
      }

      return {
        // 初始状态 - 仅在存在 token 时进入鉴权加载，避免登录页等公开页面首屏误显示 loading
        user: null,
        accessToken,
        refreshToken,
        isAuthenticated: false,
        loading: isAuthenticated,
        error: null,
        permissions: [],
  
        // 登录
        login: async (credentials: LoginCredentials) => {
          set({ loading: true, error: null });
          try {
            // 调用真实的 API
            const response = await apiClient.post('/auth/login', {
              email: credentials.email,
              password: credentials.password,
            });
            const { access_token, refresh_token, accessToken, refreshToken, user } = response.data;
            const normalizedAccessToken = access_token || accessToken;
            const normalizedRefreshToken = refresh_token || refreshToken;
            if (!normalizedAccessToken) {
              throw new Error('Login response missing access token');
            }
            
            // 转换用户数据格式以兼容现有接口
            // 使用后端返回的 roles 和 permissions
            const userRoles = Array.isArray(user.roles)
              ? user.roles
                  .map((r: any) => (typeof r === 'string' ? r : r?.code || r?.name))
                  .filter(Boolean)
              : [user.role || 'user'];
            const userPermissions = Array.isArray(user.permissions)
              ? user.permissions.map((p: any) => (typeof p === 'string' ? p : p?.code || p?.name)).filter(Boolean)
              : [];
            const primaryRole = user.role || userRoles[0] || 'user';
            
            const normalizedUser: User = {
              id: user.id,
              name: user.name,
              email: user.email,
              roles: userRoles,
              permissions: userPermissions,
              disabled: false,
              avatar: user.avatar,
              user_id: user.user_id || user.id,
              username: user.username || user.email,
              role: primaryRole,
              // 用户详细信息
              department: user.department,
              position: user.position,
              phone: user.phone,
              description: user.description,
            };
            
            // 更新 TokenManager & set middleware cookie
            const tm = TokenManager.getInstance();
            tm.setAccessToken(normalizedAccessToken);
            setAuthCookie(normalizedAccessToken);
            if (normalizedRefreshToken) {
              tm.setRefreshToken(normalizedRefreshToken);
            }
            
            set({
              user: normalizedUser,
              accessToken: normalizedAccessToken,
              refreshToken: normalizedRefreshToken || null,
              isAuthenticated: true,
              loading: false,
              permissions: normalizedUser.permissions || [],
            });
            
            return normalizedUser;
          } catch (error: any) {
            const detail = error.response?.data?.detail;
            const errorMessage = Array.isArray(detail)
              ? detail.map((d: any) => d?.msg || d?.message || String(d)).join('; ')
              : (typeof detail === 'object' && detail !== null
                  ? (detail.message || detail.msg || JSON.stringify(detail))
                  : (detail || error.message || 'Login failed'));
            set({
              error: errorMessage,
              loading: false,
            });
            throw new Error(errorMessage);
          }
        },
        
        // 注册
        register: async (data: RegisterData) => {
          set({ loading: true, error: null });
          try {
            await apiClient.post('/auth/register', {
              email: data.email,
              name: data.name,
              password: data.password,
            });

            set({
              loading: false,
              error: null,
            });
          } catch (error: any) {
            const detail = error.response?.data?.detail;
            const errorMessage = Array.isArray(detail)
              ? detail.map((d: any) => d?.msg || d?.message || String(d)).join('; ')
              : (typeof detail === 'object' && detail !== null
                  ? (detail.message || detail.msg || JSON.stringify(detail))
                  : (detail || error.message || 'Registration failed'));
            set({
              error: errorMessage,
              loading: false,
            });
            throw new Error(errorMessage);
          }
        },
        
        // 登出
        logout: () => {
          const tm = TokenManager.getInstance();
          const refreshToken = tm.getRefreshToken();
          apiClient.post('/auth/logout', refreshToken ? { refreshToken } : {}).catch(() => {});
          tm.clearTokens();
          clearAuthCookie();
          
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            permissions: [],
            error: null,
          });
          
          if (typeof window !== 'undefined') {
            try { sessionStorage.clear(); } catch {}
            try { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); } catch {}
            if (!window.location.pathname.startsWith('/auth')) {
              window.location.replace('/auth');
            } else {
              window.location.reload();
            }
          }
        },
        
        // 检查认证状态
        checkAuth: async () => {
          const tm = TokenManager.getInstance();
          if (!tm.hasToken()) {
            set({ isAuthenticated: false, loading: false });
            return false;
          }

          try {
            // 验证 token 是否有效，调用真实的 API
            const response = await apiClient.get('/auth/me');
            const user = response.data;

            // 转换用户数据格式
            // 使用后端返回的 roles 和 permissions
            const userRoles = Array.isArray(user.roles)
              ? user.roles
                  .map((r: any) => (typeof r === 'string' ? r : r?.code || r?.name))
                  .filter(Boolean)
              : [user.role || 'user'];
            const userPermissions = Array.isArray(user.permissions)
              ? user.permissions.map((p: any) => (typeof p === 'string' ? p : p?.code || p?.name)).filter(Boolean)
              : [];
            const primaryRole = user.role || userRoles[0] || 'user';
            
            const normalizedUser: User = {
              id: user.id,
              name: user.name,
              email: user.email,
              roles: userRoles,
              permissions: userPermissions,
              disabled: false,
              avatar: user.avatar,
              user_id: user.user_id || user.id,
              username: user.username || user.email,
              role: primaryRole,
              // 用户详细信息
              department: user.department,
              position: user.position,
              phone: user.phone,
              description: user.description,
            };

            set({
              user: normalizedUser,
              isAuthenticated: true,
              loading: false,
              permissions: normalizedUser.permissions || [],
            });
            return true;
          } catch (error: any) {
            // 这里的 refresh 逻辑由 apiClient 拦截器处理
            // 如果 apiClient 最终抛出错误，说明 refresh 失败
            // 只有在非401错误时才调用logout，避免重复清理
            if (error.response?.status === 401) {
              // Token 过期或无效，清理状态
              TokenManager.getInstance().clearTokens();
              clearAuthCookie();
              set({
                user: null,
                accessToken: null,
                refreshToken: null,
                isAuthenticated: false,
                permissions: [],
                loading: false,
              });
            } else {
              // 其他错误（网络错误等），保持当前状态但标记为未认证
              set({
                isAuthenticated: false,
                loading: false,
              });
            }
            return false;
          }
        },
        
        // 检查权限
        hasPermission: (permission: string) => {
          const { permissions } = get();
          return permissions.includes('*') || permissions.includes(permission);
        },
        
        // 检查角色
        hasRole: (role: string) => {
          const { user } = get();
          if (!user) return false;
          return user.roles.includes(role);
        },
        
        // 清理错误
        clearError: () => {
          set({ error: null })
        },
        
        // 重置
        reset: () => {
          get().logout()
          set({ error: null, loading: false })
        },
        
        // 内部方法
        _setTokens: (accessToken, refreshToken) => {
            set({ accessToken, refreshToken });
        }
      };
    },
    { name: 'AuthStore' }
  )
)

// ==================== 导出 Hooks ====================

// 便捷 Hook: 获取当前用户
export const useCurrentUser = () => {
  return useAuthStore((state) => state.user);
};

// 便捷 Hook: 检查是否已认证
export const useIsAuthenticated = () => {
  return useAuthStore((state) => state.isAuthenticated);
};

// 便捷 Hook: 权限检查
export const usePermission = (permission: string) => {
  return useAuthStore((state) => state.hasPermission(permission));
};

// 便捷 Hook: 角色检查
export const useRole = (role: string) => {
  return useAuthStore((state) => state.hasRole(role));
};

export default useAuthStore;
