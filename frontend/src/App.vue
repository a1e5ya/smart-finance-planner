<template>
  <div id="app">
    <!-- Show Login Screen for Unauthenticated Users -->
    <div v-if="!user" class="login-screen">
      <div class="login-container">
        <div class="logo-section">
          <h1 class="museo-dashboard">azimuth</h1>
          <p class="tagline">Your Personal Finance Assistant</p>
        </div>
        
        <LoginModal :showModal="true" @close="() => {}" :isFullScreen="true" />
      </div>
    </div>

    <!-- Main App for Authenticated Users -->
    <div v-else class="authenticated-app">
      <!-- Top Bar -->
      <div class="top-bar">
        <button 
          class="btn btn-active museo-dashboard"
          @click="showTab('dashboard')"
        >
          <span class="text-medium">azimuth</span>
        </button>
        
        <div class="flex flex-gap">
          <button 
            class="btn btn-link"
            :class="{ 'btn-active': currentTab === 'transactions' }"
            @click="showTab('transactions')"
          >
            Transactions
          </button>
          <button 
            class="btn btn-link"
            :class="{ 'btn-active': currentTab === 'categories' }"
            @click="showTab('categories')"
          >
            Categories
          </button>
          <button 
            class="btn btn-link"
            :class="{ 'btn-active': currentTab === 'timeline' }"
            @click="showTab('timeline')"
          >
            Timeline
          </button>
        </div>
        
        <div class="flex flex-center flex-gap">
          <span class="text-medium user-info">
            {{ user.displayName || user.email.split('@')[0] }}
          </span>
          
          <button 
            class="btn btn-icon btn-link"
            :class="{ 'btn-active': currentTab === 'settings' }"
            @click="showTab('settings')" 
            title="Settings"
          >
            <AppIcon name="settings-sliders" size="medium" />
          </button>

          <button 
            class="btn btn-icon btn-link" 
            @click="handleLogout" 
            title="Logout"
          >
            <AppIcon name="sign-out" size="medium" />
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="main-content" :class="{ 'chat-open': showHistory && chatHistory.length > 0 }">
        
        <!-- Dashboard Tab -->
        <DashboardTab v-if="currentTab === 'dashboard'" />

        <!-- Transactions Tab -->
        <TransactionsTab 
          v-else-if="currentTab === 'transactions'"
          :user="user"
          :transactionCount="transactionCount"
          :recentUploads="recentUploads"
          :transactions="transactions"
          :loading="loading"
          :currentPage="currentPage"
          :pageSize="pageSize"
          :filters="filters"
          :allCategories="allCategories"
          @file-upload="handleFileUpload"
          @refresh-transactions="refreshTransactions"
          @change-page="changePage"
          @categorize-transaction="categorizeTransaction"
          @edit-transaction="editTransaction"
          @update-transaction-count="updateTransactionCount"
          @update-filters="updateFilters"
          @add-chat-message="addChatMessage"
        />

        <!-- Categories Tab -->
        <CategoriesTab 
          v-else-if="currentTab === 'categories'"
          :categoriesData="categoriesData"
          :selectedCategory="selectedCategory"
          :expenseCategories="expenseCategories"
          @select-category="selectCategory"
        />

        <!-- Timeline Tab -->
        <TimelineTab v-else-if="currentTab === 'timeline'" />

        <!-- Settings Tab -->
        <SettingsTab 
          v-else-if="currentTab === 'settings'"
          :user="user"
          :backendStatus="backendStatus"
          :phase="phase"
          @logout="handleLogout"
          @show-tab="showTab"
        />
      </div>

      <!-- Always Visible Chat Bar -->
      <div class="chat-bar-always">
        <div v-if="showWelcomeMessage && !chatHistory.length && showChat" class="welcome-message">
          {{ welcomeText }}
        </div>
        
        <div v-if="chatHistory.length > 0 && showHistory && showChat" class="chat-history-simple">
          <div class="chat-messages-simple">
            <div v-for="(item, index) in chatHistory" :key="index" class="message-pair-simple">
              <div v-if="item.message" class="message user-message-simple">
                <div class="message-content-simple">{{ item.message }}</div>
              </div>
              <div class="message bot-message-simple">
                <div class="message-content-simple">{{ item.response }}</div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="currentThinking && showChat" class="current-thinking">
          <div class="message bot-message-simple">
            <div class="message-content-simple">{{ currentThinking }}</div>
          </div>
        </div>

