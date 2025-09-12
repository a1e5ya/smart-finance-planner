export const categoriesData = [
  {
    id: 'transfers',
    name: 'TRANSFERS',
    icon: 'copy-alt',
    children: [
      {
        id: 'account-transfers-own',
        name: 'Between Own Accounts',
        parentId: 'transfers',
        icon: 'copy-alt'
      },
      {
        id: 'account-transfers-family',
        name: 'Family Support',
        parentId: 'transfers',
        icon: 'hand-holding-heart'
      },
      {
        id: 'account-transfers-reserve',
        name: 'Reserve Transfer',
        parentId: 'transfers',
        icon: 'chart-histogram'
      },
      {
        id: 'savings-transfer',
        name: 'Savings Transfer',
        parentId: 'transfers',
        icon: 'calculator'
      },
      {
        id: 'house-savings',
        name: 'House Savings',
        parentId: 'transfers',
        icon: 'home-location-alt'
      }
    ]
  },
  {
    id: 'income',
    name: 'INCOME',
    icon: 'briefcase',
    children: [
      {
        id: 'unemployment-benefits',
        name: 'Unemployment Benefits',
        parentId: 'income',
        icon: 'comment-check'
      },
      {
        id: 'social-benefits',
        name: 'Social Benefits',
        parentId: 'income',
        icon: 'comment-heart'
      },
      {
        id: 'salary',
        name: 'Salary',
        parentId: 'income',
        icon: 'briefcase'
      },
      {
        id: 'gifts-received',
        name: 'Gifts Received',
        parentId: 'income',
        icon: 'gift'
      },
      {
        id: 'cashback',
        name: 'Cashback',
        parentId: 'income',
        icon: 'credit-card'
      },
      {
        id: 'dividends-interest',
        name: 'Dividends & Interest',
        parentId: 'income',
        icon: 'chat-arrow-grow'
      }
    ]
  },
  {
    id: 'expenses',
    name: 'EXPENSES',
    icon: 'shopping-cart',
    children: [
      // Food
      {
        id: 'cafes-coffee',
        name: 'Cafes & Coffee',
        parentId: 'expenses',
        category: 'Food',
        icon: 'coffee'
      },
      {
        id: 'groceries',
        name: 'Groceries',
        parentId: 'expenses',
        category: 'Food',
        icon: 'salad'
      },
      {
        id: 'restaurants',
        name: 'Restaurants',
        parentId: 'expenses',
        category: 'Food',
        icon: 'room-service'
      },
      {
        id: 'sweets',
        name: 'Sweets',
        parentId: 'expenses',
        category: 'Food',
        icon: 'ice-cream'
      },
      // Family
      {
        id: 'sports-activities',
        name: 'Sports Activities',
        parentId: 'expenses',
        category: 'Family',
        icon: 'ice-skate'
      },
      {
        id: 'child-activities',
        name: "Child's Activities",
        parentId: 'expenses',
        category: 'Family',
        icon: 'ferris-wheel'
      },
      {
        id: 'toys-games',
        name: 'Toys & Games',
        parentId: 'expenses',
        category: 'Family',
        icon: 'kite'
      },
      // Housing & Utilities
      {
        id: 'monthly-rent',
        name: 'Monthly Rent',
        parentId: 'expenses',
        category: 'Housing & Utilities',
        icon: 'key'
      },
      {
        id: 'internet-phone',
        name: 'Internet & Phone',
        parentId: 'expenses',
        category: 'Housing & Utilities',
        icon: 'signal-alt-2'
      },
      {
        id: 'energy-water',
        name: 'Energy & Water',
        parentId: 'expenses',
        category: 'Housing & Utilities',
        icon: 'bulb'
      },
      // Shopping
      {
        id: 'household',
        name: 'Household',
        parentId: 'expenses',
        category: 'Shopping',
        icon: 'soap'
      },
      {
        id: 'electronics',
        name: 'Electronics',
        parentId: 'expenses',
        category: 'Shopping',
        icon: 'gamepad'
      },
      {
        id: 'clothing-shoes',
        name: 'Clothing & Shoes',
        parentId: 'expenses',
        category: 'Shopping',
        icon: 'label'
      },
      {
        id: 'accessories',
        name: 'Accessories',
        parentId: 'expenses',
        category: 'Shopping',
        icon: 'lipstick'
      },
      {
        id: 'subscriptions',
        name: 'Subscriptions',
        parentId: 'expenses',
        category: 'Shopping',
        icon: 'interactive'
      },
      {
        id: 'guilty-pleasure',
        name: 'Guilty pleasure',
        parentId: 'expenses',
        category: 'Shopping',
        icon: 'glass-cheers'
      },
      // Leisure & Culture
      {
        id: 'music',
        name: 'Music',
        parentId: 'expenses',
        category: 'Leisure & Culture',
        icon: 'guitar'
      },
      {
        id: 'social-activities',
        name: 'Social Activities',
        parentId: 'expenses',
        category: 'Leisure & Culture',
        icon: 'ticket'
      },
      {
        id: 'education',
        name: 'Education',
        parentId: 'expenses',
        category: 'Leisure & Culture',
        icon: 'graduation-cap'
      },
      {
        id: 'books-media',
        name: 'Books & Media',
        parentId: 'expenses',
        category: 'Leisure & Culture',
        icon: 'book-alt'
      },
      {
        id: 'hobbies-crafts',
        name: 'Hobbies & Crafts',
        parentId: 'expenses',
        category: 'Leisure & Culture',
        icon: 'palette'
      },
      // Health
      {
        id: 'pharmacy',
        name: 'Pharmacy',
        parentId: 'expenses',
        category: 'Health',
        icon: 'band-aid'
      },
      {
        id: 'medical-services',
        name: 'Medical Services',
        parentId: 'expenses',
        category: 'Health',
        icon: 'stethoscope'
      },
      {
        id: 'dental-care',
        name: 'Dental Care',
        parentId: 'expenses',
        category: 'Health',
        icon: 'tooth'
      },
      {
        id: 'gym-fitness',
        name: 'Gym & Fitness',
        parentId: 'expenses',
        category: 'Health',
        icon: 'gym'
      },
      // Transport
      {
        id: 'vehicle-registration',
        name: 'Vehicle Registration & Tax',
        parentId: 'expenses',
        category: 'Transport',
        icon: 'car'
      },
      {
        id: 'maintenance-repairs',
        name: 'Maintenance & Repairs',
        parentId: 'expenses',
        category: 'Transport',
        icon: 'dashboard'
      },
      {
        id: 'fuel',
        name: 'Fuel',
        parentId: 'expenses',
        category: 'Transport',
        icon: 'gas-pump'
      },
      {
        id: 'parking-fees',
        name: 'Parking Fees',
        parentId: 'expenses',
        category: 'Transport',
        icon: 'road'
      },
      {
        id: 'public-transport',
        name: 'Public Transport',
        parentId: 'expenses',
        category: 'Transport',
        icon: 'train-side'
      },
      // Insurance
      {
        id: 'health-insurance',
        name: 'Health Insurance',
        parentId: 'expenses',
        category: 'Insurance',
        icon: 'syringe'
      },
      {
        id: 'home-insurance',
        name: 'Home Insurance',
        parentId: 'expenses',
        category: 'Insurance',
        icon: 'document-signed'
      },
      {
        id: 'vehicle-insurance',
        name: 'Vehicle Insurance',
        parentId: 'expenses',
        category: 'Insurance',
        icon: 'document-signed'
      },
      // Financial Management
      {
        id: 'bureaucracy',
        name: 'Bureaucracy',
        parentId: 'expenses',
        category: 'Financial Management',
        icon: 'diploma'
      },
      {
        id: 'investment-accounts',
        name: 'Investment Accounts',
        parentId: 'expenses',
        category: 'Financial Management',
        icon: 'earnings'
      },
      // Financial Services
      {
        id: 'withdrawal',
        name: 'Withdrawal',
        parentId: 'expenses',
        category: 'Financial Services',
        icon: 'euro'
      },
      {
        id: 'payment-provider',
        name: 'Payment provider',
        parentId: 'expenses',
        category: 'Financial Services',
        icon: 'shopping-cart'
      },
      {
        id: 'bank-services',
        name: 'Bank Services',
        parentId: 'expenses',
        category: 'Financial Services',
        icon: 'bank'
      }
    ]
  }
]

// Helper functions
export const getCategoryById = (id) => {
  for (const mainCategory of categoriesData) {
    if (mainCategory.id === id) return mainCategory
    const subcategory = mainCategory.children?.find(child => child.id === id)
    if (subcategory) return subcategory
  }
  return null
}

export const getSubcategoriesByType = (type) => {
  const expensesCategory = categoriesData.find(cat => cat.id === 'expenses')
  if (!expensesCategory) return []
  
  return expensesCategory.children.filter(child => child.category === type)
}

export const getAllExpenseCategories = () => {
  const expensesCategory = categoriesData.find(cat => cat.id === 'expenses')
  if (!expensesCategory) return []
  
  // Get unique category types
  const categoryTypes = [...new Set(expensesCategory.children.map(child => child.category))]
  
  return categoryTypes.map(type => ({
    name: type,
    subcategories: getSubcategoriesByType(type)
  }))
}