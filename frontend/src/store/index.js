import { create } from 'zustand'

export const useUserStore = create((set) => ({
  token: localStorage.getItem('token') || null,
  userInfo: null,

  setToken: (token) => {
    localStorage.setItem('token', token)
    set({ token })
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ token: null, userInfo: null })
  },
}))
