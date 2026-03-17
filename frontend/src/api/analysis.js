import { get } from '@/utils/request'

const USE_MOCK = true

const mockOverview = { total_count: 3186, avg_rating: 4.2, avg_price: 88.5, district_count: 16 }

const mockAreaDistribution = {
  districts: [
    { name: '浦东新区', count: 520 }, { name: '黄浦区', count: 310 },
    { name: '徐汇区', count: 280 }, { name: '静安区', count: 265 },
    { name: '长宁区', count: 198 }, { name: '普陀区', count: 175 },
    { name: '虹口区', count: 162 }, { name: '杨浦区', count: 155 },
    { name: '闵行区', count: 210 }, { name: '宝山区', count: 130 },
    { name: '嘉定区', count: 118 }, { name: '松江区', count: 105 },
    { name: '青浦区', count: 98 },  { name: '奉贤区', count: 82 },
    { name: '金山区', count: 75 },  { name: '崇明区', count: 103 },
  ]
}

const mockCuisineDistribution = {
  cuisines: [
    { name: '川菜', count: 420, percentage: 13.2 },
    { name: '本帮菜', count: 380, percentage: 11.9 },
    { name: '日料', count: 310, percentage: 9.7 },
    { name: '火锅', count: 290, percentage: 9.1 },
    { name: '粤菜', count: 245, percentage: 7.7 },
    { name: '西餐', count: 220, percentage: 6.9 },
    { name: '烧烤', count: 185, percentage: 5.8 },
    { name: '面食', count: 175, percentage: 5.5 },
    { name: '海鲜', count: 160, percentage: 5.0 },
    { name: '其他', count: 601, percentage: 18.9 },
  ]
}

const mockPriceDistribution = {
  ranges: [
    { label: '50元以下', count: 380 },
    { label: '50-100元', count: 920 },
    { label: '100-200元', count: 1050 },
    { label: '200-300元', count: 520 },
    { label: '300元以上', count: 316 },
  ]
}

const mockRatingDistribution = {
  ratings: [
    { range: '2.0-3.0', count: 45 },
    { range: '3.0-3.5', count: 120 },
    { range: '3.5-4.0', count: 380 },
    { range: '4.0-4.5', count: 1420 },
    { range: '4.5-5.0', count: 1221 },
  ]
}

const mockReviewKeywords = {
  positive: [
    { word: '好吃', count: 2100 }, { word: '环境好', count: 1800 },
    { word: '服务好', count: 1650 }, { word: '性价比高', count: 1400 },
    { word: '新鲜', count: 1200 }, { word: '味道正宗', count: 1100 },
    { word: '分量足', count: 980 }, { word: '干净', count: 850 },
    { word: '推荐', count: 820 }, { word: '实惠', count: 780 },
    { word: '好评', count: 750 }, { word: '必吃', count: 680 },
  ],
  negative: [
    { word: '等位久', count: 520 }, { word: '偏贵', count: 480 },
    { word: '服务差', count: 320 }, { word: '口味一般', count: 290 },
    { word: '上菜慢', count: 260 }, { word: '停车难', count: 210 },
  ]
}

const mockAreaAvgPrice = {
  districts: [
    { name: '黄浦区', avg_price: 138.5 }, { name: '静安区', avg_price: 132.0 },
    { name: '徐汇区', avg_price: 118.5 }, { name: '长宁区', avg_price: 112.0 },
    { name: '浦东新区', avg_price: 105.5 }, { name: '虹口区', avg_price: 98.0 },
    { name: '杨浦区', avg_price: 92.5 }, { name: '普陀区', avg_price: 88.0 },
    { name: '闵行区', avg_price: 85.5 }, { name: '宝山区', avg_price: 78.0 },
    { name: '嘉定区', avg_price: 75.5 }, { name: '松江区', avg_price: 72.0 },
    { name: '青浦区', avg_price: 70.5 }, { name: '奉贤区', avg_price: 65.0 },
    { name: '金山区', avg_price: 62.5 }, { name: '崇明区', avg_price: 58.0 },
  ]
}

export const getOverview = () =>
  USE_MOCK ? Promise.resolve({ code: 200, data: mockOverview }) : get('/analysis/overview')

export const getAreaDistribution = () =>
  USE_MOCK ? Promise.resolve({ code: 200, data: mockAreaDistribution }) : get('/analysis/area-distribution')

export const getCuisineDistribution = () =>
  USE_MOCK ? Promise.resolve({ code: 200, data: mockCuisineDistribution }) : get('/analysis/cuisine-distribution')

export const getPriceDistribution = () =>
  USE_MOCK ? Promise.resolve({ code: 200, data: mockPriceDistribution }) : get('/analysis/price-distribution')

export const getRatingDistribution = () =>
  USE_MOCK ? Promise.resolve({ code: 200, data: mockRatingDistribution }) : get('/analysis/rating-distribution')

export const getReviewKeywords = () =>
  USE_MOCK ? Promise.resolve({ code: 200, data: mockReviewKeywords }) : get('/analysis/review-keywords')

export const getAreaAvgPrice = () =>
  USE_MOCK ? Promise.resolve({ code: 200, data: mockAreaAvgPrice }) : get('/analysis/area-avg-price')