<div class="chat-input-row">
  <button 
    class="history-toggle-btn btn-link"
    @click="toggleChatPanel"
    :title="showChat ? 'Close Chat' : 'Open Chat'"
  >
    <AppIcon :name="showChat ? 'angle-down' : 'angle-up'" size="medium" />
  </button>
          <input 
            type="text" 
            class="chat-input-always" 
            v-model="chatInput"
            @keypress.enter="sendMessage()"
            @click="openChatPanel"
            :disabled="loading"
          >
          <button 
            class="btn btn-link" 
            @click="sendMessage()"
            :disabled="loading || !chatInput.trim()"
          >
            <AppIcon name="arrow-right" size="medium" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import axios from 'axios'
import { auth } from '@/firebase/config'
import { onAuthStateChanged } from 'firebase/auth'

// Component imports
import AppIcon from '@/components/AppIcon.vue'
import LoginModal from '@/components/LoginModal.vue'
import DashboardTab from '@/components/DashboardTab.vue'
import TransactionsTab from '@/components/TransactionsTab.vue'
import CategoriesTab from '@/components/CategoriesTab.vue'
import TimelineTab from '@/components/TimelineTab.vue'
import SettingsTab from '@/components/SettingsTab.vue'

// Data imports
import { categoriesData, getCategoryById, getAllCategoriesWithSubcategories } from '@/data/categories.js'

