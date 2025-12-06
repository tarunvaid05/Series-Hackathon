"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Sidebar from "@/components/sidebar"
import ProfilePreview from "@/components/profile-preview"
import { getLoggedInPhone } from "@/lib/auth"

interface UserProfile {
  name: string
  bio?: string
  age?: number
  image?: string
}

export default function Home() {
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [userPhone, setUserPhone] = useState<string | null>(null)
  const [userName, setUserName] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const phone = getLoggedInPhone()
    if (!phone) {
      router.push("/login")
      return
    }
    setUserPhone(phone)

    // Fetch user profile
    fetch(`/api/users/${encodeURIComponent(phone)}`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.user) {
          setUserName(data.user.name || '')
        }
        setIsLoading(false)
      })
      .catch(() => {
        setIsLoading(false)
      })
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
        userName={userName}
        userPhone={userPhone}
      />
      <div className={`flex-1 transition-all duration-300 ${sidebarOpen ? "ml-64" : "ml-0"}`}>
        <ProfilePreview onMenuClick={() => setSidebarOpen(true)} sidebarOpen={sidebarOpen} />
      </div>
    </div>
  )
}
