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
        <div class="user-name">{{ user.name }}</div>
        <div class="logout-icon" @click="logout" title="Logout">🚪</div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <div class="content-area">
        <!-- Dashboard Tab -->
        <div v-if="currentTab === 'dashboard'" class="tab-content">
          <div class="dashboard-grid">
            <div class="kpi-card">
              <h3>Net Cashflow (MTD)</h3>
              <div class="value">+$2,340</div>
            </div>
            <div class="kpi-card">
              <h3>Total Expenses</h3>
              <div class="value">$4,567</div>
            </div>
            <div class="kpi-card">
              <h3>Savings Rate</h3>
              <div class="value">23%</div>
            </div>
            <div class="kpi-card">
              <h3>Goals On-Track</h3>
              <div class="value">2/3</div>
            </div>
          </div>

          <div class="chart-section">
            <div class="chart-title">Expenses vs Income (12 months + forecast)</div>
            <div class="chart-placeholder">
              📊<br>
              Chart.js Integration Coming Soon<br>
              <small>Connected to backend: {{ backendStatus }}</small>
            </div>
          </div>
        </div>

        <!-- Other Tabs -->
        <div v-else-if="currentTab === 'transactions'" class="tab-content">
          <div class="placeholder-section">
            <div class="placeholder-title">Import Your Bank Data</div>
            <div class="placeholder-text">Upload CSV files from your bank to get started.</div>
            <button class="placeholder-button" @click="sendMessage('import transactions')">
              Upload CSV File
            </button>
          </div>
        </div>

        <div v-else-if="currentTab === 'categories'" class="tab-content">
          <div class="placeholder-section">
            <div class="placeholder-title">Category Management</div>
            <div class="placeholder-text">Create and organize your spending categories.</div>
          </div>
        </div>

        <div v-else-if="currentTab === 'timeline'" class="tab-content">
          <div class="placeholder-section">
            <div class="placeholder-title">Financial Timeline</div>
            <div class="placeholder-text">Visualize your financial journey over time.</div>
          </div>
        </div>

        <div v-else-if="currentTab === 'settings'" class="tab-content">
          <div class="placeholder-section">
            <div class="placeholder-title">Settings</div>
            <div class="placeholder-text">Backend Status: {{ backendStatus }}</div>
            <div class="placeholder-text">Phase: {{ phase }}</div>
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
          placeholder="Ask me anything (e.g., 'Save 3000 by December' or 'Import transactions')..."
          v-model="chatInput"
          @keypress.enter="sendMessage()"
        >
        <button class="send-button" @click="sendMessage()">
          ➤
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'App',
  setup() {
    const currentTab = ref('dashboard')
    const chatInput = ref('')
    const chatResponse = ref('')
    const backendStatus = ref('Checking...')
    const phase = ref('0')
    const user = ref({ name: 'Alexa' })

    const API_BASE = 'http://localhost:8001'

    // Check backend health on startup
    const checkBackend = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`)
        backendStatus.value = 'Connected ✅'
        phase.value = response.data.phase || '0'
      } catch (error) {
        backendStatus.value = 'Disconnected ❌'
        console.error('Backend connection failed:', error)
      }
    }

    // Send chat message
    const sendMessage = async (message = null) => {
      const messageText = message || chatInput.value.trim()
      if (!messageText) return

      chatInput.value = ''
      chatResponse.value = 'Thinking...'

      try {
        const response = await axios.post(`${API_BASE}/chat/command`, {
          message: messageText
        })
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

    const logout = () => {
      alert('Logout functionality coming in next phase!')
    }

    // Initialize on component mount
    onMounted(() => {
      checkBackend()
      // Show welcome message after 2 seconds
      setTimeout(() => {
        chatResponse.value = "Welcome! I'm your AI finance assistant. Try asking me to 'Save 3000 by December for vacation' or 'Import transactions' to see how I work!"
      }, 2000)
    })

    return {
      currentTab,
      chatInput,
      chatResponse,
      backendStatus,
      phase,
      user,
      sendMessage,
      showTab,
      logout
    }
  }
}
</script>

<style>
/* Import your existing styles */
@import '@/assets/styles.css';
</style>