<template>
  <div class="tab-content">
    <!-- Quick Stats Overview -->
    <div class="container" v-if="summary">
      <div class="grid grid-auto">
        <div class="card text-center">
          <div class="text-small text-muted">Total Transactions</div>
          <div class="text-large">{{ summary.total_transactions.toLocaleString() }}</div>
          <div class="text-small text-light">{{ formatAmount(summary.total_amount) }} total volume</div>
        </div>
        <div class="card text-center">
          <div class="text-small text-muted">Income</div>
          <div class="text-large text-green">{{ formatAmount(summary.income_amount) }}</div>
          <div class="text-small text-light">{{ (summary.by_type && summary.by_type.income) || 0 }} transactions</div>
        </div>
        <div class="card text-center">
          <div class="text-small text-muted">Expenses</div>
          <div class="text-large text-red">{{ formatAmount(summary.expense_amount) }}</div>
          <div class="text-small text-light">{{ (summary.by_type && summary.by_type.expense) || 0 }} transactions</div>
        </div>
        <div class="card text-center">
          <div class="text-small text-muted">Categorized</div>
          <div class="text-large">{{ (summary.categorization_rate * 100).toFixed(0) }}%</div>
          <div class="text-small text-light">{{ summary.categorized_count }} of {{ summary.total_transactions }}</div>
        </div>
      </div>
    </div>

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
          <div class="upload-icon">📁</div>
          <div class="text-large">Drag & Drop CSV Files</div>
          <div class="text-medium text-light">Or click to browse and select files</div>
          <div class="text-small text-muted">Supports: CSV, XLSX • Max: 10MB</div>
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
        <button class="btn" @click="loadSummary" :disabled="loading">
          Refresh Data
        </button>
      </div>
    </div>

    <!-- Upload Status -->
    <div class="container" v-if="localUploads.length > 0">
      <div class="text-medium section-header">Current Uploads</div>
      <div class="flex-column flex-gap-sm">
        <div v-for="upload in localUploads" :key="upload.id" class="card flex flex-gap">
          <div class="status-icon">
            {{ upload.status === 'success' ? '✅' : upload.status === 'error' ? '❌' : '⏳' }}
          </div>
          <div class="flex-1">
            <div class="text-medium">{{ upload.filename }}</div>
            <div class="text-small text-light">
              {{ upload.timestamp }}
              <span v-if="upload.status === 'processing'"> • Processing...</span>
              <span v-else-if="upload.status === 'success'"> • {{ upload.rows }} rows imported</span>
              <span v-else-if="upload.status === 'error'"> • Upload failed</span>
            </div>
            <div v-if="upload.summary && upload.status === 'success'" class="text-small text-muted">
              {{ upload.summary.transaction_types ? Object.keys(upload.summary.transaction_types).join(', ') : '' }}
            </div>
          </div>
          <button 
            v-if="upload.batch_id && upload.status === 'success'"
            class="btn btn-small btn-link"
            @click="showBatchDetails(upload.batch_id)"
            title="View batch details"
          >
            Details
          </button>
        </div>
      </div>
    </div>

    <!-- Quick Actions & Filters -->
    <div class="container">
      <div class="flex flex-between flex-wrap">
        <div class="text-medium section-header">
          Transaction History 
          <span class="text-small text-muted">({{ summary?.total_transactions || 0 }} total)</span>
        </div>
        <div class="flex flex-gap">
          <button 
            class="btn" 
            @click="loadTransactionsNeedingReview"
            :class="{ 'btn-active': showingReviewOnly }"
          >
            Need Review ({{ reviewCount || 0 }})
          </button>
          <button class="btn" @click="refreshTransactions" :disabled="loading">
            Refresh
          </button>
        </div>
      </div>
      
      <!-- Enhanced Filters -->
      <div class="filters-section">
        <div class="flex flex-gap flex-wrap">
          <!-- Date Range -->
          <div class="filter-group">
            <label class="text-small text-muted">Date Range</label>
            <div class="flex flex-gap-sm">
              <input 
                type="date" 
                :value="filters.startDate"
                @input="updateFilter('startDate', $event.target.value)"
                class="filter-input"
                placeholder="Start Date"
              >
              <input 
                type="date" 
                :value="filters.endDate"
                @input="updateFilter('endDate', $event.target.value)"
                class="filter-input"
                placeholder="End Date"
              >
            </div>
          </div>
          
          <!-- Amount Range -->
          <div class="filter-group">
            <label class="text-small text-muted">Amount Range</label>
            <div class="flex flex-gap-sm">
              <input 
                type="number" 
                :value="filters.minAmount"
                @input="updateFilter('minAmount', $event.target.value)"
                class="filter-input"
                placeholder="Min $"
                step="0.01"
              >
              <input 
                type="number" 
                :value="filters.maxAmount"
                @input="updateFilter('maxAmount', $event.target.value)"
                class="filter-input"
                placeholder="Max $"
                step="0.01"
              >
            </div>
          </div>
          
          <!-- Search & Category -->
          <div class="filter-group">
            <label class="text-small text-muted">Search & Category</label>
            <div class="flex flex-gap-sm">
              <input 
                type="text" 
                :value="filters.merchant"
                @input="updateFilter('merchant', $event.target.value)"
                class="filter-input"
                placeholder="Search merchant..."
              >
              <select 
                :value="filters.categoryId"
                @change="updateFilter('categoryId', $event.target.value)"
                class="filter-input"
              >
                <option value="">All Categories</option>
                <option v-for="category in allCategories" :key="category.id" :value="category.id">
                  {{ category.name }}
                </option>
              </select>
            </div>
          </div>
          
          <!-- Transaction Type -->
          <div class="filter-group">
            <label class="text-small text-muted">Type</label>
            <select 
              :value="filters.transactionType"
              @change="updateFilter('transactionType', $event.target.value)"
              class="filter-input"
            >
              <option value="">All Types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>
        </div>
        
        <!-- Filter Actions -->
        <div class="flex flex-gap-sm">
          <button class="btn btn-small" @click="clearFilters">
            Clear Filters
          </button>
          <button class="btn btn-small" @click="saveFiltersAsPreset" v-if="hasActiveFilters">
            Save Preset
          </button>
        </div>
      </div>
    </div>

    <!-- Bulk Actions Bar -->
    <div class="container" v-if="selectedTransactions.length > 0">
      <div class="bulk-actions-bar">
        <div class="flex flex-gap">
          <span class="text-medium">{{ selectedTransactions.length }} selected</span>
          <select v-model="bulkCategoryId" class="filter-input">
            <option value="">Choose category...</option>
            <option v-for="category in allCategories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>
          <button 
            class="btn btn-active" 
            @click="bulkCategorize" 
            :disabled="!bulkCategoryId"
          >
            Categorize Selected
          </button>
          <button class="btn btn-link" @click="clearSelection">
            Clear Selection
          </button>
        </div>
      </div>
    </div>

    <!-- Enhanced Transactions Table -->
    <div class="container">
      <div v-if="loading" class="text-center loading-state">
        <div class="loading-spinner">⟳</div>
        <div class="text-medium">Loading transactions...</div>
      </div>
      
      <div v-else-if="transactions.length === 0" class="text-center empty-state">
        <div class="empty-icon">📄</div>
        <div class="text-medium">No transactions found</div>
        <div class="text-small text-light">
          {{ hasActiveFilters ? 'Try adjusting your filters' : 'Upload CSV files to get started' }}
        </div>
      </div>
      
      <div v-else class="transactions-table">
        <!-- Table Header -->
        <div class="transaction-row header">
          <div class="col-select">
            <input 
              type="checkbox" 
              :checked="allVisibleTransactionsSelected"
              @change="toggleAllTransactions"
              class="checkbox-input"
            >
          </div>
          <div class="col-date" @click="toggleSort('posted_at')">
            Date
            <span v-if="sortBy === 'posted_at'">
              {{ sortOrder === 'desc' ? '↓' : '↑' }}
            </span>
          </div>
          <div class="col-merchant" @click="toggleSort('merchant')">
            Merchant
            <span v-if="sortBy === 'merchant'">
              {{ sortOrder === 'desc' ? '↓' : '↑' }}
            </span>
          </div>
          <div class="col-amount" @click="toggleSort('amount')">
            Amount
            <span v-if="sortBy === 'amount'">
              {{ sortOrder === 'desc' ? '↓' : '↑' }}
            </span>
          </div>
          <div class="col-category">Category</div>
          <div class="col-type">Type</div>
          <div class="col-confidence">Confidence</div>
          <div class="col-actions">Actions</div>
        </div>
        
        <!-- Transaction Rows -->
        <div 
          v-for="transaction in transactions" 
          :key="transaction.id"
          class="transaction-row"
          :class="{ 
            'review-needed': transaction.review_needed,
            'selected': selectedTransactions.includes(transaction.id),
            'low-confidence': transaction.confidence_score && transaction.confidence_score < 0.7
          }"
        >
          <div class="col-select">
            <input 
              type="checkbox" 
              :checked="selectedTransactions.includes(transaction.id)"
              @change="toggleTransactionSelection(transaction.id)"
              class="checkbox-input"
            >
          </div>
          
          <div class="col-date">
            <div class="text-medium">{{ formatDate(transaction.posted_at) }}</div>
            <div class="text-small text-muted">{{ transaction.weekday }}</div>
          </div>
          
          <div class="col-merchant">
            <div class="text-medium">{{ transaction.merchant || 'Unknown Merchant' }}</div>
            <div class="text-small text-light" v-if="transaction.memo">{{ truncateText(transaction.memo, 50) }}</div>
            <div class="text-small text-muted" v-if="transaction.csv_category">
              CSV: {{ transaction.csv_category }}
              <span v-if="transaction.csv_subcategory"> → {{ transaction.csv_subcategory }}</span>
            </div>
          </div>
          
          <div class="col-amount" :class="getAmountClass(transaction)">
            <div class="text-medium">{{ formatAmount(transaction.amount) }}</div>
            <div class="text-small text-muted" v-if="transaction.owner">{{ transaction.owner }}</div>
          </div>
          
          <div class="col-category">
            <div v-if="transaction.category_name" class="category-tag assigned">
              <span>{{ transaction.category_name }}</span>
              <button 
                class="btn btn-link btn-small change-category-btn"
                @click="showCategorySelector(transaction)"
                title="Change category"
              >
                Change
              </button>
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
          </div>
          
          <div class="col-type">
            <span class="type-badge" :class="transaction.transaction_type">
              {{ formatTransactionType(transaction.transaction_type) }}
            </span>
          </div>
          
          <div class="col-confidence">
            <div v-if="transaction.confidence_score" class="confidence-indicator">
              <div class="confidence-bar">
                <div 
                  class="confidence-fill" 
                  :style="{ width: (transaction.confidence_score * 100) + '%' }"
                  :class="getConfidenceClass(transaction.confidence_score)"
                ></div>
              </div>
              <span class="text-small">{{ (transaction.confidence_score * 100).toFixed(0) }}%</span>
            </div>
            <span v-else class="text-small text-muted">—</span>
          </div>
          
          <div class="col-actions">
            <div class="flex flex-gap-sm">
              <button 
                class="btn btn-small" 
                @click="editTransaction(transaction)"
                title="Edit transaction"
              >
                Edit
              </button>
              <button 
                class="btn btn-small" 
                @click="viewTransactionDetails(transaction)"
                title="View details"
              >
                Details
              </button>
              <button 
                v-if="transaction.review_needed"
                class="btn btn-small btn-active" 
                @click="markAsReviewed(transaction.id)"
                title="Mark as reviewed"
              >
                Reviewed
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Enhanced Pagination -->
      <div class="pagination-section" v-if="transactions.length > 0">
        <div class="flex flex-between flex-center">
          <div class="text-small text-muted">
            Showing {{ ((currentPage - 1) * pageSize) + 1 }} to 
            {{ Math.min(currentPage * pageSize, summary?.total_transactions || 0) }} 
            of {{ summary?.total_transactions || 0 }} transactions
          </div>
          
          <div class="flex flex-gap">
            <select v-model="pageSize" @change="changePageSize" class="filter-input">
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
            
            <span class="pagination-info">Page {{ currentPage }}</span>
            
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
    </div>

    <!-- Transaction Detail Modal -->
    <div v-if="selectedTransactionDetail" class="modal-overlay" @click="closeTransactionDetail">
      <div class="modal-content transaction-detail-modal" @click.stop>
        <div class="modal-header">
          <h3>Transaction Details</h3>
          <button class="btn btn-link" @click="closeTransactionDetail">
            Close
          </button>
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
            <div class="detail-item">
              <label>Confidence</label>
              <span v-if="selectedTransactionDetail.confidence_score">
                {{ (selectedTransactionDetail.confidence_score * 100).toFixed(0) }}%
              </span>
              <span v-else>—</span>
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
    // Local component state
    const fileInput = ref(null)
    const isDragging = ref(false)
    const localUploads = ref([])
    const loading = ref(false)
    const summary = ref(null)
    const transactions = ref([])
    const reviewCount = ref(0)
    const showingReviewOnly = ref(false)
    
    // Pagination & Sorting
    const currentPage = ref(1)
    const pageSize = ref(50)
    const sortBy = ref('posted_at')
    const sortOrder = ref('desc')
    
    // Filters
    const filters = ref({
      startDate: '',
      endDate: '',
      minAmount: null,
      maxAmount: null,
      merchant: '',
      categoryId: '',
      transactionType: ''
    })
    
    // Selection & Bulk Actions
    const selectedTransactions = ref([])
    const bulkCategoryId = ref('')
    const categorizingTransactions = ref([])
    
    // Modal states
    const selectedTransactionDetail = ref(null)
    
    // Dynamic API base URL
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

    // Computed properties
    const hasActiveFilters = computed(() => {
      return Object.values(filters.value).some(value => value !== '' && value !== null)
    })
    
    const groupedCategories = computed(() => {
      // Group categories by their parent or type for better organization
      const groups = {}
      
      for (const category of props.allCategories) {
        // You can customize grouping logic based on your category structure
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

    // Watch for filter changes
    watch(filters, () => {
      currentPage.value = 1
      loadTransactions()
    }, { deep: true })
    
    watch(() => [currentPage.value, pageSize.value, sortBy.value, sortOrder.value], () => {
      loadTransactions()
    })

    // File handling functions
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
            timeout: 60000
          })
          
          upload.status = 'success'
          upload.rows = response.data.summary.rows_inserted || 0
          upload.summary = response.data.summary
          upload.batch_id = response.data.batch_id
          
          emit('add-chat-message', {
            message: `File uploaded: ${file.name}`,
            response: `Successfully processed ${file.name} with ${upload.rows} transactions imported! ${response.data.summary.rows_duplicated || 0} duplicates were skipped.`
          })
          
          // Refresh data
          await loadSummary()
          await loadTransactions()
          
        } catch (error) {
          upload.status = 'error'
          console.error('Upload failed:', error)
          
          let errorMessage = 'Upload failed: Unknown error'
          if (error.response?.status === 401) {
            try {
              const newToken = await props.user.getIdToken(true)
              // Retry logic would go here
              errorMessage = 'Authentication failed. Please try signing out and back in.'
            } catch (retryError) {
              errorMessage = 'Authentication failed. Please try signing out and back in.'
            }
          } else if (error.response?.data?.detail) {
            errorMessage = error.response.data.detail
          }
          
          emit('add-chat-message', {
            message: `File upload: ${file.name}`,
            response: `${errorMessage}`
          })
        }
      }
    }

    // Data loading functions
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
          ...(filters.value.transactionType && { transaction_type: filters.value.transactionType }),
          ...(showingReviewOnly.value && { review_needed: true })
        })
        
        const endpoint = showingReviewOnly.value ? 
          `${API_BASE}/transactions/review?${params}` : 
          `${API_BASE}/transactions/list?${params}`
        
        const response = await axios.get(endpoint, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        if (showingReviewOnly.value) {
          transactions.value = response.data.transactions || []
          reviewCount.value = response.data.total_count || 0
        } else {
          transactions.value = response.data
        }
        
        console.log('Loaded transactions:', transactions.value.length)
      } catch (error) {
        console.error('Failed to load transactions:', error)
      } finally {
        loading.value = false
      }
    }

    const loadTransactionsNeedingReview = async () => {
      showingReviewOnly.value = !showingReviewOnly.value
      currentPage.value = 1
      await loadTransactions()
    }

    // Transaction management functions
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
        
        // Find category name for success message
        const category = props.allCategories.find(c => c.id === categoryId)
        emit('add-chat-message', {
          message: 'Transaction categorized',
          response: `Transaction successfully categorized as ${category?.name || 'selected category'}!`
        })
        
        // Refresh transactions to show updated category
        await loadTransactions()
        await loadSummary()
        
      } catch (error) {
        console.error('Failed to categorize transaction:', error)
        emit('add-chat-message', {
          response: 'Failed to categorize transaction. Please try again.'
        })
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
        
        // Clear selection and refresh
        selectedTransactions.value = []
        bulkCategoryId.value = ''
        await loadTransactions()
        await loadSummary()
        
      } catch (error) {
        console.error('Bulk categorization failed:', error)
        emit('add-chat-message', {
          response: 'Bulk categorization failed. Please try again.'
        })
      }
    }

    const markAsReviewed = async (transactionId) => {
      try {
        const token = await props.user.getIdToken()
        
        // Update transaction to mark as reviewed
        await axios.put(`${API_BASE}/transactions/${transactionId}`, {
          // This would need to be implemented in the backend
          review_needed: false
        }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        await loadTransactions()
        
      } catch (error) {
        console.error('Failed to mark as reviewed:', error)
      }
    }

    // Filter and sorting functions
    const updateFilter = (filterKey, value) => {
      filters.value[filterKey] = value
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
      showingReviewOnly.value = false
    }

    const toggleSort = (column) => {
      if (sortBy.value === column) {
        sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
      } else {
        sortBy.value = column
        sortOrder.value = 'desc'
      }
    }

    // Selection functions
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

    // Pagination functions
    const changePage = (newPage) => {
      if (newPage >= 1) {
        currentPage.value = newPage
      }
    }

    const changePageSize = () => {
      currentPage.value = 1
      loadTransactions()
    }

    // Modal functions
    const viewTransactionDetails = (transaction) => {
      selectedTransactionDetail.value = transaction
    }

    const closeTransactionDetail = () => {
      selectedTransactionDetail.value = null
    }

    const editTransaction = (transaction) => {
      console.log('Edit transaction:', transaction)
      // TODO: Implement transaction editing modal
    }

    const showCategorySelector = (transaction) => {
      console.log('Show category selector for:', transaction)
      // TODO: Implement inline category selector
    }

    const showBatchDetails = (batchId) => {
      console.log('Show batch details:', batchId)
      // TODO: Implement batch details modal
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

    const getConfidenceClass = (confidence) => {
      if (confidence >= 0.8) return 'confidence-high'
      if (confidence >= 0.6) return 'confidence-medium'
      return 'confidence-low'
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

    const refreshTransactions = async () => {
      await loadSummary()
      await loadTransactions()
    }

    const saveFiltersAsPreset = () => {
      console.log('Save filters as preset:', filters.value)
      // TODO: Implement filter presets
    }

    // Initialize data on mount
    onMounted(async () => {
      if (props.user) {
        await loadSummary()
        await loadTransactions()
      }
    })

    // Clean up old uploads after 30 seconds
    watch(localUploads, () => {
      setTimeout(() => {
        localUploads.value = localUploads.value.filter(upload => 
          Date.now() - upload.id < 30000 || upload.status === 'processing'
        )
      }, 30000)
    }, { deep: true })

    return {
      // Local state
      fileInput,
      isDragging,
      localUploads,
      loading,
      summary,
      transactions,
      reviewCount,
      showingReviewOnly,
      
      // Pagination & Sorting
      currentPage,
      pageSize,
      sortBy,
      sortOrder,
      
      // Filters
      filters,
      hasActiveFilters,
      
      // Selection & Bulk Actions
      selectedTransactions,
      bulkCategoryId,
      categorizingTransactions,
      allVisibleTransactionsSelected,
      
      // Modal states
      selectedTransactionDetail,
      
      // Computed
      groupedCategories,
      
      // File functions
      triggerFileUpload,
      handleFileSelect,
      handleFileDrop,
      
      // Data functions
      loadSummary,
      loadTransactions,
      loadTransactionsNeedingReview,
      refreshTransactions,
      
      // Transaction functions
      categorizeTransaction,
      bulkCategorize,
      markAsReviewed,
      
      // Filter functions
      updateFilter,
      clearFilters,
      toggleSort,
      saveFiltersAsPreset,
      
      // Selection functions
      toggleTransactionSelection,
      toggleAllTransactions,
      clearSelection,
      
      // Pagination functions
      changePage,
      changePageSize,
      
      // Modal functions
      viewTransactionDetails,
      closeTransactionDetail,
      editTransaction,
      showCategorySelector,
      showBatchDetails,
      
      // Utility functions
      formatDate,
      formatAmount,
      formatTransactionType,
      getAmountClass,
      getConfidenceClass,
      truncateText,
      hasCSVData
    }
  }
}
</script>