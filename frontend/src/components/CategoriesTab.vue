<template>
  <div class="tab-content">
    <div class="grid grid-sidebar">
      <!-- Category Tree -->
      <div class="container">
        <div class="text-medium section-header">Categories</div>
        <div class="flex-column">
          <!-- Transaction Types -->
          <div
            v-for="type in categoriesData"
            :key="type.id"
            class="category-group"
          >
            <!-- Transaction Type -->
            <button
              class="category-btn"
              :class="{ active: selectedCategory?.id === type.id }"
              @click="$emit('select-category', type)"
            >
              <AppIcon :name="type.icon" size="medium" />
              <span>{{ type.name }}</span>
            </button>

            <!-- Categories inside Transaction Type -->
            <div v-if="type.categories" class="subcategories">
              <div
                v-for="category in type.categories"
                :key="category.id"
                class="category-type"
              >
                <!-- Category header with expand toggle -->
                <div
                  class="category-btn category-indent flex-between"
                  :class="{ active: selectedCategory?.id === category.id }"
                >
                  <div
                    class="flex flex-gap"
                    @click="$emit('select-category', category)"
                  >
                    <AppIcon :name="category.icon" size="medium" />
                    <span>{{ category.name }}</span>
                  </div>
                  <button
                    class="toggle-btn"
                    @click="toggleCategory(category.id)"
                  >
                    <span v-if="isExpanded(category.id)">−</span>
                    <span v-else>+</span>
                  </button>
                </div>

                <!-- Subcategories (collapsed by default) -->
                <div
                  v-if="isExpanded(category.id)"
                  class="subcategories"
                >
                  <button
                    v-for="subcategory in category.children"
                    :key="subcategory.id"
                    class="category-btn category-indent-2"
                    :class="{ active: selectedCategory?.id === subcategory.id }"
                    @click="$emit('select-category', subcategory)"
                  >
                    <AppIcon :name="subcategory.icon" size="medium" />
                    <span>{{ subcategory.name }}</span>
                  </button>
                </div>
              </div>
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
                {{ getParentCategoryName(selectedCategory) }}
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
</template>

<script>
import AppIcon from './AppIcon.vue'

export default {
  name: 'CategoriesTab',
  components: { AppIcon },
  props: {
    categoriesData: {
      type: Array,
      required: true
    },
    selectedCategory: Object
  },
  emits: ['select-category'],
  data() {
    return {
      expandedCategories: {} // { [categoryId]: true/false }
    }
  },
  methods: {
    toggleCategory(id) {
      // Instead of this.$set, replace the object immutably
      this.expandedCategories = {
        ...this.expandedCategories,
        [id]: !this.expandedCategories[id]
      }
    },
    isExpanded(id) {
      return !!this.expandedCategories[id]
    },
    getParentCategoryName(item) {
      for (const type of this.categoriesData) {
        if (type.id === item.id) return `${type.name} (Transaction Type)`
        for (const category of type.categories) {
          if (category.id === item.id) return `${type.name} → ${category.name}`
          const found = category.children.find(c => c.id === item.id)
          if (found) return `${type.name} → ${category.name}`
        }
      }
      return ''
    }
  }
}
</script>


<style scoped>
.category-indent {
  margin-left: 1rem;
}
.category-indent-2 {
  margin-left: 2rem;
}
.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-weight: bold;
  padding-bottom: 0.25rem;
}
</style>
