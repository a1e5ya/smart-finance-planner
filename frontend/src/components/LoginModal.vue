<template>
  <div v-if="showModal" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <h2>{{ isLogin ? 'Sign In' : 'Sign Up' }}</h2>
      
      <!-- Google Sign-In Button -->
      <button @click="handleGoogleAuth" class="google-btn">
        🔍 Continue with Google
      </button>
      
      <div class="divider">or</div>
      
      <!-- Email/Password Form -->
      <form @submit.prevent="handleEmailAuth">
        <input
          v-model="email"
          type="email"
          placeholder="Email"
          required
          class="auth-input"
        />
        <input
          v-model="password"
          type="password"
          placeholder="Password"
          required
          class="auth-input"
        />
        
        <button type="submit" class="auth-btn" :disabled="loading">
          {{ loading ? 'Loading...' : (isLogin ? 'Sign In' : 'Sign Up') }}
        </button>
      </form>
      
      <!-- Toggle Login/Register -->
      <p class="toggle-text">
        {{ isLogin ? "Don't have an account?" : "Already have an account?" }}
        <button @click="isLogin = !isLogin" class="toggle-btn">
          {{ isLogin ? 'Sign Up' : 'Sign In' }}
        </button>
      </p>
      
      <!-- Error Message -->
      <div v-if="error" class="error-message">{{ error }}</div>
      
      <!-- Close Button -->
      <button @click="closeModal" class="close-btn">×</button>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'LoginModal',
  props: {
    showModal: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const authStore = useAuthStore()
    
    const isLogin = ref(true)
    const email = ref('')
    const password = ref('')
    const error = ref('')
    const loading = ref(false)
    
    const closeModal = () => {
      emit('close')
      // Reset form
      email.value = ''
      password.value = ''
      error.value = ''
      loading.value = false
    }
    
    const handleGoogleAuth = async () => {
      loading.value = true
      error.value = ''
      
      try {
        const result = await authStore.loginWithGoogle()
        if (result.success) {
          closeModal()
        } else {
          error.value = result.error
        }
      } catch (err) {
        error.value = err.message
      }
      
      loading.value = false
    }
    
    const handleEmailAuth = async () => {
      loading.value = true
      error.value = ''
      
      try {
        let result
        if (isLogin.value) {
          result = await authStore.login(email.value, password.value)
        } else {
          result = await authStore.register(email.value, password.value)
        }
        
        if (result.success) {
          closeModal()
        } else {
          error.value = result.error
        }
      } catch (err) {
        error.value = err.message
      }
      
      loading.value = false
    }
    
    return {
      isLogin,
      email,
      password,
      error,
      loading,
      closeModal,
      handleGoogleAuth,
      handleEmailAuth
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.8));
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 30px;
  width: 90%;
  max-width: 400px;
  position: relative;
  box-shadow: 0 20px 40px rgba(139, 69, 19, 0.2);
}

.modal-content h2 {
  text-align: center;
  margin-bottom: 20px;
  color: rgba(139, 69, 19, 1);
  font-weight: 600;
}

.google-btn {
  width: 100%;
  padding: 12px;
  background: white;
  border: 2px solid #ddd;
  border-radius: 16px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 15px;
}

.google-btn:hover {
  border-color: #4285f4;
  box-shadow: 0 4px 12px rgba(66, 133, 244, 0.2);
}

.divider {
  text-align: center;
  margin: 15px 0;
  color: rgba(139, 69, 19, 0.6);
  position: relative;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: rgba(139, 69, 19, 0.2);
  z-index: -1;
}

.divider {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.8));
  padding: 0 15px;
}

.auth-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid rgba(139, 69, 19, 0.2);
  border-radius: 16px;
  margin-bottom: 15px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
}

.auth-input:focus {
  outline: none;
  border-color: rgba(139, 69, 19, 0.5);
  background: white;
}

.auth-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #8b4513, #a0522d);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 15px;
}

.auth-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #a0522d, #cd853f);
  transform: translateY(-1px);
}

.auth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.toggle-text {
  text-align: center;
  color: rgba(139, 69, 19, 0.8);
  font-size: 14px;
}

.toggle-btn {
  background: none;
  border: none;
  color: rgba(139, 69, 19, 1);
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #dc2626;
  padding: 10px;
  border-radius: 10px;
  font-size: 14px;
  margin-top: 10px;
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 15px;
  background: none;
  border: none;
  font-size: 24px;
  color: rgba(139, 69, 19, 0.6);
  cursor: pointer;
}

.close-btn:hover {
  color: rgba(139, 69, 19, 1);
}
</style>