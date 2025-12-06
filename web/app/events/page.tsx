"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Sidebar from "@/components/sidebar"
import EventDashboard from "@/components/event-dashboard"
import { getLoggedInPhone } from "@/lib/auth"

export default function EventsPage() {
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [userPhone, setUserPhone] = useState<string | null>(null)
  const [userName, setUserName] = useState<string>('')

  useEffect(() => {
    const phone = getLoggedInPhone()
    if (!phone) {
      router.push('/login')
      return
    }
    setUserPhone(phone)

    // Fetch user profile for sidebar
    fetch(`/api/users/${encodeURIComponent(phone)}`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.user) {
          setUserName(data.user.name || '')
        }
      })
      .catch(() => {})
  }, [router])

  // Show nothing while checking auth
  if (!userPhone) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        userName={userName}
        userPhone={userPhone}
      />
      <div className={`flex-1 overflow-auto transition-all duration-300 ${sidebarOpen ? "ml-64" : "ml-0"}`}>
        <EventDashboard
          sidebarOpen={sidebarOpen}
          onMenuClick={() => setSidebarOpen(true)}
          userPhone={userPhone}
        />
      </div>
    </div>
  )
}
