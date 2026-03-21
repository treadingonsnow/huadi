import { get, post } from '@/utils/request'

export const getModelInfo = () => get('/ml/info')
export const trainModel = () => post('/ml/train', {})
export const predictRating = (data) => post('/ml/predict', data)
