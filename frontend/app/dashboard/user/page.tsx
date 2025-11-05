'use client'

import { useAuth } from '@/contexts/AuthContext'

export default function UserDetailsPage() {
  const { user } = useAuth()

  return (
    <div className="h-full p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-neon-cyan mb-6">User Details & Activity</h1>
        
        <div className="glass-effect rounded-2xl p-6 tech-border space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-text-primary mb-4">Profile Information</h2>
            <div className="space-y-3">
              <div>
                <label className="text-text-secondary text-sm">Name</label>
                <p className="text-text-primary font-medium">{user?.name}</p>
              </div>
              <div>
                <label className="text-text-secondary text-sm">Email</label>
                <p className="text-text-primary font-medium">{user?.email}</p>
              </div>
              <div>
                <label className="text-text-secondary text-sm">Role</label>
                <p className="text-text-primary font-medium capitalize">{user?.role}</p>
              </div>
            </div>
          </div>

          <div>
            <h2 className="text-xl font-semibold text-text-primary mb-4">Recent Activity</h2>
            <div className="space-y-2">
              <p className="text-text-muted text-sm">No recent activity to display.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

