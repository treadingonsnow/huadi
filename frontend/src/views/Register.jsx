import React, { useState } from 'react'
import { Form, Input, Button, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { register } from '@/api/auth'

export default function Register() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  const onFinish = async (values) => {
    setLoading(true)
    try {
      const res = await register({ username: values.username, password: values.password })
      if (res.code === 200) {
        message.success('注册成功，请登录')
        navigate('/login')
      } else {
        message.error(res.message || '注册失败')
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
        <p style={styles.subtitle}>创建新账号</p>
        <Form onFinish={onFinish} size="large" style={{ marginTop: 32 }}>
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }, { min: 3, max: 20, message: '用户名长度3-20个字符' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名（3-20个字符）" style={styles.input} />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }, { min: 6, message: '密码至少6个字符' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码（至少6个字符）" style={styles.input} />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({ validator(_, value) { return !value || getFieldValue('password') === value ? Promise.resolve() : Promise.reject(new Error('两次密码不一致')) } }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="确认密码" style={styles.input} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block style={styles.btn}>注 册</Button>
          </Form.Item>
        </Form>
        <p style={styles.hint}>已有账号？<a style={styles.link} onClick={() => navigate('/login')}>返回登录</a></p>
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
  link: { color: '#ffd700', cursor: 'pointer' },
}
