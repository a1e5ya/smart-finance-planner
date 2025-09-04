import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { auth, signInWithEmail, signInWithGoogle, signUpWithEmail, logOut } from '@/firebase/config'
import { onAuthStateChanged } from 'firebase/auth'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isAuthenticated = computed(() => !!user.value)
  const loading = ref(true)
  
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
  
  // Set up auth state listener
  const initAuth = () => {
    onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // User is signed in
        user.value = {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName,
          photoURL: firebaseUser.photoURL
        }
        
        // Set axios auth header
        const token = await firebaseUser.getIdToken()
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        
      } else {
        // User is signed out
        user.value = null
        delete axios.defaults.headers.common['Authorization']
      }
      loading.value = false
    })
  }
  
  const login = async (email, password) => {
    try {
      const result = await signInWithEmail(email, password)
      return { success: true, user: result.user }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
  
  const loginWithGoogle = async () => {
    try {
      const result = await signInWithGoogle()
      return { success: true, user: result.user }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
  
  const register = async (email, password) => {
    try {
      const result = await signUpWithEmail(email, password)
      return { success: true, user: result.user }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
  
  const logout = async () => {
    try {
      await logOut()
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
  
  return {
    user,
    isAuthenticated,
    loading,
    initAuth,
    login,
    loginWithGoogle,
    register,
    logout
  }
})