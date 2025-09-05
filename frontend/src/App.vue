<template>
  <div id="app">
    <!-- Top Bar -->
    <div class="top-bar">
      <div 
        class="app-logo" 
        :class="{ active: currentTab === 'dashboard' }"
        @click="showTab('dashboard')"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 8px;">
          <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" fill="currentColor"/>
        </svg>
        Financial Dashboard
      </div>
      
      <div class="nav-tabs">
        <div 
          class="nav-tab" 
          :class="{ active: currentTab === 'transactions' }"
          @click="showTab('transactions')"
        >
          Transactions
        </div>
        <div 
          class="nav-tab"
          :class="{ active: currentTab === 'categories' }"
          @click="showTab('categories')"
        >
          Categories
        </div>
        <div 
          class="nav-tab"
          :class="{ active: currentTab === 'timeline' }"
          @click="showTab('timeline')"
        >
          Timeline
        </div>
      </div>
      
      <div class="top-bar-right">
        <div 
          class="settings-icon" 
          :class="{ active: currentTab === 'settings' }"
          @click="showTab('settings')" 
          title="Settings"
        >
          ⚙️
        </div>
        <div class="user-name" @click="handleUserClick">
          {{ user ? (user.displayName || user.email.split('@')[0]) : 'Sign In' }}
        </div>
        <div class="logout-icon" @click="handleLogout" :title="user ? 'Logout' : 'Sign In'">
          {{ user ? '🚪' : '👤' }}
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <div class="content-area">
        <!-- Dashboard Tab - Transaction Import Focus -->
        <div v-if="currentTab === 'dashboard'" class="tab-content">

          <!-- Import Status Cards -->
          <div class="import-status-grid">
            <div class="status-card">
              <div class="status-icon">📥</div>
              <div class="status-info">
                <h3>Data Import</h3>
                <div class="status-value">{{ transactionCount }} transactions</div>
                <div class="status-detail">Ready to import CSV files</div>
              </div>
            </div>
            
            <div class="status-card">
              <div class="status-icon">👤</div>
              <div class="status-info">
                <h3>User Status</h3>
                <div class="status-value">{{ user ? '✅ Signed In' : '❌ Anonymous' }}</div>
                <div class="status-detail">{{ user ? user.email.split('@')[0] : 'Sign in to save data' }}</div>
              </div>
            </div>
            
            <div class="status-card">
              <div class="status-icon">🔗</div>
              <div class="status-info">
                <h3>Connection</h3>
                <div class="status-value">{{ backendStatus }}</div>
                <div class="status-detail">Backend API ready</div>
              </div>
            </div>
          </div>

          <!-- Quick Import Section -->
          <div class="quick-import-section">
            <div class="import-card">
              <div class="import-header">
                <h2>📁 Import Your Financial Data</h2>
                <p>Upload CSV files from your bank or financial institution to get started</p>
              </div>
              
              <div class="import-actions">
                <div class="file-drop-zone" @click="triggerFileUpload" @dragover.prevent @drop.prevent="handleFileDrop">
                  <div class="drop-zone-content">
                    <div class="upload-icon">📄</div>
                    <h3>Drag & Drop CSV Files</h3>
                    <p>Or click to browse and select files</p>
                    <div class="supported-formats">
                      <span>Supported: .csv, .xlsx</span>
                    </div>
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
                
                <div class="import-options">
                  <button class="import-btn primary" @click="triggerFileUpload">
                    📥 Choose Files
                  </button>
                  <button class="import-btn secondary" @click="showSampleData">
                    👁️ View Sample
                  </button>
                  <button class="import-btn secondary" @click="sendMessage('help import')">
                    ❓ Import Help
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Activity -->
          <div class="recent-activity">
            <h3>Recent Activity</h3>
            <div class="activity-list">
              <div v-if="recentUploads.length === 0" class="no-activity">
                No recent imports. Upload your first CSV file to get started!
              </div>
              <div v-for="upload in recentUploads" :key="upload.id" class="activity-item">
                <div class="activity-icon">{{ upload.status === 'success' ? '✅' : '⏳' }}</div>
                <div class="activity-details">
                  <div class="activity-title">{{ upload.filename }}</div>
                  <div class="activity-meta">{{ upload.timestamp }} • {{ upload.rows }} rows</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Transactions Tab -->
        <div v-else-if="currentTab === 'transactions'" class="tab-content">
          <div class="transactions-header">
            <h2>💳 Transaction Management</h2>
            <div class="transaction-stats">
              <span>Total: {{ transactionCount }} transactions</span>
              <span>•</span>
              <span>User: {{ user ? user.email.split('@')[0] : 'Guest' }}</span>
            </div>
          </div>

          <div class="transactions-content">
            <div class="placeholder-section">
              <div class="placeholder-title">Import & Manage Transactions</div>
              <div class="placeholder-text">
                Upload CSV files from your bank to automatically categorize and analyze your spending patterns.
              </div>
              <button class="placeholder-button" @click="showTab('dashboard')">
                📥 Start Import
              </button>
            </div>

            <div class="placeholder-section">
              <div class="placeholder-title">Smart Categorization</div>
              <div class="placeholder-text">
                AI-powered transaction categorization with manual override capabilities.
              </div>
            </div>
          </div>
        </div>

        <!-- Categories Tab -->
        <div v-else-if="currentTab === 'categories'" class="tab-content">
          <div class="categories-layout">
            <div class="category-tree">
              <h3>Category Hierarchy</h3>
              <div class="category-item selected">🍽️ Food & Dining</div>
              <div class="category-item" style="padding-left: 32px;">🏪 Restaurants</div>
              <div class="category-item" style="padding-left: 32px;">🛒 Groceries</div>
              <div class="category-item">🚗 Transportation</div>
              <div class="category-item" style="padding-left: 32px;">⛽ Gas</div>
              <div class="category-item" style="padding-left: 32px;">🚌 Public Transit</div>
              <div class="category-item">🏠 Housing</div>
              <div class="category-item">💼 Business</div>
              <div class="category-item">🎯 Goals</div>
            </div>
            
            <div class="category-details">
              <h3>Smart Categorization</h3>
              <p>
                {{ user ? `Personalized categories for ${user.email.split('@')[0]}` : 'Sign in to create custom categories' }}
              </p>
              
              <div style="display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap;">
                <button class="placeholder-button">Split Category</button>
                <button class="placeholder-button">Merge Categories</button>
                <button class="placeholder-button">Add Rule</button>
              </div>
              
              <div class="chart-placeholder" style="height: 200px;">
                📊<br>
                Category Analytics<br>
                <small>Import transactions to see category breakdown</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Timeline Tab -->
        <div v-else-if="currentTab === 'timeline'" class="tab-content">
          <div class="timeline-controls">
            <div class="timeline-control active">Month</div>
            <div class="timeline-control">Quarter</div>
            <div class="timeline-control">Year</div>
            <span style="margin-left: 20px; color: rgba(139, 69, 19, 0.7);">
              {{ user ? `Timeline for ${user.email.split('@')[0]}` : 'Sign in for personalized timeline' }}
            </span>
          </div>

          <div class="chart-placeholder" style="height: 400px; margin-bottom: 24px;">
            📈<br>
            Interactive Financial Timeline<br>
            <small>Import transaction data to see your financial timeline</small>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div class="placeholder-section">
              <div class="placeholder-title">Financial Goals</div>
              <div class="placeholder-text">
                Set and track financial goals after importing your transaction data.
              </div>
            </div>
            
            <div class="placeholder-section">
              <div class="placeholder-title">Scenario Planning</div>
              <div class="placeholder-text">Create what-if scenarios for your financial future.</div>
              <button class="placeholder-button">Create Scenario</button>
            </div>
          </div>
        </div>

        <!-- Settings Tab - System Information Moved Here -->
        <div v-else-if="currentTab === 'settings'" class="tab-content">
          <div class="settings-layout">
            <div class="settings-main">
              <h2>⚙️ Settings & System Status</h2>
              
              <!-- System Status Section -->
              <div class="settings-section">
                <h3>🔧 System Status</h3>
                <div class="system-indicators">
                  <div class="system-card">
                    <h4>Authentication</h4>
                    <div class="value">{{ user ? '✅ Signed In' : '❌ Anonymous' }}</div>
                    <div class="detail">{{ user ? user.email : 'Not authenticated' }}</div>
                  </div>
                  <div class="system-card">
                    <h4>Backend Status</h4>
                    <div class="value">{{ backendStatus }}</div>
                    <div class="detail">API Connection</div>
                  </div>
                  <div class="system-card">
                    <h4>Phase Progress</h4>
                    <div class="value">{{ phase }}</div>
                    <div class="detail">Current Development Phase</div>
                  </div>
                  <div class="system-card">
                    <h4>Database</h4>
                    <div class="value">🔄 Phase 2</div>
                    <div class="detail">Coming Soon</div>
                  </div>
                </div>
              </div>

              <!-- User Profile Section -->
              <div class="settings-section">
                <h3>👤 User Profile</h3>
                <div class="user-profile">
                  <div v-if="user" class="profile-info">
                    <p><strong>Email:</strong> {{ user.email }}</p>
                    <p><strong>UID:</strong> {{ user.uid.substring(0, 16) }}...</p>
                    <p><strong>Display Name:</strong> {{ user.displayName || 'Not set' }}</p>
                    <button class="settings-button" @click="handleLogout">Sign Out</button>
                  </div>
                  <div v-else class="profile-info">
                    <p>Sign in to access personalized features and secure data storage.</p>
                    <button class="settings-button" @click="showLoginModal = true">Sign In</button>
                  </div>
                </div>
              </div>

              <!-- Data Management Section -->
              <div class="settings-section">
                <h3>📊 Data Management</h3>
                <div class="data-actions">
                  <button class="settings-button">📥 Import Data</button>
                  <button class="settings-button">📤 Export Data</button>
                  <button class="settings-button">🗑️ Clear All Data</button>
                  <button class="settings-button">🔄 Reset Categories</button>
                </div>
              </div>

              <!-- Development Info -->
              <div class="settings-section">
                <h3>🔮 Next Phase Preview</h3>
                <div class="phase-preview">
                  <div class="preview-item">🔜 Database Integration (NeonDB)</div>
                  <div class="preview-item">🔜 Transaction Table Storage</div>
                  <div class="preview-item">🔜 Audit Logging</div>
                  <div class="preview-item">🔜 CSV Import Processing</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Bar -->
    <div class="chat-bar">
      <div v-if="chatResponse" class="chat-response">
        {{ chatResponse }}
      </div>
      
      <div class="chat-input-container">
        <button class="expand-history" @click="toggleChatHistory" :class="{ active: showChatHistory }">
          {{ showChatHistory ? '↓' : '↑' }}
        </button>
        <input 
          type="text" 
          class="chat-input" 
          placeholder="Ask me anything about importing transactions..."
          v-model="chatInput"
          @keypress.enter="sendMessage()"
        >
        <button class="send-button" @click="sendMessage()">
          ➤
        </button>
      </div>

      <!-- Chat History Panel -->
      <div v-if="showChatHistory" class="chat-history">
        <div class="chat-history-header">
          <h4>Recent Conversations</h4>
          <button @click="clearChatHistory" class="clear-history">Clear</button>
        </div>
        <div class="chat-history-items">
          <div v-if="chatHistory.length === 0" class="no-history">
            No conversation history yet. Start chatting to see your messages here!
          </div>
          <div v-for="(item, index) in chatHistory" :key="index" class="history-item">
            <div class="history-message user">{{ item.message }}</div>
            <div class="history-message bot">{{ item.response }}</div>
          </div>
        </div>
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

