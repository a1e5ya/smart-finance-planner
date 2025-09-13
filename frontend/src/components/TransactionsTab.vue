<template>
  <div class="tab-content">
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

    <!-- Transaction Stats -->
    <div class="container" v-if="transactionCount > 0">
      <div class="grid grid-auto">
        <div class="card flex flex-gap">
          <div>
            <div class="text-small text-muted">Total Transactions</div>
            <div class="text-medium">{{ transactionCount }}</div>
            <div class="text-small text-light">Imported and ready for analysis</div>
          </div>
        </div>
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
          <button class="btn" @click="$emit('refresh-transactions')">
            <AppIcon name="refresh" size="medium" />
            Refresh
          </button>
        </div>
      </div>
      
      <!-- Filters -->
      <div class="flex flex-gap flex-wrap">
        <input 
          type="date" 
          :value="filters.startDate"
          @input="updateFilter('startDate', $event.target.value)"
          class="chat-input-always"
          placeholder="Start Date"
        >
        <input 
          type="date" 
          :value="filters.endDate"
          @input="updateFilter('endDate', $event.target.value)"
          class="chat-input-always"
          placeholder="End Date"
        >
        <input 
          type="text" 
          :value="filters.merchant"
          @input="updateFilter('merchant', $event.target.value)"
          class="chat-input-always"
          placeholder="Search merchant..."
        >
        <select 
          :value="filters.categoryId"
          @change="updateFilter('categoryId', $event.target.value)"
          class="chat-input-always"
        >
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
              @change="$emit('categorize-transaction', transaction.id, $event.target.value)"
              class="category-select"
            >
              <option value="">Select category...</option>
              <option v-for="category in allCategories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </div>
          <div class="col-actions">
            <button class="btn btn-small" @click="$emit('edit-transaction', transaction)">
              <AppIcon name="edit" size="small" />
            </button>
          </div>
        </div>
      </div>
      
      <!-- Pagination -->
      <div class="flex flex-center flex-gap" v-if="transactions.length > 0">
        <button 
          class="btn" 
          @click="$emit('change-page', currentPage - 1)"
          :disabled="currentPage <= 1"
        >
          Previous
        </button>
        <span class="text-medium">Page {{ currentPage }}</span>
        <button 
          class="btn" 
          @click="$emit('change-page', currentPage + 1)"
          :disabled="transactions.length < pageSize"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'
import AppIcon from './AppIcon.vue'

