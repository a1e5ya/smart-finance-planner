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
                <span class="text-medium" @click="handleUserClick">
          {{ user ? (user.displayName || user.email.split('@')[0]) : 'Sign In' }}
        </span>
        
        <button 
          class="btn btn-icon btn-link"
          :class="{ 'btn-active': currentTab === 'settings-sliders' }"
          @click="showTab('settings')" 
          title="Settings"
        >
          <AppIcon name="settings-sliders" size="medium" />
        </button>

        <button 
          class="btn btn-icon btn-link" 
          @click="handleLogout" 
          :title="user ? 'Logout' : 'Sign In'"
        >
          <AppIcon :name="user ? 'sign-out' : 'login'" size="medium" />
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content" :class="{ 'chat-open': showChat }">
      <!-- Dashboard Tab -->
      <div v-if="currentTab === 'dashboard'" class="tab-content">
        <!-- Status Cards -->

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

        <!-- Import Section -->

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


      <!-- Transactions Tab -->
      <div v-else-if="currentTab === 'transactions'" class="tab-content">

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



          <div class="container text-center" style="height: 25rem;">
          <div class="flex flex-gap">
            <button class="btn btn-active">Month</button>
            <button class="btn">Quarter</button>
            <button class="btn">Year</button>
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


        <!-- User Profile -->

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


        <!-- Data Management -->

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

<div class="chat-bar-always">
  <!-- Welcome Message (only shown initially) -->
  <div v-if="showWelcomeMessage && !chatHistory.length" class="welcome-message">
    {{ welcomeText }}
  </div>
  
  <!-- Chat History -->
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

  <!-- Current Response (while thinking) -->
  <div v-if="currentThinking" class="current-thinking">
    <div class="message bot-message-simple">
      <div class="message-content-simple">{{ currentThinking }}</div>
    </div>
  </div>

  <!-- Always visible input with history toggle -->
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



    <!-- Login Modal -->
    <LoginModal :showModal="showLoginModal" @close="showLoginModal = false" />
  </div>
</template>

<script>
import { ref, onMounted, computed, nextTick } from 'vue'
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
    // Core app state
    const currentTab = ref('dashboard')
    const user = ref(null)
    const backendStatus = ref('Checking...')
    const phase = ref('1 - Transaction Import')
    const showLoginModal = ref(false)
    
    // Chat state
    const chatInput = ref('')
    const chatHistory = ref([])
    const loading = ref(false)
    const currentThinking = ref('')
    const showWelcomeMessage = ref(true)
    const showHistory = ref(false)
    
    // File upload state
    const transactionCount = ref(0)
    const recentUploads = ref([])
    const fileInput = ref(null)

    // Dynamic API base URL
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

    // Welcome message
    const welcomeText = computed(() => {
      const userName = user.value ? 
        (user.value.displayName || user.value.email.split('@')[0]) : 
        'there'
      return `Hello, ${userName}! I'm here to help you with your financial data. You can ask questions about budgeting, upload CSV files, or explore your transaction categories.`
    })

    // Chat functions
    const toggleHistory = () => {
      showHistory.value = !showHistory.value
    }

const scrollToBottom = async () => {
  await nextTick()
  
  // Wait a bit longer for the DOM to fully update
  setTimeout(() => {
    // Try multiple selectors to find the chat container
    const historyElement = document.querySelector('.chat-messages-simple') || 
                          document.querySelector('.chat-history-simple') ||
                          document.querySelector('.chat-bar-always')
    
    if (historyElement) {
      // Use scrollIntoView for more reliable scrolling
      const lastMessage = historyElement.querySelector('.message-pair-simple:last-child') ||
                         historyElement.querySelector('.current-thinking') ||
                         historyElement.lastElementChild
      
      if (lastMessage) {
        lastMessage.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'end'
        })
      } else {
        // Fallback to scrollTop method
        historyElement.scrollTo({
          top: historyElement.scrollHeight,
          behavior: 'smooth'
        })
      }
    }
  }, 100) // Increased timeout for better reliability
}

    const sendMessage = async (message = null) => {
      const messageText = message || chatInput.value.trim()
      if (!messageText || loading.value) return

      const originalInput = chatInput.value
      loading.value = true
      chatInput.value = ''
      currentThinking.value = 'Thinking...'
      
      // Hide welcome message after first interaction
      showWelcomeMessage.value = false
      
      // Show history when sending message
      showHistory.value = true

      try {
        let headers = {}
        if (user.value) {
          const token = await user.value.getIdToken()
          headers.Authorization = `Bearer ${token}`
        }

        const response = await axios.post(`${API_BASE}/chat/command`, {
          message: messageText
        }, { headers, timeout: 15000 })
        
        const botResponse = response.data.response
        
        // Add to chat history
        chatHistory.value.push({
          message: messageText,
          response: botResponse,
          timestamp: new Date().toLocaleTimeString()
        })
        
        // Scroll to bottom after adding message
        scrollToBottom()
        
        // Keep only last 20 conversations
        if (chatHistory.value.length > 20) {
          chatHistory.value = chatHistory.value.slice(-20)
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
        const errorResponse = `Error: ${error.message}. Please check if the backend is running.`
        
        chatHistory.value.push({
          message: messageText,
          response: errorResponse,
          timestamp: new Date().toLocaleTimeString()
        })

        scrollToBottom()
        chatInput.value = originalInput
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
          
          // Add success message to chat
          chatHistory.value.push({
            message: `File uploaded: ${file.name}`,
            response: `Successfully processed ${file.name} with ${upload.rows} transactions!`,
            timestamp: new Date().toLocaleTimeString()
          })
          
          // Show history and scroll to bottom
          showHistory.value = true
          scrollToBottom()
          showWelcomeMessage.value = false
        }, 2000)
      })
    }

    const showSampleData = () => {
      sendMessage('show me sample CSV format')
    }

    // Navigation functions
    const showTab = (tabName) => {
      currentTab.value = tabName
    }

    // Auth functions
    const handleUserClick = () => {
      if (!user.value) {
        showLoginModal.value = true
      }
    }

    const handleLogout = async () => {
      if (user.value) {
        try {
          await auth.signOut()
          // Add logout message to chat
          chatHistory.value.push({
            message: 'Logout',
            response: "You've been signed out. Sign in again for personalized features!",
            timestamp: new Date().toLocaleTimeString()
          })
          
          // Show history and scroll to bottom
          showHistory.value = true
          scrollToBottom()
          showWelcomeMessage.value = false
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
        
        // Add welcome message to history
        if (chatHistory.value.length === 0) {
          const userName = firebaseUser ? 
            (firebaseUser.displayName || firebaseUser.email.split('@')[0]) : 
            'there'
          
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
      showLoginModal,
      
      // Chat state
      chatInput,
      chatHistory,
      loading,
      currentThinking,
      showWelcomeMessage,
      showHistory,
      welcomeText,
      
      // File upload state
      transactionCount,
      recentUploads,
      fileInput,
      
      // Functions
      toggleHistory,
      sendMessage,
      scrollToBottom,
      triggerFileUpload,
      handleFileSelect,
      handleFileDrop,
      showSampleData,
      showTab,
      handleUserClick,
      handleLogout
    }
  }
}
</script>