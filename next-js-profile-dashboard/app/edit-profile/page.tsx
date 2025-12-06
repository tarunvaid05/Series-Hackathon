"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Menu, Loader2 } from "lucide-react"
import EditProfileForm from "@/components/edit-profile-form"
import Sidebar from "@/components/sidebar"
import { getLoggedInPhone } from "@/lib/auth"

export default function EditProfilePage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const router = useRouter()
  const [hasChanges, setHasChanges] = useState(false)
  const [userPhone, setUserPhone] = useState<string | null>(null)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)

  useEffect(() => {
    const phone = getLoggedInPhone()
    if (!phone) {
      router.push('/login')
    } else {
      setUserPhone(phone)
    }
    setIsCheckingAuth(false)
  }, [router])

  if (isCheckingAuth || !userPhone) {
    return (
      <div className="flex h-screen bg-background items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <div
        className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 ${sidebarOpen ? "ml-64" : "ml-0"}`}
      >
        {!sidebarOpen && (
          <div className="absolute top-6 left-6 z-10">
            <button onClick={() => setSidebarOpen(true)} className="p-2 hover:bg-white rounded-lg transition-colors">
              <Menu size={24} className="text-foreground" />
            </button>
          </div>
        )}

        <div className="flex-1 overflow-auto">
          <div className="max-w-2xl mx-auto py-8 px-4">
            <h1 className="text-lg font-medium text-foreground mb-8 text-center">Edit Profile</h1>
            <EditProfileForm
              userPhone={userPhone}
              onSuccess={() => router.push("/")}
              onChangeDetected={setHasChanges}
            />
          </div>
        </div>

        <div className="border-t border-border bg-background px-4 py-4 md:px-6">
          <div className="max-w-2xl mx-auto flex items-center justify-between">
            <div>
              <p className="font-semibold text-foreground">Complete your profile</p>
              <p className="text-sm text-muted-foreground">80% complete</p>
            </div>
            <button
              type="submit"
              disabled={!hasChanges}
              onClick={() => {
                const form = document.querySelector("form")
                if (form) form.requestSubmit()
              }}
              className={`px-8 py-2 rounded-full font-semibold transition-colors ${
                hasChanges ? "bg-gray-700 hover:bg-gray-800 text-white" : "bg-gray-300 text-gray-500 cursor-not-allowed"
              }`}
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
