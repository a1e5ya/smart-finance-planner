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
        <!-- Dashboard Tab -->
        <div v-if="currentTab === 'dashboard'" class="tab-content">
          <div class="dashboard-grid">
            <div class="kpi-card">
              <h3>Authentication</h3>
              <div class="value">{{ user ? '✅ Signed In' : '❌ Anonymous' }}</div>
            </div>
            <div class="kpi-card">
              <h3>Backend Status</h3>
              <div class="value">{{ backendStatus }}</div>
            </div>
            <div class="kpi-card">
              <h3>Phase Progress</h3>
              <div class="value">{{ phase }}</div>
            </div>
            <div class="kpi-card">
              <h3>User</h3>
              <div class="value">{{ user ? user.email.split('@')[0] : 'Guest' }}</div>
            </div>
          </div>

          <div class="chart-section">
            <div class="chart-title">Phase 1 Complete: Authentication + Chat Integration</div>
            <div class="chart-placeholder">
              <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
              <strong>Working Features:</strong><br>
              ✅ Firebase Authentication (Email/Password)<br>
              ✅ Frontend ↔ Backend Auth Token Flow<br>
              ✅ Personalized Chat Responses<br>
              ✅ User Session Management<br>
              <small style="margin-top: 12px; display: block;">
                Backend Status: {{ backendStatus }} | User: {{ user ? user.email : 'Anonymous' }}
              </small>
            </div>
          </div>

          <!-- Quick Actions -->
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 20px;">
            <div class="placeholder-section">
              <div class="placeholder-title">Test Authentication</div>
              <div class="placeholder-text">
                {{ user ? `Signed in as ${user.email}` : 'Sign in to test personalized features' }}
              </div>
              <button v-if="!user" class="placeholder-button" @click="showLoginModal = true">
                Sign In / Sign Up
              </button>
              <button v-else class="placeholder-button" @click="sendMessage('test auth')">
                Test Auth Flow
              </button>
            </div>
            
            <div class="placeholder-section">
              <div class="placeholder-title">Try Smart Chat</div>
              <div class="placeholder-text">Chat responses adapt based on your authentication status</div>
              <div style="display: flex; gap: 8px; flex-wrap: wrap; justify-content: center;">
                <button class="placeholder-button" @click="sendMessage('hello')">Say Hello</button>
                <button class="placeholder-button" @click="sendMessage('save 3000 for vacation')">Set Goal</button>
                <button class="placeholder-button" @click="sendMessage('help')">Get Help</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Transactions Tab -->
        <div v-else-if="currentTab === 'transactions'" class="tab-content">
          <div class="placeholder-section">
            <div class="placeholder-title">Import Your Bank Data</div>
            <div class="placeholder-text">
              {{ user ? `Ready to import data for ${user.email.split('@')[0]}` : 'Sign in to save your imported data' }}
            </div>
            <button class="placeholder-button" @click="sendMessage('import transactions')">
              Upload CSV File
            </button>
          </div>

          <div class="placeholder-section">
            <div class="placeholder-title">Transaction Management</div>
            <div class="placeholder-text">View, categorize, and analyze your transactions with ML-powered insights.</div>
          </div>
        </div>

        <!-- Categories Tab -->
        <div v-else-if="currentTab === 'categories'" class="tab-content">
          <div class="categories-layout">
            <div class="category-tree">
              <h3 style="margin-bottom: 16px; color: rgba(139, 69, 19, 1); text-transform: uppercase; letter-spacing: 1px;">Category Hierarchy</h3>
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
              <h3 style="margin-bottom: 16px;">Smart Categorization</h3>
              <p style="margin-bottom: 16px;">
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
                <small>ML-powered transaction categorization</small>
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
            <small>Past transactions • Future forecasts • Goal tracking</small>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div class="placeholder-section">
              <div class="placeholder-title">Financial Goals</div>
              <div class="placeholder-text">
                🎯 Vacation Fund: $1,200 / $3,000<br>
                🏠 House Down Payment: $15,000 / $50,000
              </div>
            </div>
            
            <div class="placeholder-section">
              <div class="placeholder-title">Scenario Planning</div>
              <div class="placeholder-text">Create what-if scenarios for your financial future.</div>
              <button class="placeholder-button">Create Scenario</button>
            </div>
          </div>
        </div>

        <!-- Settings Tab -->
        <div v-else-if="currentTab === 'settings'" class="tab-content">
          <div class="settings-layout">
            <div class="settings-main">
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
                <div class="placeholder-section">
                  <div class="placeholder-title">User Profile</div>
                  <div class="placeholder-text">
                    {{ user ? `Email: ${user.email}` : 'Not signed in' }}<br>
                    {{ user ? `UID: ${user.uid.substring(0, 8)}...` : '' }}<br>
                    Phase: 1 - Authentication Complete
                  </div>
                  <button v-if="!user" class="placeholder-button" @click="showLoginModal = true">
                    Sign In
                  </button>
                </div>
                
                <div class="placeholder-section">
                  <div class="placeholder-title">System Status</div>
                  <div class="placeholder-text">
                    Backend: {{ backendStatus }}<br>
                    Database: Coming in Phase 2<br>
                    ML Models: Coming in Phase 3
                  </div>
                </div>
                
                <div class="placeholder-section">
                  <div class="placeholder-title">Data Management</div>
                  <div class="placeholder-text">Export data, import historical files, backup settings</div>
                  <button class="placeholder-button">Export All Data</button>
                </div>
                
                <div class="placeholder-section">
                  <div class="placeholder-title">Next Phase Preview</div>
                  <div class="placeholder-text">
                    🔜 Database Integration (NeonDB)<br>
                    🔜 Audit Logging<br>
                    🔜 Live Deployment
                  </div>
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
        <button class="expand-history">↑</button>
        <input 
          type="text" 
          class="chat-input" 
          placeholder="Ask me anything! Try: 'hello', 'test auth', 'save 3000 for vacation'..."
          v-model="chatInput"
          @keypress.enter="sendMessage()"
        >
        <button class="send-button" @click="sendMessage()">
          ➤
        </button>
      </div>
    </div>

    <!-- Login Modal -->
    <LoginModal :showModal="showLoginModal" @close="showLoginModal = false" />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
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
    const phase = ref('1 - Auth Complete')
    const showLoginModal = ref(false)

    const API_BASE = 'http://localhost:8001'

    // Check backend health
    const checkBackend = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`)
        backendStatus.value = 'Connected ✅'
        phase.value = response.data.phase || '1'
      } catch (error) {
        backendStatus.value = 'Disconnected ❌'
      }
    }

    // Send chat message with auth token
    const sendMessage = async (message = null) => {
      const messageText = message || chatInput.value.trim()
      if (!messageText) return

      chatInput.value = ''
      chatResponse.value = 'Thinking...'

      try {
        // Prepare headers with auth token
        let headers = {}
        if (user.value) {
          const token = await user.value.getIdToken()
          headers.Authorization = `Bearer ${token}`
        }

        const response = await axios.post(`${API_BASE}/chat/command`, {
          message: messageText
        }, { headers })
        
        chatResponse.value = response.data.response
        
        // Handle navigation commands
        if (messageText.toLowerCase().includes('dashboard')) {
          currentTab.value = 'dashboard'
        } else if (messageText.toLowerCase().includes('import') || messageText.toLowerCase().includes('upload')) {
          currentTab.value = 'transactions'
        } else if (messageText.toLowerCase().includes('categor')) {
          currentTab.value = 'categories'
        } else if (messageText.toLowerCase().includes('timeline')) {
          currentTab.value = 'timeline'
        }
        
      } catch (error) {
        chatResponse.value = 'Sorry, I couldn\'t connect to the backend. Please check if the server is running on port 8001.'
        console.error('Chat request failed:', error)
      }
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
          chatResponse.value = "You've been signed out. Your session data is cleared. Sign in again for personalized features!"
        } catch (error) {
          console.error('Logout error:', error)
        }
      } else {
        showLoginModal.value = true
      }
    }

    // Initialize Firebase auth listener
    onMounted(() => {
      checkBackend()
      
      // Firebase auth state listener
      onAuthStateChanged(auth, (firebaseUser) => {
        user.value = firebaseUser
        console.log('Auth state changed:', firebaseUser ? firebaseUser.email : 'signed out')
      })

      setTimeout(() => {
        chatResponse.value = "🎉 Phase 1 Complete! Authentication system working. Try signing in and test personalized chat responses!"
      }, 2000)
    })

    return {
      currentTab,
      user,
      chatInput,
      chatResponse,
      backendStatus,
      phase,
      showLoginModal,
      sendMessage,
      showTab,
      handleUserClick,
      handleLogout
    }
  }
}
</script>

<style>
@import './assets/styles.css';

.settings-layout {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
}

.categories-layout {
    display: grid;
    grid-template-columns: 240px 1fr;
    gap: 16px;
}

.category-tree {
    backdrop-filter: blur(20px);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.25));
    border-radius: 20px;
    padding: 16px;
    box-shadow: 0 10px 25px rgba(139, 69, 19, 0.1), 0 5px 12px rgba(139, 69, 19, 0.06);
}

.category-item {
    padding: 8px 12px;
    margin: 3px 0;
    border-radius: 14px;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    color: rgba(40, 25, 22, 0.9);
    display: flex;
    align-items: center;
    font-size: 13px;
}

.category-item:hover {
    background: rgba(255, 255, 255, 0.5);
}

.category-item.selected {
    background: linear-gradient(135deg, #8b4513, #a0522d);
    color: white;
    box-shadow: 0 6px 15px rgba(139, 69, 19, 0.25);
}

.category-details {
    backdrop-filter: blur(20px);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.25));
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 10px 25px rgba(139, 69, 19, 0.1), 0 5px 12px rgba(139, 69, 19, 0.06);
}

.timeline-controls {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    align-items: center;
}

.timeline-control {
    padding: 8px 14px;
    backdrop-filter: blur(20px);
    background: rgba(255, 255, 255, 0.4);
    border: none;
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    color: rgba(139, 69, 19, 0.8);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    font-size: 12px;
}

.timeline-control:hover {
    background: rgba(255, 255, 255, 0.6);
}

.timeline-control.active {
    background: linear-gradient(135deg, #8b4513, #a0522d);
    color: white;
    box-shadow: 0 6px 15px rgba(139, 69, 19, 0.25);
}

@media (max-width: 1200px) {
    .categories-layout {
        grid-template-columns: 1fr;
    }
}
</style>