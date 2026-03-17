import React, { useState } from 'react'
import { Form, Input, Button, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { login } from '@/api/auth'
import { useUserStore } from '@/store'

export default function Login() {
  const navigate = useNavigate()
  const setToken = useUserStore((s) => s.setToken)
  const [loading, setLoading] = useState(false)

  const onFinish = async (values) => {
    setLoading(true)
    try {
      const res = await login({ username: values.username, password: values.password })
      if (res.code === 200) {
        setToken(res.data.access_token)
        message.success('登录成功')
        navigate('/dashboard')
      } else {
        message.error(res.message || '登录失败')
      }
    } catch {
      message.error('网络错误，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.logo}>🍜</div>
        <h1 style={styles.title}>上海美食大数据平台</h1>
        <p style={styles.subtitle}>Shanghai Food Analytics</p>
        <Form onFinish={onFinish} size="large" style={{ marginTop: 32 }}>
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" style={styles.input} />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" style={styles.input} />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={styles.btn}
            >
              登 录
            </Button>
          </Form.Item>
        </Form>
        <p style={styles.hint}>测试账号：admin / admin123</p>
      </div>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0d1117 0%, #1a1a2e 50%, #16213e 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(230,57,70,0.3)',
    borderRadius: 16,
    padding: '48px 40px',
    width: 400,
    textAlign: 'center',
    backdropFilter: 'blur(10px)',
    boxShadow: '0 8px 32px rgba(230,57,70,0.15)',
  },
  logo: { fontSize: 56, marginBottom: 8 },
  title: { color: '#ffffff', fontSize: 22, fontWeight: 700, margin: 0 },
  subtitle: { color: '#ffd700', fontSize: 13, marginTop: 4, letterSpacing: 2 },
  input: { background: 'rgba(255,255,255,0.08)', borderColor: 'rgba(255,255,255,0.15)' },
  btn: { background: '#e63946', borderColor: '#e63946', height: 44, fontSize: 16, fontWeight: 600 },
  hint: { color: '#8b949e', fontSize: 12, marginTop: 8 },
}
