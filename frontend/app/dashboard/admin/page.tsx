'use client'

import { useState, useEffect, FormEvent } from 'react'
import { useAuth } from '@/contexts/AuthContext'

const STORAGE_KEY = 'supportron_users'

interface UserForm {
  name: string
  email: string
  password: string
  role: 'admin' | 'user'
}

export default function AdminPanel() {
  const { isAdmin } = useAuth()
  const [users, setUsers] = useState<any[]>([])
  const [showAddUser, setShowAddUser] = useState(false)
  const [formData, setFormData] = useState<UserForm>({
    name: '',
    email: '',
    password: '',
    role: 'user'
  })
  const [showUploadDocs, setShowUploadDocs] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        setUsers(JSON.parse(stored))
      }
    }
  }, [])

  if (!isAdmin) {
    return (
      <div className="h-full p-6 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-400 mb-2">Access Denied</h1>
          <p className="text-text-secondary">You don't have permission to access this page.</p>
        </div>
      </div>
    )
  }

  const handleAddUser = (e: FormEvent) => {
    e.preventDefault()
    
    const newUser = {
      id: `user-${Date.now()}`,
      ...formData,
      createdAt: new Date().toISOString()
    }

    const updatedUsers = [...users, newUser]
    setUsers(updatedUsers)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedUsers))
    
    setFormData({ name: '', email: '', password: '', role: 'user' })
    setShowAddUser(false)
  }

  const handleDeleteUser = (userId: string) => {
    if (confirm('Are you sure you want to delete this user?')) {
      const updatedUsers = users.filter(u => u.id !== userId)
      setUsers(updatedUsers)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedUsers))
    }
  }

  const handleFileUpload = (e: FormEvent) => {
    e.preventDefault()
    if (!selectedFile) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const fileData = {
        id: `doc-${Date.now()}`,
        name: selectedFile.name,
        size: selectedFile.size,
        type: selectedFile.type,
        uploadedAt: new Date().toISOString(),
        content: event.target?.result
      }

      const storedDocs = localStorage.getItem('supportron_docs') || '[]'
      const docs = JSON.parse(storedDocs)
      docs.push(fileData)
      localStorage.setItem('supportron_docs', JSON.stringify(docs))

      alert('Document uploaded successfully!')
      setSelectedFile(null)
      setShowUploadDocs(false)
    }
    reader.readAsDataURL(selectedFile)
  }

  return (
    <div className="h-full p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-neon-cyan mb-6">Admin Panel</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-effect rounded-2xl p-6 tech-border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-text-primary">User Management</h2>
              <button
                onClick={() => setShowAddUser(true)}
                className="px-4 py-2 bg-gradient-to-br from-neon-cyan to-cyber-blue text-white rounded-xl hover:from-neon-cyan/90 hover:to-cyber-blue/90 transition-all"
              >
                + Add User
              </button>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {users.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-3 bg-tech-surface rounded-xl border border-tech-border"
                >
                  <div>
                    <p className="text-text-primary font-medium">{user.name}</p>
                    <p className="text-text-muted text-sm">{user.email}</p>
                    <p className="text-text-muted text-xs capitalize">{user.role}</p>
                  </div>
                  <button
                    onClick={() => handleDeleteUser(user.id)}
                    className="px-3 py-1 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors text-sm"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-effect rounded-2xl p-6 tech-border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-text-primary">Reference Documents</h2>
              <button
                onClick={() => setShowUploadDocs(true)}
                className="px-4 py-2 bg-gradient-to-br from-accent to-accent-light text-white rounded-xl hover:opacity-90 transition-all"
              >
                + Upload Doc
              </button>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {(() => {
                const storedDocs = localStorage.getItem('supportron_docs')
                const docs = storedDocs ? JSON.parse(storedDocs) : []
                return docs.length > 0 ? (
                  docs.map((doc: any) => (
                    <div
                      key={doc.id}
                      className="p-3 bg-tech-surface rounded-xl border border-tech-border"
                    >
                      <p className="text-text-primary font-medium">{doc.name}</p>
                      <p className="text-text-muted text-xs">
                        {(doc.size / 1024).toFixed(2)} KB • {new Date(doc.uploadedAt).toLocaleDateString()}
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-text-muted text-sm">No documents uploaded</p>
                )
              })()}
            </div>
          </div>
        </div>
      </div>

      {showAddUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowAddUser(false)}>
          <div className="glass-effect rounded-2xl p-6 tech-border max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold text-neon-cyan mb-4">Add New User</h3>
            <form onSubmit={handleAddUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  className="w-full bg-tech-darker text-text-primary border border-tech-border rounded-xl px-4 py-2 focus:outline-none focus:border-neon-cyan"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="w-full bg-tech-darker text-text-primary border border-tech-border rounded-xl px-4 py-2 focus:outline-none focus:border-neon-cyan"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className="w-full bg-tech-darker text-text-primary border border-tech-border rounded-xl px-4 py-2 focus:outline-none focus:border-neon-cyan"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Role</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'user' })}
                  className="w-full bg-tech-darker text-text-primary border border-tech-border rounded-xl px-4 py-2 focus:outline-none focus:border-neon-cyan"
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-gradient-to-br from-neon-cyan to-cyber-blue text-white rounded-xl hover:from-neon-cyan/90 hover:to-cyber-blue/90 transition-all"
                >
                  Add User
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddUser(false)}
                  className="flex-1 px-4 py-2 bg-tech-surface border border-tech-border text-text-primary rounded-xl hover:bg-tech-surface-hover transition-all"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showUploadDocs && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowUploadDocs(false)}>
          <div className="glass-effect rounded-2xl p-6 tech-border max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold text-neon-cyan mb-4">Upload Reference Document</h3>
            <form onSubmit={handleFileUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Select File</label>
                <input
                  type="file"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  required
                  className="w-full bg-tech-darker text-text-primary border border-tech-border rounded-xl px-4 py-2 focus:outline-none focus:border-neon-cyan"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-gradient-to-br from-accent to-accent-light text-white rounded-xl hover:opacity-90 transition-all"
                >
                  Upload
                </button>
                <button
                  type="button"
                  onClick={() => setShowUploadDocs(false)}
                  className="flex-1 px-4 py-2 bg-tech-surface border border-tech-border text-text-primary rounded-xl hover:bg-tech-surface-hover transition-all"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

