import React, { createContext } from 'react'
import { RouterProvider } from 'react-router-dom'
import { message } from 'antd'
import router from '@/router'

export const MessageContext = createContext({ messageApi: message })

export default function App() {
  const [messageApi, contextHolder] = message.useMessage()
  return (
    <MessageContext.Provider value={{ messageApi }}>
      {contextHolder}
      <RouterProvider router={router} />
    </MessageContext.Provider>
  )
}