export default {
  name: 'App',
  components: {
    AppIcon,
    LoginModal,
    DashboardTab,
    TransactionsTab,
    CategoriesTab,
    TimelineTab,
    SettingsTab
  },
  setup() {
    // Core app state
    const currentTab = ref('dashboard')
    const user = ref(null)
    const backendStatus = ref('Checking...')
    const phase = ref('1 - Transaction Import')
    const loading = ref(false)
    
    // Chat state
    const chatInput = ref('')
    const chatHistory = ref([])
    const currentThinking = ref('')
    const showWelcomeMessage = ref(true)
    const showHistory = ref(false)
    const showChat = ref(false)
    
    // File upload and transactions state
    const transactionCount = ref(0)
    const recentUploads = ref([])
    const transactions = ref([])
    const currentPage = ref(1)
    const pageSize = ref(50)
    const filters = ref({
      startDate: '',
      endDate: '',
      merchant: '',
      categoryId: '',
      minAmount: null,
      maxAmount: null
    })
    
    // Categories state
    const selectedCategory = ref(null)
    
    // Dynamic API base URL
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

    // Computed properties
    const welcomeText = computed(() => {
      const userName = user.value ? 
        (user.value.displayName || user.value.email.split('@')[0]) : 
        'there'
      return `Hello, ${userName}! I'm here to help you with your financial data. You can ask questions about budgeting, upload CSV files, or explore your transaction categories.`
    })
    
    const expenseCategories = computed(() => getAllCategoriesWithSubcategories())
    
    const allCategories = computed(() => {
      const categories = []
      for (const mainCat of categoriesData) {
        categories.push(mainCat)
        if (mainCat.categories) {
          for (const cat of mainCat.categories) {
            categories.push(cat)
            if (cat.children) {
              categories.push(...cat.children)
            }
          }
        }
      }
      return categories
    })

    // Watchers for filters
    watch(filters, () => {
      if (currentTab.value === 'transactions') {
        loadTransactions()
      }
    }, { deep: true })

    // Chat functions
    const toggleHistory = () => {
      showHistory.value = !showHistory.value
    }

    const scrollToBottom = async () => {
      await nextTick()
      setTimeout(() => {
        const historyElement = document.querySelector('.chat-messages-simple') || 
                              document.querySelector('.chat-history-simple') ||
                              document.querySelector('.chat-bar-always')
        
        if (historyElement) {
          const lastMessage = historyElement.querySelector('.message-pair-simple:last-child') ||
                             historyElement.querySelector('.current-thinking') ||
                             historyElement.lastElementChild
          
          if (lastMessage) {
            lastMessage.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'end'
            })
          } else {
            historyElement.scrollTo({
              top: historyElement.scrollHeight,
              behavior: 'smooth'
            })
          }
        }
      }, 100)
    }

    const addChatMessage = (messageData) => {
      chatHistory.value.push({
        message: messageData.message || '',
        response: messageData.response,
        timestamp: new Date().toLocaleTimeString()
      })
      
      showHistory.value = true
      scrollToBottom()
      
      if (chatHistory.value.length > 20) {
        chatHistory.value = chatHistory.value.slice(-20)
      }
    }

    const sendMessage = async (message = null) => {
      const messageText = message || chatInput.value.trim()
      if (!messageText || loading.value) return

      const originalInput = chatInput.value
      loading.value = true
      chatInput.value = ''
      currentThinking.value = 'Thinking...'
      
      showWelcomeMessage.value = false
      showHistory.value = true

      try {
        let headers = {}
        if (user.value) {
          console.log('🎯 Getting token for chat message...')
          const token = await user.value.getIdToken()
          headers.Authorization = `Bearer ${token}`
          console.log('✅ Got token for chat')
        }

        console.log('📤 Sending chat message:', messageText.substring(0, 50))
        const response = await axios.post(`${API_BASE}/chat/command`, {
          message: messageText
        }, { headers, timeout: 15000 })
        
        console.log('📥 Chat response received:', response.data)
        const botResponse = response.data.response
        
        addChatMessage({
          message: messageText,
          response: botResponse
        })
        
        // Handle navigation commands
        if (messageText.toLowerCase().includes('import') || messageText.toLowerCase().includes('upload')) {
          currentTab.value = 'transactions'
        } else if (messageText.toLowerCase().includes('categor')) {
          currentTab.value = 'categories'
        } else if (messageText.toLowerCase().includes('timeline')) {
          currentTab.value = 'timeline'
        } else if (messageText.toLowerCase().includes('settings')) {
          currentTab.value = 'settings'
        } else if (messageText.toLowerCase().includes('transactions')) {
          currentTab.value = 'transactions'
        }
        
      } catch (error) {
        console.error('❌ Chat request failed:', error)
        
        // Enhanced error handling
        let errorMessage = 'Sorry, I encountered an error. Please try again.'
        
        if (error.response?.status === 401) {
          console.log('🔄 Authentication failed - trying token refresh')
          if (user.value) {
            try {
              const newToken = await user.value.getIdToken(true) // Force refresh
              console.log('✅ Token refreshed, retrying chat...')
              
              const retryResponse = await axios.post(`${API_BASE}/chat/command`, {
                message: messageText
              }, { 
                headers: { Authorization: `Bearer ${newToken}` }, 
                timeout: 15000 
              })
              
              console.log('📥 Chat retry response:', retryResponse.data)
              const botResponse = retryResponse.data.response
              
              addChatMessage({
                message: messageText,
                response: botResponse
              })
              
              loading.value = false
              currentThinking.value = ''
              return // Success, exit function
              
            } catch (retryError) {
              console.error('❌ Chat retry failed:', retryError)
              errorMessage = 'Authentication failed. Please try signing out and back in.'
            }
          } else {
            errorMessage = 'Please sign in to use the chat feature.'
          }
        } else if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
          errorMessage = 'Unable to connect to the server. Please check if the backend is running.'
        } else if (error.response?.status >= 500) {
          errorMessage = 'Server error occurred. Please try again in a moment.'
        }
        
        addChatMessage({
          message: messageText,
          response: errorMessage
        })
        
        chatInput.value = originalInput // Restore input on error
      } finally {
        loading.value = false
        currentThinking.value = ''
      }
    }

    // Backend health check
    const checkBackend = async () => {
      try {
        console.log('🔍 Checking backend connection...')
        const response = await axios.get(`${API_BASE}/health`, { timeout: 10000 })
        backendStatus.value = 'Connected'
        phase.value = response.data.phase || 'Phase 1'
        console.log('✅ Backend connected:', response.data)
      } catch (error) {
        backendStatus.value = 'Disconnected'
        console.error('❌ Backend connection failed:', error)
      }
    }

    // Transaction functions
    const loadTransactions = async () => {
      if (!user.value) {
        console.log('⚠️ No user logged in, cannot load transactions')
        return
      }
      
      loading.value = true
      try {
        console.log('🔑 Getting token for transactions...')
        const token = await user.value.getIdToken()
        
        const params = new URLSearchParams({
          page: currentPage.value,
          limit: pageSize.value,
          ...(filters.value.startDate && { start_date: filters.value.startDate }),
          ...(filters.value.endDate && { end_date: filters.value.endDate }),
          ...(filters.value.merchant && { merchant: filters.value.merchant }),
          ...(filters.value.categoryId && { category_id: filters.value.categoryId }),
          ...(filters.value.minAmount && { min_amount: filters.value.minAmount }),
          ...(filters.value.maxAmount && { max_amount: filters.value.maxAmount })
        })
        
        console.log('📤 Loading transactions with params:', params.toString())
        const response = await axios.get(`${API_BASE}/transactions/list?${params}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        transactions.value = response.data
        console.log('✅ Loaded transactions:', response.data.length)
      } catch (error) {
        console.error('❌ Failed to load transactions:', error)
        if (error.response?.status === 401) {
          console.log('🔄 Transaction auth failed - trying token refresh')
          try {
            const newToken = await user.value.getIdToken(true) // Force refresh
            const params = new URLSearchParams({
              page: currentPage.value,
              limit: pageSize.value,
              ...(filters.value.startDate && { start_date: filters.value.startDate }),
              ...(filters.value.endDate && { end_date: filters.value.endDate }),
              ...(filters.value.merchant && { merchant: filters.value.merchant }),
              ...(filters.value.categoryId && { category_id: filters.value.categoryId }),
              ...(filters.value.minAmount && { min_amount: filters.value.minAmount }),
              ...(filters.value.maxAmount && { max_amount: filters.value.maxAmount })
            })
            
            const retryResponse = await axios.get(`${API_BASE}/transactions/list?${params}`, {
              headers: { 'Authorization': `Bearer ${newToken}` }
            })
            
            transactions.value = retryResponse.data
            console.log('✅ Transaction retry successful:', retryResponse.data.length)
          } catch (retryError) {
            console.error('❌ Transaction retry failed:', retryError)
          }
        }
      } finally {
        loading.value = false
      }
    }

    const refreshTransactions = () => {
      currentPage.value = 1
      loadTransactions()
    }

    const changePage = (newPage) => {
      currentPage.value = newPage
      loadTransactions()
    }

    const updateFilters = (newFilters) => {
      filters.value = newFilters
    }

    const categorizeTransaction = async (transactionId, categoryId) => {
      if (!user.value || !categoryId) return
      
      try {
        console.log('🏷️ Categorizing transaction:', transactionId, 'as', categoryId)
        const token = await user.value.getIdToken()
        
        await axios.post(`${API_BASE}/transactions/categorize/${transactionId}`, 
          { category_id: categoryId },
          { 
            headers: { 'Authorization': `Bearer ${token}` },
            params: { category_id: categoryId }
          }
        )
        
        // Refresh transactions to show updated category
        loadTransactions()
        
        // Add success message to chat
        const category = getCategoryById(categoryId)
        if (category) {
          addChatMessage({
            message: 'Transaction categorized',
            response: `✅ Transaction successfully categorized as ${category.name}!`
          })
        }
        
      } catch (error) {
        console.error('❌ Failed to categorize transaction:', error)
        if (error.response?.status === 401) {
          console.log('🔄 Categorization auth failed - trying refresh')
          try {
            const newToken = await user.value.getIdToken(true) // Force refresh
            await axios.post(`${API_BASE}/transactions/categorize/${transactionId}`, 
              { category_id: categoryId },
              { 
                headers: { 'Authorization': `Bearer ${newToken}` },
                params: { category_id: categoryId }
              }
            )
            
            loadTransactions()
            
            const category = getCategoryById(categoryId)
            if (category) {
              addChatMessage({
                message: 'Transaction categorized',
                response: `✅ Transaction successfully categorized as ${category.name}!`
              })
            }
          } catch (retryError) {
            console.error('❌ Categorization retry failed:', retryError)
            addChatMessage({
              response: '❌ Failed to categorize transaction. Please try again.'
            })
          }
        }
      }
    }

    const editTransaction = (transaction) => {
      console.log('✏️ Edit transaction:', transaction)
      // TODO: Implement transaction editing
    }

    // File upload handler for TransactionsTab
    const handleFileUpload = (files) => {
      console.log('📁 File upload event received:', files.length, 'files')
      // The actual file processing will be handled in TransactionsTab component
    }

    // Update transaction count from TransactionsTab
    const updateTransactionCount = (count) => {
      transactionCount.value = count
    }

    // Category functions
    const selectCategory = (category) => {
      selectedCategory.value = category
    }

    const getCategoryIcon = (categoryId) => {
      const category = getCategoryById(categoryId)
      return category?.icon || 'circle'
    }

    // Utility functions
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }

    const formatAmount = (amount) => {
      const num = parseFloat(amount)
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(Math.abs(num))
    }

    // Navigation functions
    const showTab = (tabName) => {
      currentTab.value = tabName
      if (tabName === 'transactions' && user.value) {
        loadTransactions()
      }
    }

    // Auth functions
    const handleLogout = async () => {
      if (user.value) {
        try {
          await auth.signOut()
          addChatMessage({
            message: 'Logout',
            response: "✅ You've been signed out. Sign in again for personalized features!"
          })
          
          showWelcomeMessage.value = false
        } catch (error) {
          console.error('❌ Logout error:', error)
        }
      }
    }

    // Initialize
    onMounted(() => {
      console.log('🚀 App initializing...')
      checkBackend()
      
      onAuthStateChanged(auth, (firebaseUser) => {
        user.value = firebaseUser
        console.log('🔐 Auth state changed:', firebaseUser ? firebaseUser.email : 'signed out')
        
        // Initialize welcome message for authenticated users only
        if (firebaseUser && chatHistory.value.length === 0) {
          const userName = firebaseUser.displayName || firebaseUser.email.split('@')[0]
          
          addChatMessage({
            response: `Hello, ${userName}! I'm here to help you with your financial data. You can ask questions about budgeting, upload CSV files, or explore your transaction categories.`
          })
          
          showWelcomeMessage.value = false
        }
      })
    })

        const openChatPanel = () => {
      showChat.value = true
      showHistory.value = true
    }

    const closeChatPanel = () => {
      showChat.value = false
      showHistory.value = false
    }

    const toggleChatPanel = () => {
      if (showChat.value) {
        closeChatPanel()
      } else {
        openChatPanel()
      }
    }

    return {
      // Core state
      currentTab,
      user,
      backendStatus,
      phase,
      loading,
      
      // Chat state
      chatInput,
      chatHistory,
      currentThinking,
      showWelcomeMessage,
      showHistory,
      showChat,
      welcomeText,
      
      // File upload and transaction state
      transactionCount,
      recentUploads,
      transactions,
      currentPage,
      pageSize,
      filters,
      
      // Category state
      categoriesData,
      selectedCategory,
      expenseCategories,
      allCategories,
      
      // Functions
      toggleHistory,
      openChatPanel,
      closeChatPanel,
      toggleChatPanel,
      sendMessage,
      addChatMessage,
      scrollToBottom,
      loadTransactions,
      refreshTransactions,
      changePage,
      updateFilters,
      categorizeTransaction,
      editTransaction,
      handleFileUpload,
      updateTransactionCount,
      selectCategory,
      getCategoryIcon,
      formatDate,
      formatAmount,
      showTab,
      handleLogout
    }
  }
}
</script>

<style scoped>
.login-screen {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-container {
  text-align: center;
  max-width: 400px;
  width: 90%;
}

.logo-section {
  margin-bottom: 2rem;
}

.logo-section h1 {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.tagline {
  color: var(--color-text-light);
  font-size: var(--text-medium);
}

.authenticated-app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.user-info {
  color: var(--color-text-light);
}
</style>