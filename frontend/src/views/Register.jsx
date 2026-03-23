import React, { useState, useContext } from 'react'
import { Form, Input, Button } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { register } from '@/api/auth'
import { MessageContext } from '@/App'

export default function Register() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const { messageApi } = useContext(MessageContext)

  const onFinish = async (values) => {
    setLoading(true)
    try {
      const res = await register({ username: values.username, password: values.password })
      if (res.code === 200) {
        messageApi.success('注册成功，请登录', 1.5)
        navigate('/login')
      } else {
        const errorMessage = res.message || '注册失败'
        messageApi.error(errorMessage)
        form.setFields([{ name: 'username', errors: [errorMessage] }])
      }
    } catch (error) {
      const errorMessage = error?.response?.data?.message || '网络错误，请稍后重试'
      messageApi.error(errorMessage)
      form.setFields([{ name: 'username', errors: [errorMessage] }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.logo}>🍜</div>
        <h1 style={styles.title}>创建账号</h1>
        <p style={styles.subtitle}>Shanghai Food Analytics</p>
        <Form form={form} onFinish={onFinish} size="large" style={{ marginTop: 32 }}>
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" style={styles.input} />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" style={styles.input} />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请再次输入密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="确认密码" style={styles.input} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block style={styles.btn}>
              注 册
            </Button>
          </Form.Item>
        </Form>
        <Button type="link" onClick={() => navigate('/login')} style={styles.link}>
          已有账号？返回登录
        </Button>
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
  link: { color: '#ffd700', padding: 0 },
}
