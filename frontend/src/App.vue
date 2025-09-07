<template>
  <div id="app">
    <!-- Top Bar with Custom Icons -->
    <div class="top-bar">
<button 
  class="btn btn-active museo-dashboard"
  @click="showTab('dashboard')"
>
  <span class="text-medium">azimuth</span>
</button>
      
      <div class="flex flex-gap">
        <button 
          class="btn"
          :class="{ 'btn-active': currentTab === 'transactions' }"
          @click="showTab('transactions')"
        >
          Transactions
        </button>
        <button 
          class="btn"
          :class="{ 'btn-active': currentTab === 'categories' }"
          @click="showTab('categories')"
        >
          Categories
        </button>
        <button 
          class="btn"
          :class="{ 'btn-active': currentTab === 'timeline' }"
          @click="showTab('timeline')"
        >
          Timeline
        </button>
      </div>
      
      <div class="flex flex-center flex-gap">
        <button 
          class="btn btn-icon"
          :class="{ 'btn-active': currentTab === 'settings-sliders' }"
          @click="showTab('settings')" 
          title="Settings"
        >
          <AppIcon name="settings-sliders" size="medium" />
        </button>
        <span class="text-medium" @click="handleUserClick">
          {{ user ? (user.displayName || user.email.split('@')[0]) : 'Sign In' }}
        </span>
        <button 
          class="btn btn-icon" 
          @click="handleLogout" 
          :title="user ? 'Logout' : 'Sign In'"
        >
          <AppIcon :name="user ? 'sign-out' : 'login'" size="medium" />
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Dashboard Tab -->
      <div v-if="currentTab === 'dashboard'" class="tab-content">
        <!-- Status Cards -->
        <div class="section">
          <div class="grid grid-auto">
            <div class="card flex flex-gap">
              <div>
                <div class="text-small text-muted">Data Import</div>
                <div class="text-medium">{{ transactionCount }} transactions</div>
                <div class="text-small text-light">Ready to import CSV files</div>
              </div>
            </div>
            
            
            <div class="card flex flex-gap">
            <div class="text-medium section-header">Recent Activity</div>
            <div class="flex-column flex-gap-sm">
              <div v-if="recentUploads.length === 0" class="text-center text-light">
                No recent imports. Upload your first CSV file to get started!
              </div>
              <div v-for="upload in recentUploads" :key="upload.id" class="card flex flex-gap">
                <div class="status-icon">{{ upload.status === 'success' ? '✅' : '⏳' }}</div>
                <div>
                  <div class="text-medium">{{ upload.filename }}</div>
                  <div class="text-small text-light">{{ upload.timestamp }} • {{ upload.rows }} rows</div>
                </div>
              </div>
            </div>

            </div>
          </div>
        </div>

        <!-- Import Section -->
        <div class="section">
          <div class="container container-large">
            <div class="section-header text-center">
              <div class="text-large">Import Your Financial Data</div>
              <div class="text-medium text-light">Upload CSV files from your bank or financial institution to get started</div>
            </div>
            
    <div class="drop-zone" @click="triggerFileUpload">
      <div class="flex-column flex-center flex-gap">
        <AppIcon name="upload" size="large" />
        <div class="text-large">Drag & Drop CSV Files</div>
        <div class="text-medium text-light">Or click to browse and select files</div>
      </div>
              <input 
                ref="fileInput" 
                type="file" 
                accept=".csv,.xlsx" 
                multiple 
                @change="handleFileSelect" 
                style="display: none;"
              >
            </div>
            
            <div class="flex flex-center flex-gap flex-wrap">
              <button class="btn btn-active" @click="triggerFileUpload">
                Choose Files
              </button>
              <button class="btn" @click="showSampleData">
                View Sample
              </button>
              <button class="btn" @click="sendMessage('help import')">
                Import Help
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Transactions Tab -->
      <div v-else-if="currentTab === 'transactions'" class="tab-content">
        <div class="flex-between section-header">
          <div class="text-large">Transaction Management</div>
          <div class="text-small text-light">
            Total: {{ transactionCount }} transactions • User: {{ user ? user.email.split('@')[0] : 'Guest' }}
          </div>
        </div>

        <div class="grid grid-2">
          <div class="container text-center">
            <div class="text-medium">Import & Manage Transactions</div>
            <div class="text-small text-light">
              Upload CSV files from your bank to automatically categorize and analyze your spending patterns.
            </div>
            <button class="btn btn-active" @click="showTab('dashboard')">
              Start Import
            </button>
          </div>

          <div class="container text-center">
            <div class="text-medium">Smart Categorization</div>
            <div class="text-small text-light">
              AI-powered transaction categorization with manual override capabilities.
            </div>
          </div>
        </div>
      </div>

      <!-- Categories Tab -->
      <div v-else-if="currentTab === 'categories'" class="tab-content">
        <div class="grid grid-sidebar">
          <div class="container">
            <div class="text-medium section-header">Category Hierarchy</div>
            <div class="flex-column">
              <button class="category-btn active">
                <span>🍽️</span>
                <span>Food & Dining</span>
              </button>
              <button class="category-btn category-indent">
                <span>🏪</span>
                <span>Restaurants</span>
              </button>
              <button class="category-btn category-indent">
                <span>🛒</span>
                <span>Groceries</span>
              </button>
              <button class="category-btn">
                <span>🚗</span>
                <span>Transportation</span>
              </button>
              <button class="category-btn category-indent">
                <span>⛽</span>
                <span>Gas</span>
              </button>
              <button class="category-btn category-indent">
                <span>🚌</span>
                <span>Public Transit</span>
              </button>
              <button class="category-btn">
                <span>🏠</span>
                <span>Housing</span>
              </button>
              <button class="category-btn">
                <span>💼</span>
                <span>Business</span>
              </button>
              <button class="category-btn">
                <span>🎯</span>
                <span>Goals</span>
              </button>
            </div>
          </div>
          
          <div class="container">
            <div class="text-medium section-header">Smart Categorization</div>
            <div class="text-small text-light">
              {{ user ? `Personalized categories for ${user.email.split('@')[0]}` : 'Sign in to create custom categories' }}
            </div>
            
            <div class="flex flex-gap flex-wrap">
              <button class="btn">Split Category</button>
              <button class="btn">Merge Categories</button>
              <button class="btn">Add Rule</button>
            </div>
            
            <div class="container text-center" style="height: 12.5rem;">
              <div class="text-medium">Category Analytics</div>
              <div class="text-small text-light">Import transactions to see category breakdown</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Timeline Tab -->
      <div v-else-if="currentTab === 'timeline'" class="tab-content">
        <div class="flex flex-between flex-wrap">
          <div class="flex flex-gap">
            <button class="btn btn-active">Month</button>
            <button class="btn">Quarter</button>
            <button class="btn">Year</button>
          </div>
          <div class="text-small text-light">
            {{ user ? `Timeline for ${user.email.split('@')[0]}` : 'Sign in for personalized timeline' }}
          </div>
        </div>

        <div class="section">
          <div class="container text-center" style="height: 25rem;">
            <div class="text-large">Interactive Financial Timeline</div>
            <div class="text-medium text-light">Import transaction data to see your financial timeline</div>
          </div>
        </div>

        <div class="grid grid-2">
          <div class="container text-center">
            <div class="text-medium">Financial Goals</div>
            <div class="text-small text-light">
              Set and track financial goals after importing your transaction data.
            </div>
          </div>
          
          <div class="container text-center">
            <div class="text-medium">Scenario Planning</div>
            <div class="text-small text-light">Create what-if scenarios for your financial future.</div>
            <button class="btn">Create Scenario</button>
          </div>
        </div>
      </div>

      <!-- Settings Tab -->
      <div v-else-if="currentTab === 'settings'" class="tab-content">
        
        <!-- System Status -->
        <div class="section">
          <div class="container">
            <div class="text-medium section-header">System Status</div>
            <div class="grid grid-auto">
              <div class="card text-center">
                <div class="text-small text-muted">Authentication</div>
                <div class="text-medium">{{ user ? 'Signed In' : 'Anonymous' }}</div>
                <div class="text-small text-light">{{ user ? user.email : 'Not authenticated' }}</div>
              </div>
              <div class="card text-center">
                <div class="text-small text-muted">Backend Status</div>
                <div class="text-medium">{{ backendStatus }}</div>
                <div class="text-small text-light">API Connection</div>
              </div>
              <div class="card text-center">
                <div class="text-small text-muted">Phase Progress</div>
                <div class="text-medium">{{ phase }}</div>
                <div class="text-small text-light">Current Development Phase</div>
              </div>
            </div>
          </div>
        </div>

        <!-- User Profile -->
        <div class="section">
          <div class="container">
            <div class="text-medium section-header">User Profile</div>
            <div v-if="user">
              <div class="text-small"><strong>Email:</strong> {{ user.email }}</div>
              <div class="text-small"><strong>UID:</strong> {{ user.uid.substring(0, 16) }}...</div>
              <div class="text-small"><strong>Display Name:</strong> {{ user.displayName || 'Not set' }}</div>
              <button class="btn" @click="handleLogout">Sign Out</button>
            </div>
            <div v-else>
              <div class="text-small text-light">Sign in to access personalized features and secure data storage.</div>
              <button class="btn" @click="showLoginModal = true">Sign In</button>
            </div>
          </div>
        </div>

        <!-- Data Management -->
        <div class="section">
          <div class="container">
            <div class="text-medium section-header">Data Management</div>
            <div class="flex flex-gap flex-wrap">
              <button class="btn">Import Data</button>
              <button class="btn">Export Data</button>
              <button class="btn">Clear All Data</button>
              <button class="btn">Reset Categories</button>
            </div>
          </div>
        </div>

        
      </div>
    </div>

    <!-- Chat Bar -->
    <div class="chat-bar">
      <!-- Chat History with External Scrollbar -->
      <div v-if="chatHistory.length > 0" class="chat-history">
        <div v-for="(item, index) in chatHistory" :key="index" class="history-item">
          <div class="text-small text-muted">You: {{ item.message }}</div>
          <div class="text-small">Bot: {{ item.response }}</div>
        </div>
      </div>

      <!-- Chat Response -->
      <div v-if="chatResponse" class="chat-response">
        {{ chatResponse }}
      </div>
      
      <!-- Chat Input -->
      <div class="flex flex-gap">
        <input 
          type="text" 
          class="chat-input" 
          placeholder="Ask me anything about importing transactions..."
          v-model="chatInput"
          @keypress.enter="sendMessage()"
        >
        <button class="btn btn-active" @click="sendMessage()">
          Send
        </button>
      </div>
    </div>

    <!-- Login Modal -->
    <LoginModal :showModal="showLoginModal" @close="showLoginModal = false" />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { auth } from '@/firebase/config'
