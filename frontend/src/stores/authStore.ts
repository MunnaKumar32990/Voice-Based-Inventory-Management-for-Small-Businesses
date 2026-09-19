import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email?: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  shopId: string | null;
  shopName: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User, shopId: string, shopName: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      shopId: null,
      shopName: null,
      isAuthenticated: false,
      login: (token, user, shopId, shopName) => 
        set({ token, user, shopId, shopName, isAuthenticated: true }),
      logout: () => 
        set({ token: null, user: null, shopId: null, shopName: null, isAuthenticated: false }),
    }),
    {
      name: 'voicestock-auth',
    }
  )
);
