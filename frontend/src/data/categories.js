export const categoriesData = [
  {
    id: 'income',
    name: 'INCOME',
    icon: 'apps-add',
    categories: [
      {
        id: 'benefits-support',
        name: 'Benefits & Support',
        icon: 'comment-check',
        children: [
          { id: 'unemployment-benefits', name: 'Unemployment Benefits', icon: 'comment-check' },
          { id: 'social-benefits', name: 'Social Benefits', icon: 'comment-heart' }
        ]
      },
      {
        id: 'employment-income',
        name: 'Employment Income',
        icon: 'briefcase',
        children: [
          { id: 'salary', name: 'Salary', icon: 'briefcase' }
        ]
      },
      {
        id: 'other-income',
        name: 'Other Income',
        icon: 'gift',
        children: [
          { id: 'gifts-received', name: 'Gifts Received', icon: 'gift' }
        ]
      },
      {
        id: 'investment-income',
        name: 'Investment Income',
        icon: 'credit-card',
        children: [
          { id: 'cashback', name: 'Cashback', icon: 'credit-card' },
          { id: 'dividends-interest', name: 'Dividends & Interest', icon: 'chat-arrow-grow' }
        ]
      }
    ]
  },
  {
    id: 'expenses',
    name: 'EXPENSES',
    icon: 'apps-delete',
    categories: [
      {
        id: 'food',
        name: 'Food',
        icon: 'coffee',
        children: [
          { id: 'cafes-coffee', name: 'Cafes & Coffee', icon: 'coffee' },
          { id: 'groceries', name: 'Groceries', icon: 'salad' },
          { id: 'restaurants', name: 'Restaurants', icon: 'room-service' },
          { id: 'sweets', name: 'Sweets', icon: 'ice-cream' }
        ]
      },
      {
        id: 'family',
        name: 'Family',
        icon: 'kite',
        children: [
          { id: 'sports-activities', name: 'Sports Activities', icon: 'ice-skate' },
          { id: 'child-activities', name: "Child's Activities", icon: 'ferris-wheel' },
          { id: 'toys-games', name: 'Toys & Games', icon: 'kite' }
        ]
      },
      {
        id: 'housing-utilities',
        name: 'Housing & Utilities',
        icon: 'key',
        children: [
          { id: 'monthly-rent', name: 'Monthly Rent', icon: 'key' },
          { id: 'internet-phone', name: 'Internet & Phone', icon: 'signal-alt-2' },
          { id: 'energy-water', name: 'Energy & Water', icon: 'bulb' }
        ]
      },
      {
        id: 'shopping',
        name: 'Shopping',
        icon: 'shopping-cart',
        children: [
          { id: 'household', name: 'Household', icon: 'soap' },
          { id: 'electronics', name: 'Electronics', icon: 'gamepad' },
          { id: 'clothing-shoes', name: 'Clothing & Shoes', icon: 'label' },
          { id: 'accessories', name: 'Accessories', icon: 'lipstick' },
          { id: 'subscriptions', name: 'Subscriptions', icon: 'interactive' },
          { id: 'guilty-pleasure', name: 'Guilty Pleasure', icon: 'glass-cheers' }
        ]
      },
      {
        id: 'leisure-culture',
        name: 'Leisure & Culture',
        icon: 'ticket',
        children: [
          { id: 'music', name: 'Music', icon: 'guitar' },
          { id: 'social-activities', name: 'Social Activities', icon: 'ticket' },
          { id: 'education', name: 'Education', icon: 'graduation-cap' },
          { id: 'books-media', name: 'Books & Media', icon: 'book-alt' },
          { id: 'hobbies-crafts', name: 'Hobbies & Crafts', icon: 'palette' }
        ]
      },
      {
        id: 'health',
        name: 'Health',
        icon: 'stethoscope',
        children: [
          { id: 'pharmacy', name: 'Pharmacy', icon: 'band-aid' },
          { id: 'medical-services', name: 'Medical Services', icon: 'stethoscope' },
          { id: 'dental-care', name: 'Dental Care', icon: 'tooth' },
          { id: 'gym-fitness', name: 'Gym & Fitness', icon: 'gym' }
        ]
      },
      {
        id: 'transport',
        name: 'Transport',
        icon: 'car',
        children: [
          { id: 'vehicle-registration', name: 'Vehicle Registration & Tax', icon: 'car' },
          { id: 'maintenance-repairs', name: 'Maintenance & Repairs', icon: 'dashboard' },
          { id: 'fuel', name: 'Fuel', icon: 'gas-pump' },
          { id: 'parking-fees', name: 'Parking Fees', icon: 'road' },
          { id: 'public-transport', name: 'Public Transport', icon: 'train-side' }
        ]
      },
      {
        id: 'insurance',
        name: 'Insurance',
        icon: 'document-signed',
        children: [
          { id: 'health-insurance', name: 'Health Insurance', icon: 'syringe' },
          { id: 'home-insurance', name: 'Home Insurance', icon: 'document-signed' },
          { id: 'vehicle-insurance', name: 'Vehicle Insurance', icon: 'document-signed' }
        ]
      },
      {
        id: 'financial-management',
        name: 'Financial Management',
        icon: 'diploma',
        children: [
          { id: 'bureaucracy', name: 'Bureaucracy', icon: 'diploma' },
          { id: 'investment-accounts', name: 'Investment Accounts', icon: 'earnings' }
        ]
      },
      {
        id: 'financial-services',
        name: 'Financial Services',
        icon: 'bank',
        children: [
          { id: 'withdrawal', name: 'Withdrawal', icon: 'euro' },
          { id: 'payment-provider', name: 'Payment Provider', icon: 'shopping-cart' },
          { id: 'bank-services', name: 'Bank Services', icon: 'bank' }
        ]
      }
    ]
  },
    {
    id: 'transfers',
    name: 'TRANSFERS',
    icon: 'apps-sort',
    categories: [
      {
        id: 'account-transfers',
        name: 'Account Transfers',
        icon: 'copy-alt',
        children: [
          { id: 'account-transfers-own', name: 'Between Own Accounts', icon: 'copy-alt' },
          { id: 'account-transfers-family', name: 'Family Support', icon: 'hand-holding-heart' },
          { id: 'account-transfers-reserve', name: 'Reserve Transfer', icon: 'chart-histogram' }
        ]
      },
      {
        id: 'savings-transfer',
        name: 'Savings Transfer',
        icon: 'calculator',
        children: [
          { id: 'savings-transfer-main', name: 'Savings Transfer', icon: 'calculator' },
          { id: 'house-savings', name: 'House Savings', icon: 'home-location-alt' }
        ]
      }
    ]
  }
]

/**
 * Find any transaction type, category, or subcategory by ID
 */
export const getCategoryById = (id) => {
  for (const type of categoriesData) {
    if (type.id === id) return type
    for (const category of type.categories) {
      if (category.id === id) return category
      const subcategory = category.children.find(child => child.id === id)
      if (subcategory) return subcategory
    }
  }
  return null
}

/**
 * Get all categories for a given transaction type
 */
export const getCategoriesByType = (typeId) => {
  const type = categoriesData.find(t => t.id === typeId)
  return type ? type.categories : []
}

/**
 * Get all subcategories for a given category ID
 */
export const getSubcategoriesByCategory = (categoryId) => {
  for (const type of categoriesData) {
    const category = type.categories.find(cat => cat.id === categoryId)
    if (category) return category.children
  }
  return []
}

/**
 * Get full structured data for a transaction type:
 * Categories with their subcategories
 */
export const getAllCategoriesWithSubcategories = (typeId) => {
  const type = categoriesData.find(t => t.id === typeId)
  if (!type) return []
  return type.categories.map(cat => ({
    ...cat,
    subcategories: cat.children
  }))
}
