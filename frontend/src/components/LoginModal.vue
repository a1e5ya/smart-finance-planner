<template>
  <div v-if="showModal" :class="modalClasses" @click="handleOverlayClick">
    <div :class="contentClasses" @click.stop>
      <h2 v-if="!isFullScreen">{{ isLogin ? 'Sign In' : 'Sign Up' }}</h2>
      
      <!-- Google Sign-In Button -->
      <button @click="handleGoogleAuth" :class="googleBtnClasses">
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
          :class="inputClasses"
        />
        <input
          v-model="password"
          type="password"
          placeholder="Password"
          required
          :class="inputClasses"
        />
        
        <button type="submit" :class="authBtnClasses" :disabled="loading">
          {{ loading ? 'Loading...' : (isLogin ? 'Sign In' : 'Sign Up') }}
        </button>
      </form>
      
      <!-- Toggle Login/Register -->
      <p :class="toggleTextClasses">
        {{ isLogin ? "Don't have an account?" : "Already have an account?" }}
        <button @click="isLogin = !isLogin" class="toggle-btn">
          {{ isLogin ? 'Sign Up' : 'Sign In' }}
        </button>
      </p>
      
      <!-- Error Message -->
      <div v-if="error" class="error-message">{{ error }}</div>
      
      <!-- Close Button (only for non-fullscreen) -->
      <button v-if="!isFullScreen" @click="closeModal" class="close-btn">×</button>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'LoginModal',
  props: {
    showModal: {
      type: Boolean,
      default: false
    },
    isFullScreen: {
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
      if (!props.isFullScreen) {
        emit('close')
        resetForm()
      }
    }
    
    const handleOverlayClick = () => {
      if (!props.isFullScreen) {
        closeModal()
      }
    }
    
    const resetForm = () => {
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
          if (!props.isFullScreen) {
            closeModal()
          }
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
          if (!props.isFullScreen) {
            closeModal()
          }
        } else {
          error.value = result.error
        }
      } catch (err) {
        error.value = err.message
      }
      
      loading.value = false
    }
    
    // Computed classes based on fullscreen mode
    const modalClasses = computed(() => [
      props.isFullScreen ? 'fullscreen-modal' : 'modal-overlay'
    ])
    
    const contentClasses = computed(() => [
      props.isFullScreen ? 'fullscreen-content' : 'modal-content'
    ])
    
    const googleBtnClasses = computed(() => [
      'google-btn',
      props.isFullScreen ? 'fullscreen-google-btn' : ''
    ])
    
    const inputClasses = computed(() => [
      'auth-input',
      props.isFullScreen ? 'fullscreen-input' : ''
    ])
    
    const authBtnClasses = computed(() => [
      'auth-btn',
      props.isFullScreen ? 'fullscreen-auth-btn' : ''
    ])
    
    const toggleTextClasses = computed(() => [
      'toggle-text',
      props.isFullScreen ? 'fullscreen-toggle-text' : ''
    ])
    
    return {
      isLogin,
      email,
      password,
      error,
      loading,
      closeModal,
      handleOverlayClick,
      handleGoogleAuth,
      handleEmailAuth,
      modalClasses,
      contentClasses,
      googleBtnClasses,
      inputClasses,
      authBtnClasses,
      toggleTextClasses
    }
  }
}
</script>

<style scoped>
/* Regular Modal Styles */
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
  background: var(--color-background-light);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-large);
  padding: var(--gap-large);
  width: 90%;
  max-width: 400px;
  position: relative;
  box-shadow: var(--shadow);
}

/* Full Screen Modal Styles */
.fullscreen-modal {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fullscreen-content {

  backdrop-filter: blur(20px);
  border-radius: 30px;
  padding: 0;
  width: 100%;
  max-width: 400px;
  position: relative;

}

/* Common Styles */
.modal-content h2,
.fullscreen-content h2 {
  text-align: center;
  margin-bottom: var(--gap-standard);
  color: var(--color-text);
  font-weight: 600;
}

.fullscreen-content h2 {
  color: rgb(0, 0, 0);
  margin-bottom: var(--gap-large);
}

.google-btn {
  width: 100%;
  padding: var(--gap-small) var(--gap-standard);
  background: var(--color-button);
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: var(--radius);
  font-size: var(--text-medium);
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: var(--gap-standard);
  box-shadow: var(--shadow);
}

.fullscreen-google-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: #333;
}

.google-btn:hover,
.fullscreen-google-btn:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}

.divider {
  text-align: center;
  margin: var(--gap-standard) 0;
  color: var(--color-text-muted);
  position: relative;
}

.fullscreen-content .divider {
  color: rgba(0, 0, 0, 0.8);
}



.divider {
  background: var(--color-background-light);
  padding: 0 var(--gap-standard);
}

.fullscreen-content .divider {
  background: rgba(255, 255, 255, 0.1);
}

.auth-input {
  width: 100%;
  padding: var(--gap-small) var(--gap-standard);
  border: 2px solid rgba(0, 0, 0, 0.2);
  border-radius: var(--radius);
  margin-bottom: var(--gap-standard);
  font-size: var(--text-medium);
  background: var(--color-button);
  transition: all 0.3s ease;
  color: var(--color-text);
}

.fullscreen-input {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: #333;
}

.auth-input:focus,
.fullscreen-input:focus {
  outline: none;
  border-color: var(--color-button-active);
  background: white;
}

.auth-btn {
  width: 100%;
  padding: var(--gap-small) var(--gap-standard);

  color: #000;
  border: none;
  border-radius: var(--radius);
  font-size: var(--text-medium);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: var(--gap-standard);
  box-shadow: var(--shadow);
}

.fullscreen-auth-btn {
  background: rgba(255, 255, 255, 0.2) !important;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.auth-btn:hover:not(:disabled),
.fullscreen-auth-btn:hover:not(:disabled) {
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}

.auth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.toggle-text {
  text-align: center;
  font-size: var(--text-small);
  margin: 0;
}

.fullscreen-toggle-text {

}

.toggle-btn {
  background: none;
  border: none;
  color: var(--color-text);
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
  font-size: inherit;
}

.fullscreen-content .toggle-btn {

}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #dc2626;
  padding: var(--gap-small);
  border-radius: var(--radius);
  font-size: var(--text-small);
  margin-top: var(--gap-standard);
}

.close-btn {
  position: absolute;
  top: var(--gap-small);
  right: var(--gap-standard);
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-text-muted);
  cursor: pointer;
}

.close-btn:hover {
  color: var(--color-text);
}
</style>