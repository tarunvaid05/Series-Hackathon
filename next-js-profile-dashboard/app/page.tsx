"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Sidebar from "@/components/sidebar"
import ProfilePreview from "@/components/profile-preview"
import { getLoggedInPhone } from "@/lib/auth"

export default function Home() {
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [userPhone, setUserPhone] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const phone = getLoggedInPhone()
    if (!phone) {
      router.push("/login")
      return
    }
    setUserPhone(phone)
    setIsLoading(false)
  }, [router])

  // Show nothing while checking auth
  if (isLoading || !userPhone) {
    return null
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <div className={`flex-1 transition-all duration-300 ${sidebarOpen ? "ml-64" : "ml-0"}`}>
        <ProfilePreview onMenuClick={() => setSidebarOpen(true)} sidebarOpen={sidebarOpen} />
      </div>
    </div>
  )
}
