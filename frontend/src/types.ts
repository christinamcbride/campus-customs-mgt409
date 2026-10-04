export interface SizeStock {
  size: string
  quantity: number
  in_stock: boolean
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  category: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  total_stock: number | null
}

export interface ProductDetail extends Product {
  sizes: SizeStock[]
}

export interface ProductPage {
  items: Product[]
  total: number
  limit: number
  offset: number
}

export interface CategoryList {
  categories: string[]
  price_min: number
  price_max: number
}

export interface User {
  id: number
  name: string
  email: string
  first_name: string | null
  last_name: string | null
  created_at: string
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

export interface ChatReply {
  reply: string
  products: Product[]
  matched_for: string | null
}

export interface ChatHistoryMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  products: Product[]
  created_at: string
}
