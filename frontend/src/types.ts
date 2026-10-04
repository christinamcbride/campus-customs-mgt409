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
