<template>
  <div id="app">
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
        <span class="text-medium" @click="handleUserClick">
          {{ user ? (user.displayName || user.email.split('@')[0]) : 'Sign In' }}
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

        <div class="container container-large">
          <div class="section-header text-center">
            <div class="text-large">Import Your Financial Data</div>
            <div class="text-medium text-light">Upload CSV files from your bank or financial institution</div>
          </div>
          
          <div 
            class="drop-zone" 
            @click="triggerFileUpload"
            @drop.prevent="handleFileDrop"
            @dragover.prevent
            @dragenter.prevent
            :class="{ 'drop-active': isDragging }"
            @dragenter="isDragging = true"
            @dragleave="isDragging = false"
          >
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
        <!-- Import Section -->
        <div class="container container-large">
          <div class="section-header text-center">
            <div class="text-large">Import & Manage Transactions</div>
            <div class="text-medium text-light">Upload CSV files from your bank or financial institution</div>
          </div>
          
          <div 
            class="drop-zone" 
            @click="triggerFileUpload"
            @drop.prevent="handleFileDrop"
            @dragover.prevent
            @dragenter.prevent
            :class="{ 'drop-active': isDragging }"
            @dragenter="isDragging = true"
            @dragleave="isDragging = false"
          >
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
          </div>
        </div>

        <!-- Recent Uploads -->
        <div class="container" v-if="recentUploads.length > 0">
          <div class="text-medium section-header">Recent Imports</div>
          <div class="flex-column flex-gap-sm">
            <div v-for="upload in recentUploads" :key="upload.id" class="card flex flex-gap">
              <div class="status-icon">{{ upload.status === 'success' ? '✅' : upload.status === 'error' ? '❌' : '⏳' }}</div>
              <div>
                <div class="text-medium">{{ upload.filename }}</div>
                <div class="text-small text-light">{{ upload.timestamp }} • {{ upload.rows }} rows</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Transaction Management -->
        <div class="container">
          <div class="flex flex-between flex-wrap">
            <div class="text-medium section-header">Transaction History ({{ transactionCount }} total)</div>
            <div class="flex flex-gap">
              <button class="btn" @click="refreshTransactions">
                <AppIcon name="refresh" size="medium" />
                Refresh
              </button>
            </div>
          </div>
          
          <!-- Filters -->
          <div class="flex flex-gap flex-wrap">
            <input 
              type="date" 
              v-model="filters.startDate" 
              class="chat-input-always"
              placeholder="Start Date"
            >
            <input 
              type="date" 
              v-model="filters.endDate" 
              class="chat-input-always"
              placeholder="End Date"
            >
            <input 
              type="text" 
              v-model="filters.merchant" 
              class="chat-input-always"
              placeholder="Search merchant..."
            >
            <select v-model="filters.categoryId" class="chat-input-always">
              <option value="">All Categories</option>
              <option v-for="category in allCategories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </div>
        </div>

        <!-- Transactions Table -->
        <div class="container">
          <div v-if="loading" class="text-center">
            Loading transactions...
          </div>
          <div v-else-if="transactions.length === 0" class="text-center text-light">
            No transactions found. Upload CSV files to get started.
          </div>
          <div v-else class="transactions-table">
            <div class="transaction-row header">
              <div class="col-date">Date</div>
              <div class="col-merchant">Merchant</div>
              <div class="col-amount">Amount</div>
              <div class="col-category">Category</div>
              <div class="col-actions">Actions</div>
            </div>
            <div 
              v-for="transaction in transactions" 
              :key="transaction.id"
              class="transaction-row"
            >
              <div class="col-date">
                {{ formatDate(transaction.posted_at) }}
              </div>
              <div class="col-merchant">
                <div class="text-medium">{{ transaction.merchant || 'Unknown' }}</div>
                <div class="text-small text-light">{{ transaction.memo }}</div>
              </div>
              <div class="col-amount" :class="{ 'negative': parseFloat(transaction.amount) < 0 }">
                {{ formatAmount(transaction.amount) }}
              </div>
              <div class="col-category">
                <div v-if="transaction.category_name" class="category-tag">
                  <AppIcon :name="getCategoryIcon(transaction.category_id)" size="small" />
                  {{ transaction.category_name }}
                </div>
                <select 
                  v-else 
                  @change="categorizeTransaction(transaction.id, $event.target.value)"
                  class="category-select"
                >
                  <option value="">Select category...</option>
                  <option v-for="category in allCategories" :key="category.id" :value="category.id">
                    {{ category.name }}
                  </option>
                </select>
              </div>
              <div class="col-actions">
                <button class="btn btn-small" @click="editTransaction(transaction)">
                  <AppIcon name="edit" size="small" />
                </button>
              </div>
            </div>
          </div>
          
          <!-- Pagination -->
          <div class="flex flex-center flex-gap" v-if="transactions.length > 0">
            <button 
              class="btn" 
              @click="changePage(currentPage - 1)"
              :disabled="currentPage <= 1"
            >
              Previous
            </button>
            <span class="text-medium">Page {{ currentPage }}</span>
            <button 
              class="btn" 
              @click="changePage(currentPage + 1)"
              :disabled="transactions.length < pageSize"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      <!-- Categories Tab -->
      <div v-else-if="currentTab === 'categories'" class="tab-content">
        <div class="grid grid-sidebar">
          <!-- Category Tree -->
          <div class="container">
            <div class="text-medium section-header">Categories</div>
            <div class="flex-column">
              <div v-for="mainCategory in categoriesData" :key="mainCategory.id" class="category-group">
                <button 
                  class="category-btn"
                  :class="{ 'active': selectedCategory?.id === mainCategory.id }"
                  @click="selectCategory(mainCategory)"
                >
                  <AppIcon :name="mainCategory.icon" size="medium" />
                  <span>{{ mainCategory.name }}</span>
                </button>
                
                <!-- Subcategories for Expenses -->
                <div v-if="mainCategory.id === 'expenses'" class="subcategories">
                  <div v-for="categoryType in expenseCategories" :key="categoryType.name" class="category-type">
                    <div class="category-type-header">{{ categoryType.name }}</div>
                    <button 
                      v-for="subcategory in categoryType.subcategories"
                      :key="subcategory.id"
                      class="category-btn category-indent"
                      :class="{ 'active': selectedCategory?.id === subcategory.id }"
                      @click="selectCategory(subcategory)"
                    >
                      <AppIcon :name="subcategory.icon" size="medium" />
                      <span>{{ subcategory.name }}</span>
                    </button>
                  </div>
                </div>
                
                <!-- Regular subcategories for other categories -->
                <div v-else-if="mainCategory.children" class="subcategories">
                  <button 
                    v-for="subcategory in mainCategory.children"
                    :key="subcategory.id"
                    class="category-btn category-indent"
                    :class="{ 'active': selectedCategory?.id === subcategory.id }"
                    @click="selectCategory(subcategory)"
                  >
                    <AppIcon :name="subcategory.icon" size="medium" />
                    <span>{{ subcategory.name }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Category Details -->
          <div class="container">
            <div v-if="selectedCategory" class="flex-column flex-gap">
              <div class="flex flex-gap">
                <AppIcon :name="selectedCategory.icon" size="large" />
                <div>
                  <div class="text-large">{{ selectedCategory.name }}</div>
                  <div class="text-small text-light">
                    {{ selectedCategory.category || selectedCategory.name }} Category
                  </div>
                </div>
              </div>
              
              <div class="flex flex-gap flex-wrap">
                <button class="btn">Edit Category</button>
                <button class="btn">Add Rule</button>
                <button class="btn">View Transactions</button>
              </div>
              
              <div class="container text-center" style="height: 12.5rem;">
                <div class="text-medium">Category Analytics</div>
                <div class="text-small text-light">
                  Transaction data will show spending patterns for this category
                </div>
              </div>
            </div>
            
            <div v-else class="text-center text-light">
              Select a category to view details
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
          <div class="text-medium">Timeline visualization coming soon</div>
          <div class="text-small text-light">Import transactions to see spending trends over time</div>
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
            <button class="btn" @click="showTab('dashboard')">Import Data</button>
            <button class="btn">Export Data</button>
            <button class="btn">Clear All Data</button>
            <button class="btn">Reset Categories</button>
          </div>
        </div>
      </div>
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

    <!-- Login Modal -->
    <LoginModal :showModal="showLoginModal" @close="showLoginModal = false" />
  </div>
</template>

<script>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import axios from 'axios'
import { auth } from '@/firebase/config'
import { onAuthStateChanged } from 'firebase/auth'
import LoginModal from '@/components/LoginModal.vue'
import AppIcon from '@/components/AppIcon.vue'
import { categoriesData, getCategoryById, getAllExpenseCategories } from '@/data/categories.js'

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
    const loading = ref(false)
    
    // Chat state
    const chatInput = ref('')
    const chatHistory = ref([])
    const currentThinking = ref('')
    const showWelcomeMessage = ref(true)
    const showHistory = ref(false)
    const showChat = ref(false)
    
    // File upload state
    const transactionCount = ref(0)
    const recentUploads = ref([])
    const fileInput = ref(null)
    const isDragging = ref(false)
    
    // Transactions state
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
    
    const expenseCategories = computed(() => getAllExpenseCategories())
    
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
          currentTab.value = 'dashboard'
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
      isDragging.value = false
      const files = event.dataTransfer.files
      processFiles(files)
    }

    const processFiles = async (files) => {
      if (!files || files.length === 0) return
      
      if (!user.value) {
        showLoginModal.value = true
        return
      }

      for (const file of Array.from(files)) {
        console.log('Processing file:', file.name)
        
        const upload = {
          id: Date.now() + Math.random(),
          filename: file.name,
          status: 'processing',
          rows: 0,
          timestamp: new Date().toLocaleTimeString()
        }
        
        recentUploads.value.unshift(upload)
        
        try {
          const formData = new FormData()
          formData.append('file', file)
          formData.append('account_name', 'Default Account')
          formData.append('account_type', 'checking')
          
          const token = await user.value.getIdToken()
          const response = await axios.post(`${API_BASE}/transactions/import`, formData, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            }
          })
          
          upload.status = 'success'
          upload.rows = response.data.summary.rows_inserted || 0
          transactionCount.value += upload.rows
          
          // Add success message to chat
          chatHistory.value.push({
            message: `File uploaded: ${file.name}`,
            response: `Successfully processed ${file.name} with ${upload.rows} transactions imported!`,
            timestamp: new Date().toLocaleTimeString()
          })
          
          showHistory.value = true
          scrollToBottom()
          showWelcomeMessage.value = false
          
          // Refresh transactions if on that tab
          if (currentTab.value === 'transactions') {
            loadTransactions()
          }
          
        } catch (error) {
          upload.status = 'error'
          console.error('Upload failed:', error)
          
          chatHistory.value.push({
            message: `File upload: ${file.name}`,
            response: `Upload failed: ${error.response?.data?.detail || error.message}`,
            timestamp: new Date().toLocaleTimeString()
          })
          
          showHistory.value = true
          scrollToBottom()
        }
      }
    }

    const showSampleData = () => {
      sendMessage('show me sample CSV format')
    }

    // Transaction functions
    const loadTransactions = async () => {
      if (!user.value) return
      
      loading.value = true
      try {
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
        
        const response = await axios.get(`${API_BASE}/transactions/list?${params}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        transactions.value = response.data
      } catch (error) {
        console.error('Failed to load transactions:', error)
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
      }
    }

    const editTransaction = (transaction) => {
      console.log('Edit transaction:', transaction)
      // TODO: Implement transaction editing
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
    const handleUserClick = () => {
      if (!user.value) {
        showLoginModal.value = true
      }
    }

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
      loading,
      
      // Chat state
      chatInput,
      chatHistory,
      currentThinking,
      showWelcomeMessage,
      showHistory,
      showChat,
      welcomeText,
      
      // File upload state
      transactionCount,
      recentUploads,
      fileInput,
      isDragging,
      
      // Transaction state
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
      triggerFileUpload,
      handleFileSelect,
      handleFileDrop,
      loadTransactions,
      refreshTransactions,
      changePage,
      categorizeTransaction,
      editTransaction,
      selectCategory,
      getCategoryIcon,
      formatDate,
      formatAmount,
      showTab,
      handleUserClick,
      handleLogout
    }
  }
}
</script>