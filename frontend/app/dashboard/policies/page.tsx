'use client'

export default function PoliciesPage() {
  return (
    <div className="h-full p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-neon-cyan mb-6">Client Policies</h1>
        
        <div className="glass-effect rounded-2xl p-6 tech-border space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-text-primary mb-4">IT Support Policies</h2>
            <div className="space-y-4 text-text-secondary">
              <p>Policy documents will be displayed here.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