export default {
  name: 'TransactionsTab',
  components: {
    AppIcon
  },
  props: {
    user: {
      type: Object,
      required: true
    },
    transactionCount: {
      type: Number,
      default: 0
    },
    recentUploads: {
      type: Array,
      default: () => []
    },
    transactions: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    currentPage: {
      type: Number,
      default: 1
    },
    pageSize: {
      type: Number,
      default: 50
    },
    filters: {
      type: Object,
      required: true
    },
    allCategories: {
      type: Array,
      default: () => []
    }
  },
  emits: [
    'file-upload', 
    'refresh-transactions', 
    'change-page', 
    'categorize-transaction', 
    'edit-transaction',
    'update-transaction-count',
    'add-chat-message'
  ],
  setup(props, { emit }) {
    // Local component state
    const fileInput = ref(null)
    const isDragging = ref(false)
    const localUploads = ref([])
    
    // Dynamic API base URL
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

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
      
      if (!props.user) {
        console.log('No user logged in for file upload')
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
        
        // Add to local uploads (will be synced to parent)
        localUploads.value.unshift(upload)
        
        try {
          console.log('Getting ID token for file upload...')
          const token = await props.user.getIdToken()
          console.log('Got token for upload, making request...')
          
          const formData = new FormData()
          formData.append('file', file)
          formData.append('account_name', 'Default Account')
          formData.append('account_type', 'checking')
          
          const response = await axios.post(`${API_BASE}/transactions/import`, formData, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            }
          })
          
          upload.status = 'success'
          upload.rows = response.data.summary.rows_inserted || 0
          
          console.log('Upload successful:', upload.rows, 'rows imported')
          
          // Emit events to parent
          emit('update-transaction-count', props.transactionCount + upload.rows)
          emit('add-chat-message', {
            message: `File uploaded: ${file.name}`,
            response: `Successfully processed ${file.name} with ${upload.rows} transactions imported!`
          })
          
          // Refresh transactions
          emit('refresh-transactions')
          
        } catch (error) {
          upload.status = 'error'
          console.error('Upload failed:', error)
          
          if (error.response?.status === 401) {
            console.error('Upload authentication failed - trying token refresh')
            try {
              const newToken = await props.user.getIdToken(true) // Force refresh
              console.log('Refreshed token, retrying upload...')
              
              const formData = new FormData()
              formData.append('file', file)
              formData.append('account_name', 'Default Account')
              formData.append('account_type', 'checking')
              
              const retryResponse = await axios.post(`${API_BASE}/transactions/import`, formData, {
                headers: {
                  'Authorization': `Bearer ${newToken}`,
                  'Content-Type': 'multipart/form-data'
                }
              })
              
              upload.status = 'success'
              upload.rows = retryResponse.data.summary.rows_inserted || 0
              
              console.log('Upload retry successful:', upload.rows, 'rows imported')
              
              emit('update-transaction-count', props.transactionCount + upload.rows)
              emit('add-chat-message', {
                message: `File uploaded: ${file.name}`,
                response: `Successfully processed ${file.name} with ${upload.rows} transactions imported!`
              })
              
              emit('refresh-transactions')
              
            } catch (retryError) {
              console.error('Upload retry also failed:', retryError)
              emit('add-chat-message', {
                message: `File upload: ${file.name}`,
                response: `Upload failed: ${retryError.response?.data?.detail || retryError.message}`
              })
            }
          } else {
            emit('add-chat-message', {
              message: `File upload: ${file.name}`,
              response: `Upload failed: ${error.response?.data?.detail || error.message}`
            })
          }
        }
      }
    }

    // Filter update function
    const updateFilter = (filterKey, value) => {
      // Emit filter changes to parent
      const newFilters = { ...props.filters, [filterKey]: value }
      emit('update-filters', newFilters)
    }

    // Helper functions
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

    const getCategoryIcon = (categoryId) => {
      // This would need to import getCategoryById from categories.js
      // For now, return a default icon
      return 'circle'
    }

    return {
      // Local state
      fileInput,
      isDragging,
      localUploads,
      
      // Functions
      triggerFileUpload,
      handleFileSelect,
      handleFileDrop,
      updateFilter,
      formatDate,
      formatAmount,
      getCategoryIcon
    }
  }
}
</script>

<style scoped>
/* Transaction Table Styles */
.transactions-table {
  display: grid;
  gap: 0.5rem;
  margin-top: var(--gap-standard);
}

.transaction-row {
  display: grid;
  grid-template-columns: 120px 1fr 120px 150px 80px;
  gap: var(--gap-standard);
  padding: var(--gap-small);
  align-items: center;
  border-radius: var(--radius);
  transition: background 0.2s ease;
}

.transaction-row.header {
  font-weight: 600;
  background: var(--color-background-light);
  border-radius: var(--radius);
}

.transaction-row:not(.header):hover {
  background: var(--color-background-light);
}

.col-date {
  font-size: var(--text-small);
  color: var(--color-text-muted);
}

.col-merchant {
  min-width: 0; /* Allow text truncation */
}

.col-amount {
  text-align: right;
  font-weight: 500;
}

.col-amount.negative {
  color: #dc2626;
}

.col-category {
  min-width: 0;
}

.col-actions {
  text-align: center;
}

.category-tag {
  display: flex;
  align-items: center;
  gap: var(--gap-small);
  padding: 0.25rem 0.5rem;
  background: var(--color-background-light);
  border-radius: var(--radius);
  font-size: var(--text-small);
}

.category-select {
  width: 100%;
  padding: 0.25rem;
  border: 1px solid var(--color-text-muted);
  border-radius: var(--radius);
  background: var(--color-button);
  font-size: var(--text-small);
}

.drop-zone.drop-active {
  border-color: var(--color-text);
  background: var(--color-background);
  transform: scale(1.02);
}

/* Responsive adjustments */
@media (max-width: 48rem) {
  .transaction-row {
    grid-template-columns: 1fr;
    gap: var(--gap-small);
    padding: var(--gap-standard);
    background: var(--color-background);
    border-radius: var(--radius);
    margin-bottom: var(--gap-small);
  }
  
  .transaction-row.header {
    display: none;
  }
  
  .col-date::before { content: "Date: "; font-weight: 600; }
  .col-merchant::before { content: "Merchant: "; font-weight: 600; }
  .col-amount::before { content: "Amount: "; font-weight: 600; }
  .col-category::before { content: "Category: "; font-weight: 600; }
  
  .col-amount {
    text-align: left;
  }
}
</style>