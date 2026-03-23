import request, { get } from '@/utils/request'

const USE_MOCK = false

const mockRestaurants = [
  { id: 1, name: '外婆家（南京西路店）', cuisine_type: '本帮菜', district: '静安区', business_area: '南京西路', avg_price: 85, rating: 4.6, review_count: 3200, address: '南京西路1038号梅龙镇广场B1', phone: '021-****8888' },
  { id: 2, name: '鼎泰丰（新天地店）', cuisine_type: '台湾菜', district: '黄浦区', business_area: '新天地', avg_price: 120, rating: 4.7, review_count: 5600, address: '马当路181号新天地北里', phone: '021-****6888' },
  { id: 3, name: '小龙坎老火锅（徐家汇店）', cuisine_type: '火锅', district: '徐汇区', business_area: '徐家汇', avg_price: 95, rating: 4.5, review_count: 2800, address: '虹桥路1号港汇恒隆广场B2', phone: '021-****7777' },
  { id: 4, name: '南京大牌档（浦东店）', cuisine_type: '本帮菜', district: '浦东新区', business_area: '陆家嘴', avg_price: 75, rating: 4.4, review_count: 1900, address: '世纪大道8号国金中心B1', phone: '021-****5555' },
  { id: 5, name: '海底捞（静安寺店）', cuisine_type: '火锅', district: '静安区', business_area: '静安寺', avg_price: 130, rating: 4.8, review_count: 8900, address: '愚园路1号嘉里中心B1', phone: '021-****9999' },
  { id: 6, name: '一兰拉面（人民广场店）', cuisine_type: '日料', district: '黄浦区', business_area: '人民广场', avg_price: 80, rating: 4.5, review_count: 4200, address: '西藏中路268号来福士广场B1', phone: '021-****3333' },
  { id: 7, name: '避风塘（长宁店）', cuisine_type: '粤菜', district: '长宁区', business_area: '中山公园', avg_price: 110, rating: 4.3, review_count: 1500, address: '长宁路1018号龙之梦购物中心4F', phone: '021-****4444' },
  { id: 8, name: '老吉士酒家', cuisine_type: '本帮菜', district: '徐汇区', business_area: '衡山路', avg_price: 95, rating: 4.6, review_count: 2100, address: '天平路41号', phone: '021-****2222' },
  { id: 9, name: '新荣记（静安店）', cuisine_type: '海鲜', district: '静安区', business_area: '南京西路', avg_price: 380, rating: 4.9, review_count: 1200, address: '南京西路1515号嘉里中心', phone: '021-****1111' },
  { id: 10, name: '喜茶（陆家嘴店）', cuisine_type: '甜品饮品', district: '浦东新区', business_area: '陆家嘴', avg_price: 35, rating: 4.4, review_count: 6800, address: '世纪大道100号上海环球金融中心B1', phone: '021-****6666' },
  { id: 11, name: '大董烤鸭（浦东店）', cuisine_type: '北京菜', district: '浦东新区', business_area: '张江', avg_price: 220, rating: 4.7, review_count: 3400, address: '张衡路500号', phone: '021-****0000' },
  { id: 12, name: '巴奴毛肚火锅（徐汇店）', cuisine_type: '火锅', district: '徐汇区', business_area: '徐家汇', avg_price: 115, rating: 4.6, review_count: 2600, address: '漕溪北路8号美罗城5F', phone: '021-****8866' },
]

export const searchRestaurants = (params) => {
  if (USE_MOCK) {
    let items = [...mockRestaurants]
    if (params?.keyword) {
      const kw = params.keyword.toLowerCase()
      items = items.filter(r => r.name.includes(kw) || r.cuisine_type.includes(kw) || r.district.includes(kw))
    }
    if (params?.cuisine) items = items.filter(r => r.cuisine_type === params.cuisine)
    if (params?.district) items = items.filter(r => r.district === params.district)
    if (params?.price_min) items = items.filter(r => r.avg_price >= Number(params.price_min))
    if (params?.price_max) items = items.filter(r => r.avg_price <= Number(params.price_max))
    if (params?.rating_min) items = items.filter(r => r.rating >= Number(params.rating_min))
    const page = params?.page || 1
    const page_size = params?.page_size || 20
    const start = (page - 1) * page_size
    return Promise.resolve({ code: 200, data: { total: items.length, items: items.slice(start, start + page_size) } })
  }
  return get('/restaurants/search', params)
}

export const getRestaurantDetail = (id) => {
  if (USE_MOCK) {
    const item = mockRestaurants.find(r => r.id === Number(id))
    return Promise.resolve({ code: 200, data: item || null })
  }
  return get(`/restaurants/${id}`)
}

export const getFavorites = (params) => {
  if (USE_MOCK) {
    return Promise.resolve({ code: 200, data: { items: [] } })
  }
  return get('/restaurants/favorites', params)
}

export const toggleFavorite = (restaurantId) => {
  if (USE_MOCK) {
    return Promise.resolve({ code: 200, data: { action: 'add', message: '已收藏' } })
  }
  return request.post('/restaurants/favorites', null, { params: { restaurant_id: restaurantId } })
}
