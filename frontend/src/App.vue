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
      <div class="main-content" :class="{ 'chat-open': showChat }">
        
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
        <div v-if="showWelcomeMessage && !chatHistory.length" class="welcome-message">
          {{ welcomeText }}
        </div>
        
        <div v-if="chatHistory.length > 0 && showHistory" class="chat-history-simple">
          <div class="chat-messages-simple">
            <div v-for="(item, index) in chatHistory" :key="index" class="message-pair-simple">
              <div class="message user-message-simple">
                <div class="message-content-simple">{{ item.message }}</div>
              </div>
              <div class="message bot-message-simple">
                <div class="message-content-simple">{{ item.response }}</div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="currentThinking" class="current-thinking">
          <div class="message bot-message-simple">
            <div class="message-content-simple">{{ currentThinking }}</div>
          </div>
        </div>

        <div class="chat-input-row">
          <button 
            v-if="chatHistory.length > 0"
            class="history-toggle-btn btn-link"
            @click="toggleHistory"
            :title="showHistory ? 'Hide History' : 'Show History'"
          >
            <AppIcon :name="showHistory ? 'angle-down' : 'angle-up'" size="medium" />
          </button>
          <input 
            type="text" 
            class="chat-input-always" 
            v-model="chatInput"
            @keypress.enter="sendMessage()"
            @click="showHistory = true"
            :disabled="loading"
            placeholder="Ask about your finances..."
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
        if (mainCat.children) {
          categories.push(...mainCat.children)
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
          console.log('Getting token for chat message...')
          const token = await user.value.getIdToken()
          headers.Authorization = `Bearer ${token}`
        }

        const response = await axios.post(`${API_BASE}/chat/command`, {
          message: messageText
        }, { headers, timeout: 15000 })
        
        const botResponse = response.data.response
        
        chatHistory.value.push({
          message: messageText,
          response: botResponse,
          timestamp: new Date().toLocaleTimeString()
        })
        
        scrollToBottom()
        
        if (chatHistory.value.length > 20) {
          chatHistory.value = chatHistory.value.slice(-20)
        }
        
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
        console.error('Chat request failed:', error)
        
        // Try with token refresh if 401
        if (error.response?.status === 401 && user.value) {
          try {
            console.log('Chat authentication failed - trying token refresh')
            const newToken = await user.value.getIdToken(true) // Force refresh
            
            const retryResponse = await axios.post(`${API_BASE}/chat/command`, {
              message: messageText
            }, { 
              headers: { Authorization: `Bearer ${newToken}` }, 
              timeout: 15000 
            })
            
            const botResponse = retryResponse.data.response
            
            chatHistory.value.push({
              message: messageText,
              response: botResponse,
              timestamp: new Date().toLocaleTimeString()
            })
            
            scrollToBottom()
            
          } catch (retryError) {
            console.error('Chat retry also failed:', retryError)
            const errorResponse = `Error: ${retryError.message}. Please check if the backend is running.`
            
            chatHistory.value.push({
              message: messageText,
              response: errorResponse,
              timestamp: new Date().toLocaleTimeString()
            })

            scrollToBottom()
            chatInput.value = originalInput
          }
        } else {
          const errorResponse = `Error: ${error.message}. Please check if the backend is running.`
          
          chatHistory.value.push({
            message: messageText,
            response: errorResponse,
            timestamp: new Date().toLocaleTimeString()
          })

          scrollToBottom()
          chatInput.value = originalInput
        }
      } finally {
        loading.value = false
        currentThinking.value = ''
      }
    }

    // Backend health check
    const checkBackend = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`, { timeout: 10000 })
        backendStatus.value = 'Connected'
        phase.value = response.data.phase || 'Phase 1'
        console.log('✅ Backend connected:', response.data)
      } catch (error) {
        backendStatus.value = 'Disconnected'
        console.error('Backend connection failed:', error)
      }
    }

    // Transaction functions
    const loadTransactions = async () => {
      if (!user.value) {
        console.log('No user logged in, cannot load transactions')
        return
      }
      
      loading.value = true
      try {
        console.log('Getting ID token for user:', user.value.email)
        const token = await user.value.getIdToken()
        console.log('Got token, making request...')
        
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
        
        const response = await axios.get(`${API_BASE}/transactions/list?${params}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        transactions.value = response.data
        console.log('Loaded transactions:', response.data.length)
      } catch (error) {
        console.error('Failed to load transactions:', error)
        if (error.response?.status === 401) {
          console.error('Authentication failed - token may be expired')
          try {
            const newToken = await user.value.getIdToken(true) // Force refresh
            console.log('Refreshed token, retrying...')
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
            console.log('Retry successful, loaded transactions:', retryResponse.data.length)
          } catch (retryError) {
            console.error('Retry also failed:', retryError)
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

    const categorizeTransaction = async (transactionId, categoryId) => {
      if (!user.value || !categoryId) return
      
      try {
        console.log('Categorizing transaction:', transactionId, 'as', categoryId)
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
          chatHistory.value.push({
            message: 'Transaction categorized',
            response: `Transaction successfully categorized as ${category.name}!`,
            timestamp: new Date().toLocaleTimeString()
          })
          scrollToBottom()
        }
        
      } catch (error) {
        console.error('Failed to categorize transaction:', error)
        if (error.response?.status === 401) {
          console.error('Categorization authentication failed - trying token refresh')
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
              chatHistory.value.push({
                message: 'Transaction categorized',
                response: `Transaction successfully categorized as ${category.name}!`,
                timestamp: new Date().toLocaleTimeString()
              })
              scrollToBottom()
            }
          } catch (retryError) {
            console.error('Categorization retry failed:', retryError)
          }
        }
      }
    }

    const editTransaction = (transaction) => {
      console.log('Edit transaction:', transaction)
      // TODO: Implement transaction editing
    }

    // File upload handler for TransactionsTab
    const handleFileUpload = (files) => {
      console.log('File upload event received:', files.length, 'files')
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
          chatHistory.value.push({
            message: 'Logout',
            response: "You've been signed out. Sign in again for personalized features!",
            timestamp: new Date().toLocaleTimeString()
          })
          
          showHistory.value = true
          scrollToBottom()
          showWelcomeMessage.value = false
        } catch (error) {
          console.error('Logout error:', error)
        }
      }
    }

    // Initialize
    onMounted(() => {
      checkBackend()
      
      onAuthStateChanged(auth, (firebaseUser) => {
        user.value = firebaseUser
        console.log('Auth state changed:', firebaseUser ? firebaseUser.email : 'signed out')
        
        // Initialize welcome message for authenticated users only
        if (firebaseUser && chatHistory.value.length === 0) {
          const userName = firebaseUser.displayName || firebaseUser.email.split('@')[0]
          
          chatHistory.value.push({
            response: `Hello, ${userName}! I'm here to help you with your financial data. You can ask questions about budgeting, upload CSV files, or explore your transaction categories.`,
            timestamp: new Date().toLocaleTimeString()
          })
          
          showWelcomeMessage.value = false
        }
      })
    })

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
      sendMessage,
      scrollToBottom,
      loadTransactions,
      refreshTransactions,
      changePage,
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