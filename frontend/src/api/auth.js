import request, { post } from '@/utils/request'

const USE_MOCK = false

export const login = (data) => {
  if (USE_MOCK) {
    if (data.username === 'admin' && data.password === 'admin123') {
      return Promise.resolve({ code: 200, message: 'success', data: { access_token: 'mock-token-admin', token_type: 'bearer' } })
    }
    if (data.username === 'analyst' && data.password === 'analyst123') {
      return Promise.resolve({ code: 200, message: 'success', data: { access_token: 'mock-token-analyst', token_type: 'bearer' } })
    }
    return Promise.resolve({ code: 401, message: '用户名或密码错误', data: null })
  }
  return post('/auth/login', data)
}

export const register = (data) => {
  if (USE_MOCK) {
    if (!data.username || !data.password) {
      return Promise.resolve({ code: 400, message: '用户名或密码不能为空', data: null })
    }
    return Promise.resolve({ code: 200, message: 'success', data: { user_id: 1, username: data.username, role: 'user' } })
  }
  return request.post('/auth/register', null, { params: data })
}
