<template>
  <div class="tab-content">
    <!-- Summary Stats -->
    <div class="container" v-if="summary">
      <div class="transactions-stats">
        <div class="stat-card">
          <div class="stat-label">Total Transactions</div>
          <div class="stat-value">{{ summary.total_transactions.toLocaleString() }}</div>
          <div class="stat-detail">{{ formatAmount(summary.total_amount) }} total volume</div>
        </div>
        <div class="stat-card income">
          <div class="stat-label">Income</div>
          <div class="stat-value">{{ formatAmount(summary.income_amount) }}</div>
          <div class="stat-detail">{{ (summary.by_type && summary.by_type.income) || 0 }} transactions</div>
        </div>
        <div class="stat-card expense">
          <div class="stat-label">Expenses</div>
          <div class="stat-value">{{ formatAmount(summary.expense_amount) }}</div>
          <div class="stat-detail">{{ (summary.by_type && summary.by_type.expense) || 0 }} transactions</div>
        </div>
        <div class="stat-card categorized">
          <div class="stat-label">Categorized</div>
          <div class="stat-value">{{ (summary.categorization_rate * 100).toFixed(0) }}%</div>
          <div class="stat-detail">{{ summary.categorized_count }} of {{ summary.total_transactions }}</div>
        </div>
      </div>
    </div>

    <!-- Import Section -->
    <div class="container">
      <div class="import-section">
        <div class="import-header">
          <h3>Import & Manage Transactions</h3>
          <p>Upload CSV files from your bank or financial institution</p>
        </div>
        
        <div 
          class="drop-zone" 
          @click="triggerFileUpload"
          @drop.prevent="handleFileDrop"
          @dragover.prevent
          @dragenter.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          :class="{ 'drag-active': isDragging }"
        >
          <div class="drop-zone-content">
            <div class="upload-text">
              <div class="upload-title">Drag & Drop CSV Files</div>
              <div class="upload-subtitle">Or click to browse and select files</div>
              <div class="upload-formats">Supports: CSV, XLSX • Max: 10MB</div>
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
        
        <div class="import-actions">
          <button class="btn btn-active" @click="triggerFileUpload">
            Choose Files
          </button>
          <button class="btn" @click="loadSummary" :disabled="loading">
            Refresh Data
          </button>
          <button class="btn btn-danger" @click="showResetConfirmation" v-if="summary && summary.total_transactions > 0">
            Reset All Data
          </button>
        </div>
      </div>
    </div>

    <!-- Upload Progress -->
    <div class="container" v-if="localUploads.length > 0">
      <div class="upload-progress">
        <h4>Upload Progress</h4>
        <div class="upload-items">
          <div v-for="upload in localUploads" :key="upload.id" class="upload-item" :class="upload.status">
            <div class="upload-status-icon">
              <span v-if="upload.status === 'success'">✅</span>
              <span v-else-if="upload.status === 'error'">❌</span>
              <span v-else class="loading-spinner">⟳</span>
            </div>
            <div class="upload-details">
              <div class="upload-filename">{{ upload.filename }}</div>
              <div class="upload-info">
                <span class="upload-time">{{ upload.timestamp }}</span>
                <span v-if="upload.status === 'processing'" class="upload-status"> • Processing...</span>
                <span v-else-if="upload.status === 'success'" class="upload-status"> • {{ upload.rows }} rows imported</span>
                <span v-else-if="upload.status === 'error'" class="upload-status"> • Upload failed</span>
              </div>
              <div v-if="upload.summary && upload.status === 'success'" class="upload-summary">
                Types: {{ upload.summary.transaction_types ? Object.keys(upload.summary.transaction_types).join(', ') : '' }}
              </div>
            </div>
            <div class="upload-actions" v-if="upload.batch_id && upload.status === 'success'">
              <button class="btn btn-small btn-link" @click="showBatchDetails(upload.batch_id)">
                Details
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters and Controls -->
    <div class="container">
      <div class="transactions-header">
        <div class="header-info">
          <h3>Transaction History</h3>
          <span class="transaction-count">({{ summary?.total_transactions || 0 }} total)</span>
        </div>
        <div class="header-actions">
          <button class="btn btn-small" @click="toggleFilters" :class="{ 'btn-active': showFilters }">
            Filters {{ hasActiveFilters ? '(Active)' : '' }}
          </button>
          <button class="btn btn-small" @click="refreshTransactions" :disabled="loading">
            Refresh
          </button>
        </div>
      </div>
      
      <!-- Expandable Filters -->
      <div class="filters-panel" v-if="showFilters">
        <div class="filters-grid">
          <div class="filter-group">
            <label>Date Range</label>
            <div class="date-inputs">
              <input 
                type="date" 
                v-model="filters.startDate"
                class="filter-input"
                placeholder="Start Date"
              >
              <input 
                type="date" 
                v-model="filters.endDate"
                class="filter-input"
                placeholder="End Date"
              >
            </div>
          </div>
          
          <div class="filter-group">
            <label>Amount Range (€)</label>
            <div class="amount-inputs">
              <input 
                type="number" 
                v-model.number="filters.minAmount"
                class="filter-input"
                placeholder="Min €"
                step="0.01"
              >
              <input 
                type="number" 
                v-model.number="filters.maxAmount"
                class="filter-input"
                placeholder="Max €"
                step="0.01"
              >
            </div>
          </div>
          
          <div class="filter-group">
            <label>Search</label>
            <input 
              type="text" 
              v-model="filters.merchant"
              class="filter-input"
              placeholder="Search merchant or description..."
            >
          </div>
          
          <div class="filter-group">
            <label>Category</label>
            <select v-model="filters.categoryId" class="filter-input">
              <option value="">All Categories</option>
              <option v-for="category in allCategories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </div>
          
          <div class="filter-group">
            <label>Type</label>
            <select v-model="filters.transactionType" class="filter-input">
              <option value="">All Types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>
        </div>
        
        <div class="filter-actions">
          <button class="btn btn-small" @click="clearFilters">Clear Filters</button>
          <button class="btn btn-small" @click="toggleFilters">Hide Filters</button>
        </div>
      </div>
    </div>

    <!-- Bulk Selection (simplified) -->
    <div class="container" v-if="selectedTransactions.length > 0">
      <div class="bulk-actions">
        <span class="bulk-selection">{{ selectedTransactions.length }} selected</span>
        <button class="btn btn-link" @click="clearSelection">
          Clear Selection
        </button>
      </div>
    </div>

    <!-- Transactions Table -->
    <div class="container">
      <div v-if="loading" class="loading-state">
        <div>Loading transactions...</div>
      </div>
      
      <div v-else-if="transactions.length === 0" class="empty-state">
        <div class="empty-title">No transactions found</div>
        <div class="empty-subtitle">
          {{ hasActiveFilters ? 'Try adjusting your filters' : 'Upload CSV files to get started' }}
        </div>
      </div>
      
      <div v-else class="transactions-table-container">
        <table class="transactions-table">
          <thead>
            <tr>
              <th class="col-select">
                <input 
                  type="checkbox" 
                  :checked="allVisibleTransactionsSelected"
                  @change="toggleAllTransactions"
                >
              </th>
              <th class="col-date clickable" @click="toggleSort('posted_at')">
                Date
                <span v-if="sortBy === 'posted_at'">
                  {{ sortOrder === 'desc' ? '↓' : '↑' }}
                </span>
              </th>
              <th class="col-merchant clickable" @click="toggleSort('merchant')">
                Merchant
                <span v-if="sortBy === 'merchant'">
                  {{ sortOrder === 'desc' ? '↓' : '↑' }}
                </span>
              </th>
              <th class="col-amount clickable" @click="toggleSort('amount')">
                Amount
                <span v-if="sortBy === 'amount'">
                  {{ sortOrder === 'desc' ? '↓' : '↑' }}
                </span>
              </th>
              <th class="col-category">Category</th>
              <th class="col-type">Type</th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="transaction in transactions" 
              :key="transaction.id"
              class="transaction-row"
              :class="{ 
                'uncategorized': !transaction.category_name,
                'selected': selectedTransactions.includes(transaction.id)
              }"
            >
              <td class="col-select">
                <input 
                  type="checkbox" 
                  :checked="selectedTransactions.includes(transaction.id)"
                  @change="toggleTransactionSelection(transaction.id)"
                >
              </td>
              
              <td class="col-date">
                <div class="date-primary">{{ formatDate(transaction.posted_at) }}</div>
                <div class="date-secondary">{{ transaction.weekday }}</div>
              </td>
              
              <td class="col-merchant">
                <div class="merchant-primary">{{ transaction.merchant || 'Unknown Merchant' }}</div>
                <div class="merchant-secondary" v-if="transaction.memo">
                  {{ truncateText(transaction.memo, 60) }}
                </div>
                <div class="merchant-csv" v-if="transaction.csv_category">
                  CSV: {{ transaction.csv_category }}
                  <span v-if="transaction.csv_subcategory"> → {{ transaction.csv_subcategory }}</span>
                </div>
              </td>
              
              <td class="col-amount" :class="getAmountClass(transaction)">
                <div class="amount-primary">{{ formatAmount(transaction.amount) }}</div>
                <div class="amount-secondary" v-if="transaction.owner">{{ transaction.owner }}</div>
              </td>
              
              <td class="col-category">
                <div v-if="transaction.category_name" class="category-assigned">
                  <span class="category-name">{{ transaction.category_name }}</span>
                </div>
                <div v-else class="category-selector">
                  <select 
                    @change="categorizeTransaction(transaction.id, $event.target.value)"
                    class="category-select"
                    :disabled="categorizingTransactions.includes(transaction.id)"
                  >
                    <option value="">Select category...</option>
                    <optgroup 
                      v-for="group in groupedCategories" 
                      :key="group.name" 
                      :label="group.name"
                    >
                      <option 
                        v-for="category in group.categories" 
                        :key="category.id" 
                        :value="category.id"
                      >
                        {{ category.name }}
                      </option>
                    </optgroup>
                  </select>
                </div>
              </td>
              
              <td class="col-type">
                <span class="type-badge" :class="transaction.transaction_type">
                  {{ formatTransactionType(transaction.transaction_type) }}
                </span>
              </td>
              
              <td class="col-actions">
                <div class="action-buttons">
                  <button 
                    class="btn btn-small btn-link" 
                    @click="editTransaction(transaction)"
                    title="Edit transaction"
                  >
                    Edit
                  </button>
                  <button 
                    class="btn btn-small btn-link" 
                    @click="viewTransactionDetails(transaction)"
                    title="View details"
                  >
                    Details
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <div class="pagination-section" v-if="transactions.length > 0">
        <div class="pagination-info">
          Showing {{ ((currentPage - 1) * pageSize) + 1 }} to 
          {{ Math.min(currentPage * pageSize, summary?.total_transactions || 0) }} 
          of {{ summary?.total_transactions || 0 }} transactions
        </div>
        
        <div class="pagination-controls">
          <select v-model.number="pageSize" @change="changePageSize" class="page-size-select">
            <option :value="25">25 per page</option>
            <option :value="50">50 per page</option>
            <option :value="100">100 per page</option>
            <option :value="200">200 per page</option>
          </select>
          
          <button 
            class="btn btn-small" 
            @click="changePage(currentPage - 1)"
            :disabled="currentPage <= 1"
          >
            Previous
          </button>
          
          <span class="page-indicator">Page {{ currentPage }}</span>
          
          <button 
            class="btn btn-small" 
            @click="changePage(currentPage + 1)"
            :disabled="transactions.length < pageSize"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Transaction Detail Modal -->
    <div v-if="selectedTransactionDetail" class="modal-overlay" @click="closeTransactionDetail">
      <div class="modal-content transaction-detail-modal" @click.stop>
        <div class="modal-header">
          <h3>Transaction Details</h3>
          <button class="btn btn-link close-btn" @click="closeTransactionDetail">×</button>
        </div>
        
        <div class="modal-body">
          <div class="detail-grid">
            <div class="detail-item">
              <label>Date</label>
              <span>{{ formatDate(selectedTransactionDetail.posted_at) }}</span>
            </div>
            <div class="detail-item">
              <label>Amount</label>
              <span :class="getAmountClass(selectedTransactionDetail)">
                {{ formatAmount(selectedTransactionDetail.amount) }}
              </span>
            </div>
            <div class="detail-item">
              <label>Merchant</label>
              <span>{{ selectedTransactionDetail.merchant || 'Unknown' }}</span>
            </div>
            <div class="detail-item">
              <label>Category</label>
              <span>{{ selectedTransactionDetail.category_name || 'Uncategorized' }}</span>
            </div>
            <div class="detail-item">
              <label>Type</label>
              <span class="type-badge" :class="selectedTransactionDetail.transaction_type">
                {{ formatTransactionType(selectedTransactionDetail.transaction_type) }}
              </span>
            </div>
            <div class="detail-item" v-if="selectedTransactionDetail.owner">
              <label>Owner</label>
              <span>{{ selectedTransactionDetail.owner }}</span>
            </div>
            <div class="detail-item full-width" v-if="selectedTransactionDetail.memo">
              <label>Memo</label>
              <span>{{ selectedTransactionDetail.memo }}</span>
            </div>
            <div class="detail-item full-width" v-if="selectedTransactionDetail.notes">
              <label>Notes</label>
              <span>{{ selectedTransactionDetail.notes }}</span>
            </div>
          </div>
          
          <!-- CSV Data Section -->
          <div v-if="hasCSVData(selectedTransactionDetail)" class="csv-section">
            <h4>Original CSV Data</h4>
            <div class="detail-grid">
              <div class="detail-item" v-if="selectedTransactionDetail.main_category">
                <label>Main Category</label>
                <span>{{ selectedTransactionDetail.main_category }}</span>
              </div>
              <div class="detail-item" v-if="selectedTransactionDetail.csv_category">
                <label>CSV Category</label>
                <span>{{ selectedTransactionDetail.csv_category }}</span>
              </div>
              <div class="detail-item" v-if="selectedTransactionDetail.csv_subcategory">
                <label>CSV Subcategory</label>
                <span>{{ selectedTransactionDetail.csv_subcategory }}</span>
              </div>
              <div class="detail-item" v-if="selectedTransactionDetail.owner">
                <label>Owner</label>
                <span>{{ selectedTransactionDetail.owner }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="btn" @click="editTransaction(selectedTransactionDetail)">
            Edit Transaction
          </button>
          <button class="btn btn-link" @click="closeTransactionDetail">Close</button>
        </div>
      </div>
    </div>

    <!-- Reset Confirmation Modal -->
    <div v-if="showResetModal" class="modal-overlay" @click="closeResetModal">
      <div class="modal-content reset-modal" @click.stop>
        <div class="modal-header">
          <h3>Reset All Transaction Data</h3>
        </div>
        
        <div class="modal-body">
          <div class="reset-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>This action cannot be undone!</strong></p>
              <p>This will permanently delete:</p>
              <ul>
                <li>All {{ summary?.total_transactions || 0 }} transactions</li>
                <li>All import batches and history</li>
                <li>All categorization data</li>
              </ul>
              <p>Are you sure you want to continue?</p>
            </div>
          </div>
          
          <div class="confirmation-input">
            <label>Type "RESET" to confirm:</label>
            <input 
              type="text" 
              v-model="resetConfirmationText"
              class="reset-input"
              placeholder="RESET"
            >
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-danger" 
            @click="confirmReset"
            :disabled="resetConfirmationText !== 'RESET' || resetting"
          >
            {{ resetting ? 'Resetting...' : 'Reset All Data' }}
          </button>
          <button class="btn btn-link" @click="closeResetModal" :disabled="resetting">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'


export default {
  name: 'TransactionsTab',
  props: {
    user: {
      type: Object,
      required: true
    },
    allCategories: {
      type: Array,
      default: () => []
    }
  },
  emits: [
    'add-chat-message'
  ],
  setup(props, { emit }) {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

    // File handling refs
    const fileInput = ref(null)
    const isDragging = ref(false)
    const localUploads = ref([])
    
    // Data state refs
    const loading = ref(false)
    const summary = ref(null)
    const transactions = ref([])
    
    // Pagination and sorting refs
    const currentPage = ref(1)
    const pageSize = ref(50)
    const sortBy = ref('posted_at')
    const sortOrder = ref('desc')
    
    // Filter state refs
    const showFilters = ref(false)
    const filters = ref({
      startDate: '',
      endDate: '',
      minAmount: null,
      maxAmount: null,
      merchant: '',
      categoryId: '',
      transactionType: ''
    })
    
    // Selection and bulk action refs
    const selectedTransactions = ref([])
    const bulkCategoryId = ref('')
    const categorizingTransactions = ref([])
    
    // Modal state refs
    const selectedTransactionDetail = ref(null)
    const showResetModal = ref(false)
    const resetConfirmationText = ref('')
    const resetting = ref(false)

    // Computed properties
    const hasActiveFilters = computed(() => {
      return Object.values(filters.value).some(value => value !== '' && value !== null)
    })
    
    const groupedCategories = computed(() => {
      const groups = {}
      
      for (const category of props.allCategories) {
        const groupName = category.parent_name || category.category_type || 'Other'
        
        if (!groups[groupName]) {
          groups[groupName] = {
            name: groupName,
            categories: []
          }
        }
        
        groups[groupName].categories.push(category)
      }
      
      return Object.values(groups)
    })
    
    const allVisibleTransactionsSelected = computed(() => {
      return transactions.value.length > 0 && 
             transactions.value.every(t => selectedTransactions.value.includes(t.id))
    })

    // Watchers
    watch(filters, () => {
      currentPage.value = 1
      loadTransactions()
    }, { deep: true })
    
    watch(() => [currentPage.value, pageSize.value, sortBy.value, sortOrder.value], () => {
      loadTransactions()
    })

    // Clean up old uploads periodically
    watch(localUploads, () => {
      setTimeout(() => {
        localUploads.value = localUploads.value.filter(upload => 
          Date.now() - upload.id < 30000 || upload.status === 'processing'
        )
      }, 30000)
    }, { deep: true })

    // File handling methods
    const triggerFileUpload = () => {
      fileInput.value?.click()
    }

    const handleFileSelect = (event) => {
      const files = event.target.files
      processFiles(files)
      event.target.value = ''
    }

    const handleFileDrop = (event) => {
      isDragging.value = false
      const files = event.dataTransfer.files
      processFiles(files)
    }

    const processFiles = async (files) => {
      if (!files || files.length === 0) return
      
      if (!props.user) {
        emit('add-chat-message', {
          response: 'Please sign in to upload files.'
        })
        return
      }

      for (const file of Array.from(files)) {
        console.log('Processing file:', file.name)
        
        if (!file.name.toLowerCase().endsWith('.csv') && !file.name.toLowerCase().endsWith('.xlsx')) {
          emit('add-chat-message', {
            message: `File upload: ${file.name}`,
            response: 'Please upload only CSV or XLSX files.'
          })
          continue
        }

        if (file.size > 10 * 1024 * 1024) {
          emit('add-chat-message', {
            message: `File upload: ${file.name}`,
            response: 'File too large. Please upload files smaller than 10MB.'
          })
          continue
        }
        
        const upload = {
          id: Date.now() + Math.random(),
          filename: file.name,
          status: 'processing',
          rows: 0,
          timestamp: new Date().toLocaleTimeString(),
          summary: null,
          batch_id: null
        }
        
        localUploads.value.unshift(upload)
        
        emit('add-chat-message', {
          message: `Uploading: ${file.name}`,
          response: `Processing ${file.name}... Please wait.`
        })
        
        try {
          const token = await props.user.getIdToken()
          
          const formData = new FormData()
          formData.append('file', file)
          formData.append('account_name', 'Default Account')
          formData.append('account_type', 'checking')
          
          const response = await axios.post(`${API_BASE}/transactions/import`, formData, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            },
            timeout: 120000
          })
          
          upload.status = 'success'
          upload.rows = response.data.summary.rows_inserted || 0
          upload.summary = response.data.summary
          upload.batch_id = response.data.batch_id
          
          const duplicatesMsg = response.data.summary.rows_duplicated ? 
            ` (${response.data.summary.rows_duplicated} duplicates skipped)` : ''
          
          emit('add-chat-message', {
            message: `File uploaded: ${file.name}`,
            response: `Successfully processed ${file.name} with ${upload.rows} transactions imported!${duplicatesMsg}`
          })
          
          await loadSummary()
          await loadTransactions()
          
        } catch (error) {
          upload.status = 'error'
          console.error('Upload failed:', error)
          
          let errorMessage = 'Upload failed: Unknown error'
          if (error.response?.status === 401) {
            try {
              const newToken = await props.user.getIdToken(true)
              errorMessage = 'Authentication failed. Please try signing out and back in.'
            } catch (retryError) {
              errorMessage = 'Authentication failed. Please try signing out and back in.'
            }
          } else if (error.response?.data?.detail) {
            errorMessage = error.response.data.detail
          } else if (error.code === 'ECONNABORTED') {
            errorMessage = 'Upload timeout. Please try with a smaller file.'
          }
          
          emit('add-chat-message', {
            message: `File upload: ${file.name}`,
            response: `${errorMessage}`
          })
        }
      }
    }

    // Data loading methods
    const loadSummary = async () => {
      if (!props.user) return
      
      try {
        const token = await props.user.getIdToken()
        const response = await axios.get(`${API_BASE}/transactions/summary`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        summary.value = response.data
        console.log('Loaded transaction summary:', response.data)
      } catch (error) {
        console.error('Failed to load summary:', error)
        if (error.response?.status === 401) {
          try {
            const newToken = await props.user.getIdToken(true)
            const retryResponse = await axios.get(`${API_BASE}/transactions/summary`, {
              headers: { 'Authorization': `Bearer ${newToken}` }
            })
            summary.value = retryResponse.data
          } catch (retryError) {
            console.error('Summary retry failed:', retryError)
          }
        }
      }
    }

    const loadTransactions = async () => {
      if (!props.user) return
      
      loading.value = true
      try {
        const token = await props.user.getIdToken()
        
        const params = new URLSearchParams({
          page: currentPage.value,
          limit: pageSize.value,
          sort_by: sortBy.value,
          sort_order: sortOrder.value,
          ...(filters.value.startDate && { start_date: filters.value.startDate }),
          ...(filters.value.endDate && { end_date: filters.value.endDate }),
          ...(filters.value.merchant && { merchant: filters.value.merchant }),
          ...(filters.value.categoryId && { category_id: filters.value.categoryId }),
          ...(filters.value.minAmount && { min_amount: filters.value.minAmount }),
          ...(filters.value.maxAmount && { max_amount: filters.value.maxAmount }),
          ...(filters.value.transactionType && { transaction_type: filters.value.transactionType })
        })
        
        const response = await axios.get(`${API_BASE}/transactions/list?${params}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        transactions.value = response.data
        console.log('Loaded transactions:', transactions.value.length)
      } catch (error) {
        console.error('Failed to load transactions:', error)
        if (error.response?.status === 401) {
          try {
            const newToken = await props.user.getIdToken(true)
            const params = new URLSearchParams({
              page: currentPage.value,
              limit: pageSize.value,
              sort_by: sortBy.value,
              sort_order: sortOrder.value,
              ...(filters.value.startDate && { start_date: filters.value.startDate }),
              ...(filters.value.endDate && { end_date: filters.value.endDate }),
              ...(filters.value.merchant && { merchant: filters.value.merchant }),
              ...(filters.value.categoryId && { category_id: filters.value.categoryId }),
              ...(filters.value.minAmount && { min_amount: filters.value.minAmount }),
              ...(filters.value.maxAmount && { max_amount: filters.value.maxAmount }),
              ...(filters.value.transactionType && { transaction_type: filters.value.transactionType })
            })
            
            const retryResponse = await axios.get(`${API_BASE}/transactions/list?${params}`, {
              headers: { 'Authorization': `Bearer ${newToken}` }
            })
            
            transactions.value = retryResponse.data
            console.log('Transaction retry successful:', retryResponse.data.length)
          } catch (retryError) {
            console.error('Transaction retry failed:', retryError)
          }
        }
      } finally {
        loading.value = false
      }
    }

    const refreshTransactions = async () => {
      await loadSummary()
      await loadTransactions()
    }

    // Transaction management methods
    const categorizeTransaction = async (transactionId, categoryId) => {
      if (!categoryId || categorizingTransactions.value.includes(transactionId)) return
      
      categorizingTransactions.value.push(transactionId)
      
      try {
        const token = await props.user.getIdToken()
        
        await axios.post(`${API_BASE}/transactions/categorize/${transactionId}`, {
          category_id: categoryId,
          confidence: 1.0
        }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        const category = props.allCategories.find(c => c.id === categoryId)
        emit('add-chat-message', {
          message: 'Transaction categorized',
          response: `Transaction successfully categorized as ${category?.name || 'selected category'}!`
        })
        
        await loadTransactions()
        await loadSummary()
        
      } catch (error) {
        console.error('Failed to categorize transaction:', error)
        if (error.response?.status === 401) {
          try {
            const newToken = await props.user.getIdToken(true)
            await axios.post(`${API_BASE}/transactions/categorize/${transactionId}`, {
              category_id: categoryId,
              confidence: 1.0
            }, {
              headers: { 'Authorization': `Bearer ${newToken}` }
            })
            
            const category = props.allCategories.find(c => c.id === categoryId)
            emit('add-chat-message', {
              message: 'Transaction categorized',
              response: `Transaction successfully categorized as ${category?.name || 'selected category'}!`
            })
            
            await loadTransactions()
            await loadSummary()
          } catch (retryError) {
            console.error('Categorization retry failed:', retryError)
            emit('add-chat-message', {
              response: 'Failed to categorize transaction. Please try again.'
            })
          }
        } else {
          emit('add-chat-message', {
            response: 'Failed to categorize transaction. Please try again.'
          })
        }
      } finally {
        categorizingTransactions.value = categorizingTransactions.value.filter(id => id !== transactionId)
      }
    }

    const bulkCategorize = async () => {
      if (!bulkCategoryId.value || selectedTransactions.value.length === 0) return
      
      try {
        const token = await props.user.getIdToken()
        
        await axios.post(`${API_BASE}/transactions/bulk-categorize`, {
          transaction_ids: selectedTransactions.value,
          category_id: bulkCategoryId.value,
          confidence: 1.0
        }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        const category = props.allCategories.find(c => c.id === bulkCategoryId.value)
        emit('add-chat-message', {
          message: `Bulk categorization: ${selectedTransactions.value.length} transactions`,
          response: `Successfully categorized ${selectedTransactions.value.length} transactions as ${category?.name || 'selected category'}!`
        })
        
        selectedTransactions.value = []
        bulkCategoryId.value = ''
        await loadTransactions()
        await loadSummary()
        
      } catch (error) {
        console.error('Bulk categorization failed:', error)
        if (error.response?.status === 401) {
          try {
            const newToken = await props.user.getIdToken(true)
            await axios.post(`${API_BASE}/transactions/bulk-categorize`, {
              transaction_ids: selectedTransactions.value,
              category_id: bulkCategoryId.value,
              confidence: 1.0
            }, {
              headers: { 'Authorization': `Bearer ${newToken}` }
            })
            
            const category = props.allCategories.find(c => c.id === bulkCategoryId.value)
            emit('add-chat-message', {
              message: `Bulk categorization: ${selectedTransactions.value.length} transactions`,
              response: `Successfully categorized ${selectedTransactions.value.length} transactions as ${category?.name || 'selected category'}!`
            })
            
            selectedTransactions.value = []
            bulkCategoryId.value = ''
            await loadTransactions()
            await loadSummary()
          } catch (retryError) {
            console.error('Bulk categorization retry failed:', retryError)
            emit('add-chat-message', {
              response: 'Bulk categorization failed. Please try again.'
            })
          }
        } else {
          emit('add-chat-message', {
            response: 'Bulk categorization failed. Please try again.'
          })
        }
      }
    }

    // Filter and UI methods
    const toggleFilters = () => {
      showFilters.value = !showFilters.value
    }

    const clearFilters = () => {
      filters.value = {
        startDate: '',
        endDate: '',
        minAmount: null,
        maxAmount: null,
        merchant: '',
        categoryId: '',
        transactionType: ''
      }
    }

    const toggleSort = (column) => {
      if (sortBy.value === column) {
        sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
      } else {
        sortBy.value = column
        sortOrder.value = 'desc'
      }
    }

    // Selection methods
    const toggleTransactionSelection = (transactionId) => {
      const index = selectedTransactions.value.indexOf(transactionId)
      if (index > -1) {
        selectedTransactions.value.splice(index, 1)
      } else {
        selectedTransactions.value.push(transactionId)
      }
    }

    const toggleAllTransactions = () => {
      if (allVisibleTransactionsSelected.value) {
        selectedTransactions.value = []
      } else {
        selectedTransactions.value = transactions.value.map(t => t.id)
      }
    }

    const clearSelection = () => {
      selectedTransactions.value = []
      bulkCategoryId.value = ''
    }

    // Pagination methods
    const changePage = (newPage) => {
      if (newPage >= 1) {
        currentPage.value = newPage
      }
    }

    const changePageSize = () => {
      currentPage.value = 1
      loadTransactions()
    }

    // Modal methods
    const viewTransactionDetails = (transaction) => {
      selectedTransactionDetail.value = transaction
    }

    const closeTransactionDetail = () => {
      selectedTransactionDetail.value = null
    }

    const editTransaction = (transaction) => {
      console.log('Edit transaction:', transaction)
    }

    const showBatchDetails = (batchId) => {
      console.log('Show batch details:', batchId)
    }

    // Reset functionality
    const showResetConfirmation = () => {
      showResetModal.value = true
      resetConfirmationText.value = ''
    }

    const closeResetModal = () => {
      showResetModal.value = false
      resetConfirmationText.value = ''
    }

    const confirmReset = async () => {
      if (resetConfirmationText.value !== 'RESET' || resetting.value) return
      
      resetting.value = true
      
      try {
        const token = await props.user.getIdToken()
        
        // Call backend endpoint to reset all data
        await axios.delete(`${API_BASE}/transactions/reset-all`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        // Clear local state
        transactions.value = []
        summary.value = null
        selectedTransactions.value = []
        localUploads.value = []
        
        emit('add-chat-message', {
          message: 'Reset all transaction data',
          response: 'All transaction data has been successfully reset. You can now import fresh data.'
        })
        
        closeResetModal()
        
      } catch (error) {
        console.error('Reset failed:', error)
        
        let errorMessage = 'Reset failed. Please try again.'
        if (error.response?.status === 401) {
          try {
            const newToken = await props.user.getIdToken(true)
            await axios.delete(`${API_BASE}/transactions/reset-all`, {
              headers: { 'Authorization': `Bearer ${newToken}` }
            })
            
            transactions.value = []
            summary.value = null
            selectedTransactions.value = []
            localUploads.value = []
            
            emit('add-chat-message', {
              message: 'Reset all transaction data',
              response: 'All transaction data has been successfully reset. You can now import fresh data.'
            })
            
            closeResetModal()
          } catch (retryError) {
            console.error('Reset retry failed:', retryError)
            emit('add-chat-message', {
              response: 'Reset failed. Please try signing out and back in.'
            })
          }
        } else if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail
        }
        
        if (resetting.value) {
          emit('add-chat-message', {
            response: errorMessage
          })
        }
      } finally {
        resetting.value = false
      }
    }

    // Utility methods
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-EU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })
    }

    const formatAmount = (amount) => {
      const num = parseFloat(amount)
      return new Intl.NumberFormat('en-EU', {
        style: 'currency',
        currency: 'EUR'
      }).format(Math.abs(num))
    }

    const formatTransactionType = (type) => {
      if (!type) return 'Unknown'
      return type.charAt(0).toUpperCase() + type.slice(1)
    }

    const getAmountClass = (transaction) => {
      const amount = parseFloat(transaction.amount)
      if (transaction.transaction_type === 'income' || amount > 0) {
        return 'amount-positive'
      } else if (transaction.transaction_type === 'expense' || amount < 0) {
        return 'amount-negative'
      }
      return 'amount-neutral'
    }

    const truncateText = (text, maxLength) => {
      if (!text || text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    const hasCSVData = (transaction) => {
      return transaction.main_category || 
             transaction.csv_category || 
             transaction.csv_subcategory || 
             transaction.owner
    }

    // Initialize data on component mount
    onMounted(async () => {
      if (props.user) {
        await loadSummary()
        await loadTransactions()
      }
    })

    // Return all reactive references and methods for template use
    return {
      // File handling
      fileInput,
      isDragging,
      localUploads,
      
      // Data state
      loading,
      summary,
      transactions,
      
      // Pagination and sorting
      currentPage,
      pageSize,
      sortBy,
      sortOrder,
      
      // Filters
      showFilters,
      filters,
      hasActiveFilters,
      
      // Selection and bulk actions
      selectedTransactions,
      bulkCategoryId,
      categorizingTransactions,
      allVisibleTransactionsSelected,
      
      // Modals
      selectedTransactionDetail,
      showResetModal,
      resetConfirmationText,
      resetting,
      
      // Computed
      groupedCategories,
      
      // File handling methods
      triggerFileUpload,
      handleFileSelect,
      handleFileDrop,
      
      // Data loading methods
      loadSummary,
      loadTransactions,
      refreshTransactions,
      
      // Transaction methods
      categorizeTransaction,
      bulkCategorize,
      
      // Filter and UI methods
      toggleFilters,
      clearFilters,
      toggleSort,
      
      // Selection methods
      toggleTransactionSelection,
      toggleAllTransactions,
      clearSelection,
      
      // Pagination methods
      changePage,
      changePageSize,
      
      // Modal methods
      viewTransactionDetails,
      closeTransactionDetail,
      editTransaction,
      showBatchDetails,
      
      // Reset methods
      showResetConfirmation,
      closeResetModal,
      confirmReset,
      
      // Utility methods
      formatDate,
      formatAmount,
      formatTransactionType,
      getAmountClass,
      truncateText,
      hasCSVData
    }
  }
}
</script>