export default {
  name: 'App',
  components: {
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
    const showChatHistory = ref(false)
    const transactionCount = ref(0)
    const recentUploads = ref([])
    const chatHistory = ref([])
    const fileInput = ref(null)

    // Dynamic API base URL
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

    // Check backend health
    const checkBackend = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`, { timeout: 10000 })
        backendStatus.value = 'Connected ✅'
        phase.value = response.data.phase || 'Phase 1'
        console.log('✅ Backend connected:', response.data)
      } catch (error) {
        backendStatus.value = 'Disconnected ❌'
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
        chatInput.value = originalInput // Restore input on error
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
        
        // Add to recent uploads (mock for now)
        const upload = {
          id: Date.now() + index,
          filename: file.name,
          status: 'processing',
          rows: Math.floor(Math.random() * 1000) + 100,
          timestamp: new Date().toLocaleTimeString()
        }
        
        recentUploads.value.unshift(upload)
        
        // Simulate processing
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

    const toggleChatHistory = () => {
      showChatHistory.value = !showChatHistory.value
    }

    const clearChatHistory = () => {
      chatHistory.value = []
      chatResponse.value = ''
    }

    // Other functions
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
      })
    })

    return {
      currentTab,
      user,
      chatInput,
      chatResponse,
      backendStatus,
      phase,
      showLoginModal,
      showChatHistory,
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
      toggleChatHistory,
      clearChatHistory
    }
  }
}
</script>

<style>
@import './assets/styles.css';

/* Component-specific styles can be added here if needed */
.chat-bar {
    position: relative;
}

.file-drop-zone.dragover {
    border-color: rgba(139, 69, 19, 0.6);
    background: rgba(255, 255, 255, 0.4);
    transform: scale(1.02);
}

.status-card.processing {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.8; }
    100% { opacity: 1; }
}
</style>