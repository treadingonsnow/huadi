import React from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import Login from '@/views/Login'
import Dashboard from '@/views/admin/Dashboard'
import Search from '@/views/Search'

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token')
  if (!token) return <Navigate to="/login" replace />
  return children
}

const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  {
    path: '/dashboard',
    element: <ProtectedRoute><Dashboard /></ProtectedRoute>,
  },
  {
    path: '/search',
    element: <ProtectedRoute><Search /></ProtectedRoute>,
  },
  { path: '/', element: <Navigate to="/dashboard" replace /> },
  { path: '*', element: <Navigate to="/dashboard" replace /> },
])

export default router
