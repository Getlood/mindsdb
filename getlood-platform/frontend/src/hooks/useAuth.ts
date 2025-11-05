import { useState, useEffect } from 'react'
import axios from 'axios'

interface User {
  id: string
  email: string
  display_name: string
  role: string
  tier: string
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  error: string | null
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('token'),
    isLoading: true,
    error: null
  })

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('token')

      if (!token) {
        setState(prev => ({ ...prev, isLoading: false }))
        return
      }

      try {
        const response = await axios.get('/api/v1/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        })

        setState({
          user: response.data,
          token,
          isLoading: false,
          error: null
        })
      } catch (error) {
        localStorage.removeItem('token')
        setState({
          user: null,
          token: null,
          isLoading: false,
          error: 'Session expired'
        })
      }
    }

    loadUser()
  }, [])

  const login = async (email: string, password: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const response = await axios.post('/api/v1/auth/login', {
        email,
        password
      })

      const { access_token } = response.data

      localStorage.setItem('token', access_token)

      // Load user info
      const userResponse = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      })

      setState({
        user: userResponse.data,
        token: access_token,
        isLoading: false,
        error: null
      })

      return true
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.response?.data?.detail || 'Login failed'
      }))
      return false
    }
  }

  const register = async (email: string, password: string, displayName: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const response = await axios.post('/api/v1/auth/register', {
        email,
        password,
        display_name: displayName
      })

      const { access_token } = response.data

      localStorage.setItem('token', access_token)

      // Load user info
      const userResponse = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      })

      setState({
        user: userResponse.data,
        token: access_token,
        isLoading: false,
        error: null
      })

      return true
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.response?.data?.detail || 'Registration failed'
      }))
      return false
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setState({
      user: null,
      token: null,
      isLoading: false,
      error: null
    })
  }

  return {
    user: state.user,
    token: state.token,
    isLoading: state.isLoading,
    error: state.error,
    isAuthenticated: !!state.user,
    login,
    register,
    logout
  }
}
