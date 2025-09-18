<template>
  <div class="tab-content">
    <!-- Top Cards Section -->
    <div class="grid grid-3">
      <!-- Import Card -->
      <div class="container">
        <div class="import-section">
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
          <div class="import-header">
            <h3>Import Transactions</h3>
          </div>
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
        </div>
      </div>

      <!-- Transaction Count Card -->
      <div class="container stat-card">
          <div class="stat-label">Total Transactions</div>
          <div class="stat-value">{{ summary?.total_transactions?.toLocaleString() || 0 }}</div>
          <div class="stat-detail">
            <span v-if="summary?.categorized_count">
              {{ summary.categorized_count }} categorized
            </span>
          </div>
      </div>

      <!-- Reset Card -->
      <div class="container stat-card">
          <div class="stat-detail">
            <button class="btn btn-danger" @click="showResetModal = true" v-if="summary && summary.total_transactions > 0">
              Reset All Data
            </button>
            <span v-else class="text-muted">No data to reset</span>
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
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Transactions Table with Filters -->
    <div class="container">
      <!-- Table Header with Controls -->
      <div class="transactions-header">
        <div class="header-info">
          <h3>Transaction History</h3>
          <span class="transaction-count">({{ summary?.total_transactions || 0 }} total)</span>
        </div>
        <div class="header-actions">
          <button class="btn btn-small" @click="showFilters = !showFilters" :class="{ 'btn-active': showFilters }">
            Filters {{ hasActiveFilters ? '(Active)' : '' }}
          </button>
          <button class="btn btn-small" @click="refreshTransactions" :disabled="loading">
            Refresh
          </button>
        </div>
      </div>
      
      <!-- Expandable Filters - Reorganized -->
      <div class="filters-panel" v-if="showFilters">
        <div class="filters-row">
          <!-- Date Range Filters -->
          <div class="filter-group">
            <label>From Date</label>
            <input 
              type="date" 
              v-model="filters.startDate"
              class="filter-input"
            >
          </div>
          
          <div class="filter-group">
            <label>To Date</label>
            <input 
              type="date" 
              v-model="filters.endDate"
              class="filter-input"
            >
          </div>
          
          <!-- Amount Range Filters -->
          <div class="filter-group">
            <label>Min Amount (€)</label>
            <input 
              type="number" 
              v-model.number="filters.minAmount"
              class="filter-input"
              placeholder="0.00"
              step="0.01"
            >
          </div>
          
          <div class="filter-group">
            <label>Max Amount (€)</label>
            <input 
              type="number" 
              v-model.number="filters.maxAmount"
              class="filter-input"
              placeholder="1000.00"
              step="0.01"
            >
          </div>
        </div>
        
        <div class="filters-row">
          <!-- Search and Category Filters -->
          <div class="filter-group filter-search">
            <label>Search</label>
            <input 
              type="text" 
              v-model="filters.merchant"
              class="filter-input"
              placeholder="Search merchant, message..."
            >
          </div>
          
          <div class="filter-group">
            <label>Category</label>
            <select v-model="filters.mainCategory" class="filter-input">
              <option value="">All Categories</option>
              <option v-for="category in uniqueMainCategories" :key="category" :value="category">
                {{ category }}
              </option>
            </select>
          </div>
          
          <div class="filter-group">
            <label>Subcategory</label>
            <select v-model="filters.categoryFilter" class="filter-input">
              <option value="">All Subcategories</option>
              <option v-for="category in uniqueCategories" :key="category" :value="category">
                {{ category }}
              </option>
            </select>
          </div>
          
          <div class="filter-group">
            <label>Transaction Type</label>
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
          <button class="btn btn-small" @click="showFilters = false">Hide Filters</button>
        </div>
      </div>

      <!-- Bulk Selection -->
      <div class="bulk-actions" v-if="selectedTransactions.length > 0">
        <span class="bulk-selection">{{ selectedTransactions.length }} selected</span>
        <select v-model="bulkCategoryId" class="bulk-category-select">
          <option value="">Select category for bulk assignment...</option>
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
        <button class="btn btn-small" @click="bulkCategorize" :disabled="!bulkCategoryId">
          Apply Category
        </button>
        <button class="btn btn-link" @click="clearSelection">
          Clear Selection
        </button>
      </div>

      <!-- Loading and Empty States -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">⟳</div>
        <div>Loading transactions...</div>
      </div>
      
      <div v-else-if="transactions.length === 0" class="empty-state">
        <div class="empty-title">No transactions found</div>
        <div class="empty-subtitle">
          {{ hasActiveFilters ? 'Try adjusting your filters' : 'Upload CSV files to get started' }}
        </div>
      </div>
      
      <!-- Transactions Table -->
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
              <th class="col-amount clickable" @click="toggleSort('amount')">
                Amount
                <span v-if="sortBy === 'amount'">
                  {{ sortOrder === 'desc' ? '↓' : '↑' }}
                </span>
              </th>
              <th class="col-merchant clickable" @click="toggleSort('merchant')">
                Merchant
                <span v-if="sortBy === 'merchant'">
                  {{ sortOrder === 'desc' ? '↓' : '↑' }}
                </span>
              </th>
              <th class="col-category">Category</th>
              <th class="col-category">Account</th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="transaction in transactions" 
              :key="transaction.id"
              class="transaction-row"
              :class="{ 
                'selected': selectedTransactions.includes(transaction.id),
                'auto-categorizing': categorizingTransactions.includes(transaction.id)
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
              
              <td class="col-amount" :class="getAmountClass(transaction)">
                <div class="amount-primary">{{ formatAmount(transaction.amount) }}</div>
                <div class="amount-secondary" v-if="transaction.transfer_pair_id">
                  Transfer ID: {{ transaction.transfer_pair_id }}
                </div>
              </td>
              
              <td class="col-merchant">
                <div class="merchant-primary">{{ transaction.merchant || 'Unknown Merchant' }}</div>
                <div class="merchant-secondary" v-if="transaction.memo">
                  {{ truncateText(transaction.memo, 80) }}
                </div>
              </td>
              
              <td class="col-category">
                <div class="category-assigned" v-if="transaction.main_category">
                  <div class="category-name">{{ transaction.main_category }}</div>
                  <div class="category-name" v-if="transaction.csv_category">{{ transaction.csv_category }}</div>
                </div>
                <div v-else class="text-muted">-</div>
                <div v-if="transaction.editing_category" class="category-selector-edit">
                  <select 
                    @change="categorizeTransaction(transaction.id, $event.target.value)"
                    class="category-select"
                    :disabled="categorizingTransactions.includes(transaction.id)"
                    :value="transaction.category_id || ''"
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
                  <button 
                    class="btn btn-small btn-link cancel-edit-btn" 
                    @click="cancelEditingCategory(transaction.id)"
                    title="Cancel"
                  >
                    Cancel
                  </button>
                </div>
              </td>
              

              
              <td class="col-category">
                <div class="category-assigned" v-if="transaction.owner || transaction.csv_account">
                  <div class="category-name" v-if="transaction.owner">{{ transaction.owner }}</div>
                  <div class="merchant-secondary" v-if="transaction.csv_account">{{ transaction.csv_account }}</div>
                </div>
                <div v-else class="text-muted">-</div>
              </td>
              
              <td class="col-actions">
                <div class="action-buttons">
                  <!-- Show edit button for category assignment -->
                  <button 
                    v-if="!transaction.editing_category"
                    class="btn btn-small btn-link" 
                    @click="startEditingCategory(transaction.id)"
                    title="Assign category"
                  >
                    Edit
                  </button>
                  
                  <!-- Show "Auto-categorizing..." for transactions being processed -->
                  <span v-if="categorizingTransactions.includes(transaction.id)" class="text-muted">
                    Processing...
                  </span>
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

    <!-- Reset Confirmation Modal -->
    <div v-if="showResetModal" class="modal-overlay" @click="showResetModal = false">
      <div class="modal-content reset-modal" @click.stop>
        <div class="modal-header">
          <h3>Reset All Transaction Data</h3>
        </div>
        
        <div class="modal-body">
          <div class="reset-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-text">
              <p><strong>This action cannot be undone!</strong></p>
              <p>This will permanently delete all {{ summary?.total_transactions || 0 }} transactions.</p>
              <p>Are you sure you want to continue?</p>
            </div>
          </div>
        </div>
        
        <div class="modal-actions">
          <button 
            class="btn btn-danger" 
            @click="confirmReset"
            :disabled="resetting"
          >
            {{ resetting ? 'Resetting...' : 'Yes, Reset All Data' }}
          </button>
          <button class="btn btn-link" @click="showResetModal = false" :disabled="resetting">
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
    
    // Filter state refs - updated for new structure
    const showFilters = ref(false)
    const filters = ref({
      startDate: '',
      endDate: '',
      minAmount: null,
      maxAmount: null,
      merchant: '',
      mainCategory: '',
      categoryFilter: '',
      transactionType: ''
    })
    
    // Selection and bulk action refs
    const selectedTransactions = ref([])
    const bulkCategoryId = ref('')
    const categorizingTransactions = ref([])
    
    // Modal state refs
    const showResetModal = ref(false)
    const resetting = ref(false)

    // Computed properties for filters
    const uniqueMainCategories = computed(() => {
      const categories = new Set()
      transactions.value.forEach(t => {
        if (t.main_category) {
          categories.add(t.main_category)
        }
      })
      return Array.from(categories).sort()
    })

    const uniqueCategories = computed(() => {
      const categories = new Set()
      transactions.value.forEach(t => {
        if (t.csv_category) {
          categories.add(t.csv_category)
        }
      })
      return Array.from(categories).sort()
    })

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
          response: `Processing ${file.name}... CSV categories will be imported and displayed directly.`
        })
        
        try {
          const token = await props.user.getIdToken()
          
          const formData = new FormData()
          formData.append('file', file)
          formData.append('account_name', 'Default Account')
          formData.append('account_type', 'checking')
          formData.append('auto_categorize', 'false') // No auto-categorization, just CSV data
          
          const response = await axios.post(`${API_BASE}/transactions/import`, formData, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            },
            timeout: 300000
          })
          
          upload.status = 'success'
          upload.rows = response.data.summary.rows_inserted || 0
          upload.summary = response.data.summary
          upload.batch_id = response.data.batch_id
          
          const duplicatesMsg = response.data.summary.rows_duplicated ? 
            ` (${response.data.summary.rows_duplicated} duplicates skipped)` : ''
          
          emit('add-chat-message', {
            message: `File uploaded: ${file.name}`,
            response: `Successfully imported ${file.name} with ${upload.rows} transactions!${duplicatesMsg} All CSV category data has been preserved.`
          })
          
          await loadSummary()
          await loadTransactions()
          
        } catch (error) {
          upload.status = 'error'
          console.error('Upload failed:', error)
          
          let errorMessage = 'Upload failed: Unknown error'
          if (error.response?.status === 401) {
            errorMessage = 'Authentication failed. Please try signing out and back in.'
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
          ...(filters.value.minAmount && { min_amount: filters.value.minAmount }),
          ...(filters.value.maxAmount && { max_amount: filters.value.maxAmount }),
          ...(filters.value.transactionType && { transaction_type: filters.value.transactionType })
          // Note: mainCategory and categoryFilter would need backend support for CSV field filtering
        })
        
        const response = await axios.get(`${API_BASE}/transactions/list?${params}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        let transactionData = response.data.map(transaction => ({
          ...transaction,
          editing_category: false
        }))

        // Client-side filtering for CSV categories since backend might not support them yet
        if (filters.value.mainCategory) {
          transactionData = transactionData.filter(t => 
            t.main_category && t.main_category.toLowerCase().includes(filters.value.mainCategory.toLowerCase())
          )
        }

        if (filters.value.categoryFilter) {
          transactionData = transactionData.filter(t => 
            t.csv_category && t.csv_category.toLowerCase().includes(filters.value.categoryFilter.toLowerCase())
          )
        }
        
        transactions.value = transactionData
        
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
              ...(filters.value.minAmount && { min_amount: filters.value.minAmount }),
              ...(filters.value.maxAmount && { max_amount: filters.value.maxAmount }),
              ...(filters.value.transactionType && { transaction_type: filters.value.transactionType })
            })
            
            const retryResponse = await axios.get(`${API_BASE}/transactions/list?${params}`, {
              headers: { 'Authorization': `Bearer ${newToken}` }
            })
            
            let retryData = retryResponse.data.map(transaction => ({
              ...transaction,
              editing_category: false
            }))

            // Apply client-side CSV filtering on retry as well
            if (filters.value.mainCategory) {
              retryData = retryData.filter(t => 
                t.main_category && t.main_category.toLowerCase().includes(filters.value.mainCategory.toLowerCase())
              )
            }

            if (filters.value.categoryFilter) {
              retryData = retryData.filter(t => 
                t.csv_category && t.csv_category.toLowerCase().includes(filters.value.categoryFilter.toLowerCase())
              )
            }
            
            transactions.value = retryData
            
            console.log('Transaction retry successful:', retryData.length)
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

    // Transaction management methods - simplified for CSV-first approach
    const startEditingCategory = (transactionId) => {
      const transaction = transactions.value.find(t => t.id === transactionId)
      if (transaction) {
        transaction.editing_category = true
      }
    }

    const cancelEditingCategory = (transactionId) => {
      const transaction = transactions.value.find(t => t.id === transactionId)
      if (transaction) {
        transaction.editing_category = false
      }
    }

    const categorizeTransaction = async (transactionId, categoryId) => {
      if (!categoryId || categorizingTransactions.value.includes(transactionId)) return
      
      categorizingTransactions.value.push(transactionId)
      
      // Stop editing mode
      const transaction = transactions.value.find(t => t.id === transactionId)
      if (transaction) {
        transaction.editing_category = false
      }
      
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
          message: 'Manual category override',
          response: `Transaction manually categorized as ${category?.name || 'selected category'}! This overrides the CSV category.`
        })
        
        await loadTransactions()
        await loadSummary()
        
      } catch (error) {
        console.error('Failed to categorize transaction:', error)
        emit('add-chat-message', {
          response: 'Failed to apply manual category. Please try again.'
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
          message: `Bulk manual categorization: ${selectedTransactions.value.length} transactions`,
          response: `Successfully applied manual category ${category?.name || 'selected category'} to ${selectedTransactions.value.length} transactions! This overrides CSV categories.`
        })
        
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

    // Filter methods - updated for new filter structure
    const clearFilters = () => {
      filters.value = {
        startDate: '',
        endDate: '',
        minAmount: null,
        maxAmount: null,
        merchant: '',
        mainCategory: '',
        categoryFilter: '',
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

    // Reset functionality
    const confirmReset = async () => {
      if (resetting.value) return
      
      resetting.value = true
      
      try {
        const token = await props.user.getIdToken()
        
        await axios.post(`${API_BASE}/transactions/reset`, {
          action: 'reset_all',
          confirm: true
        }, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        // Clear local state on success
        transactions.value = []
        summary.value = null
        selectedTransactions.value = []
        localUploads.value = []
        
        emit('add-chat-message', {
          message: 'Reset all transaction data',
          response: 'All transaction data has been successfully reset. You can now import fresh CSV files.'
        })
        
        showResetModal.value = false
        
      } catch (error) {
        console.error('Reset failed:', error)
        
        const errorMessage = 'Reset feature is not yet implemented on the server. Please contact support or manually delete data through database.'
        
        emit('add-chat-message', {
          response: errorMessage
        })
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
      
      // Filters - updated
      showFilters,
      filters,
      hasActiveFilters,
      uniqueMainCategories,
      uniqueCategories,
      
      // Selection and bulk actions
      selectedTransactions,
      bulkCategoryId,
      categorizingTransactions,
      allVisibleTransactionsSelected,
      
      // Modals
      showResetModal,
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
      startEditingCategory,
      cancelEditingCategory,
      categorizeTransaction,
      bulkCategorize,
      
      // Filter and UI methods
      clearFilters,
      toggleSort,
      
      // Selection methods
      toggleTransactionSelection,
      toggleAllTransactions,
      clearSelection,
      
      // Pagination methods
      changePage,
      changePageSize,
      
      // Reset methods
      confirmReset,
      
      // Utility methods
      formatDate,
      formatAmount,
      formatTransactionType,
      getAmountClass,
      truncateText
    }
  }
}
</script>