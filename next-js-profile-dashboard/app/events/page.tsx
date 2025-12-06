"use client"

import { useState } from "react"
import Sidebar from "@/components/sidebar"
import EventDashboard from "@/components/event-dashboard"

// Default user phone for demo - in production would come from auth/session
const DEFAULT_USER_PHONE = "+15550000000"

export default function EventsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <div className={`flex-1 overflow-auto transition-all duration-300 ${sidebarOpen ? "ml-64" : "ml-0"}`}>
        <EventDashboard
          sidebarOpen={sidebarOpen}
          onMenuClick={() => setSidebarOpen(true)}
          userPhone={DEFAULT_USER_PHONE}
        />
      </div>
    </div>
  )
}