import { onAuthStateChanged } from 'firebase/auth'
import LoginModal from '@/components/LoginModal.vue'
import AppIcon from '@/components/AppIcon.vue'

export default {
  name: 'App',
  components: {
    AppIcon,
    LoginModal
  },
  setup() {
    const currentTab = ref('dashboard')
    const user = ref(null)
    const chatInput = ref('')
    const chatResponse = ref('')
    const backendStatus = ref('Checking...')
    const phase = ref('1 - Transaction Import')
    const showLoginModal = ref(false)
    const transactionCount = ref(0)
    const recentUploads = ref([])
    const chatHistory = ref([])
    const fileInput = ref(null)

    // Dynamic API base URL
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

    // Initialize with welcome message
    const initializeWelcomeMessage = () => {
      const userName = user.value ? 
        (user.value.displayName || user.value.email.split('@')[0]) : 
        'there'
      
      chatResponse.value = `Hello, ${userName}! How are you today? I'm here to help you with your financial data. You can upload CSV files, ask questions about budgeting, or explore your transaction categories.`
    }

    // Check backend health
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

    // Send chat message with auth token
    const sendMessage = async (message = null) => {
      const messageText = message || chatInput.value.trim()
      if (!messageText) return

      const originalInput = chatInput.value
      chatInput.value = ''
      chatResponse.value = 'Thinking...'

      try {
        let headers = {}
        if (user.value) {
          const token = await user.value.getIdToken()
          headers.Authorization = `Bearer ${token}`
        }

        const response = await axios.post(`${API_BASE}/chat/command`, {
          message: messageText
        }, { headers, timeout: 15000 })
        
        chatResponse.value = response.data.response
        
        // Add to chat history
        chatHistory.value.unshift({
          message: messageText,
          response: response.data.response,
          timestamp: new Date().toLocaleTimeString()
        })
        
        // Keep only last 10 conversations
        if (chatHistory.value.length > 10) {
          chatHistory.value = chatHistory.value.slice(0, 10)
        }
        
        // Handle navigation commands
        if (messageText.toLowerCase().includes('import') || messageText.toLowerCase().includes('upload')) {
          currentTab.value = 'dashboard'
        } else if (messageText.toLowerCase().includes('categor')) {
          currentTab.value = 'categories'
        } else if (messageText.toLowerCase().includes('timeline')) {
          currentTab.value = 'timeline'
        } else if (messageText.toLowerCase().includes('settings')) {
          currentTab.value = 'settings'
        }
        
      } catch (error) {
        console.error('Chat request failed:', error)
        chatResponse.value = `Error: ${error.message}. Please check if the backend is running.`
        chatInput.value = originalInput
      }
    }

    // File handling functions
    const triggerFileUpload = () => {
      fileInput.value?.click()
    }

    const handleFileSelect = (event) => {
      const files = event.target.files
      processFiles(files)
    }

    const handleFileDrop = (event) => {
      const files = event.dataTransfer.files
      processFiles(files)
    }

    const processFiles = (files) => {
      if (!files || files.length === 0) return
      
      Array.from(files).forEach((file, index) => {
        console.log('Processing file:', file.name)
        
        const upload = {
          id: Date.now() + index,
          filename: file.name,
          status: 'processing',
          rows: Math.floor(Math.random() * 1000) + 100,
          timestamp: new Date().toLocaleTimeString()
        }
        
        recentUploads.value.unshift(upload)
        
        setTimeout(() => {
          upload.status = 'success'
          transactionCount.value += upload.rows
          chatResponse.value = `Successfully processed ${file.name} with ${upload.rows} transactions!`
        }, 2000)
      })
    }

    const showSampleData = () => {
      sendMessage('show me sample CSV format')
    }

    const clearChatHistory = () => {
      chatHistory.value = []
      initializeWelcomeMessage()
    }

    const showTab = (tabName) => {
      currentTab.value = tabName
    }

    const handleUserClick = () => {
      if (!user.value) {
        showLoginModal.value = true
      }
    }

    const handleLogout = async () => {
      if (user.value) {
        try {
          await auth.signOut()
          chatResponse.value = "You've been signed out. Sign in again for personalized features!"
        } catch (error) {
          console.error('Logout error:', error)
        }
      } else {
        showLoginModal.value = true
      }
    }

    // Initialize
    onMounted(() => {
      checkBackend()
      
      onAuthStateChanged(auth, (firebaseUser) => {
        user.value = firebaseUser
        console.log('Auth state changed:', firebaseUser ? firebaseUser.email : 'signed out')
        initializeWelcomeMessage()
      })

      initializeWelcomeMessage()
    })

    return {
      currentTab,
      user,
      chatInput,
      chatResponse,
      backendStatus,
      phase,
      showLoginModal,
      transactionCount,
      recentUploads,
      chatHistory,
      fileInput,
      sendMessage,
      showTab,
      handleUserClick,
      handleLogout,
      triggerFileUpload,
      handleFileSelect,
      handleFileDrop,
      showSampleData,
      clearChatHistory
    }
  }
}
</script>

<style>
@import './assets/styles.css';
</style>