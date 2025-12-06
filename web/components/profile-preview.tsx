"use client"

import { useEffect, useState } from "react"
import ProfileCard from "./profile-card"
import { Menu } from "lucide-react"
import { getLoggedInPhone } from "@/lib/auth"

interface UserProfile {
  name: string
  age?: number
  bio?: string
  image?: string
}

export default function ProfilePreview({
  onMenuClick,
  sidebarOpen,
}: { onMenuClick: () => void; sidebarOpen: boolean }) {
  const [showAnimation, setShowAnimation] = useState(false)
  const [selectedProfile, setSelectedProfile] = useState<"me" | "friend" | null>(null)
  const [currentUser, setCurrentUser] = useState<UserProfile>({
    name: "User",
    age: undefined,
    bio: "",
    image: "/professional-portrait-man.jpg",
  })

  useEffect(() => {
    const timer = setTimeout(() => setShowAnimation(true), 300)
    return () => clearTimeout(timer)
  }, [])

  // Fetch user profile from API
  useEffect(() => {
    const phone = getLoggedInPhone()
    if (!phone) return

    fetch(`/api/users/${encodeURIComponent(phone)}`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.user) {
          setCurrentUser({
            name: data.user.name && !data.user.name.startsWith('+') ? data.user.name : 'User',
            age: data.user.age,
            bio: data.user.bio || "",
            image: data.user.image || "/professional-portrait-man.jpg",
          })
        }
      })
      .catch(() => {})
  }, [])

  const aiFriend = {
    name: "Brady",
    age: 22,
    bio: "AI Enthusiast & Developer",
    image: "/cartoon-character-ai-assistant.jpg",
    linkedinUrl: "https://www.linkedin.com/in/brady",
  }

  return (
    <div className="relative w-full h-full bg-white">
      {/* Header with menu and centered title */}
      <div className="absolute top-6 left-0 right-0 flex items-center justify-center px-6">
        {!sidebarOpen && (
          <button onClick={onMenuClick} className="absolute left-6 p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Menu size={24} className="text-foreground" />
          </button>
        )}
        <h1 className="text-lg font-medium text-foreground">Profile Preview</h1>
      </div>

      {/* Profile Card on Left with gray border */}
      <div
        className={`absolute left-8 lg:left-12 top-1/2 transform -translate-y-1/2 transition-all duration-700 ${
          showAnimation ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-12"
        }`}
      >
        <div className="border-8 border-gray-200 rounded-3xl">
          <ProfileCard
            profile={currentUser}
            isSelected={selectedProfile === "me"}
            onClick={() => setSelectedProfile("me")}
            showCloseButton={selectedProfile === "me"}
            onClose={() => setSelectedProfile(null)}
          />
        </div>
      </div>

      {/* Center Icons */}
      <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 flex items-center gap-8">
        {/* Main user icon with animation */}
        <div
          className={`transition-all duration-700 ${showAnimation ? "opacity-100 scale-100" : "opacity-0 scale-50"}`}
        >
          <button
            onClick={() => setSelectedProfile("me")}
            className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-400 to-cyan-500 flex items-center justify-center cursor-pointer hover:scale-110 transition-transform border-4 border-white shadow-lg"
          >
            <img src="/professional-portrait-man.jpg" alt="User" className="w-20 h-20 rounded-full object-cover" />
          </button>
        </div>

        {/* AI Friend icon with animation */}
        <div
          className={`transition-all duration-1000 delay-300 ${
            showAnimation ? "opacity-100 translate-x-0" : "opacity-0 translate-x-8"
          }`}
        >
          <button
            onClick={() => setSelectedProfile("friend")}
            className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-400 to-purple-500 flex items-center justify-center cursor-pointer hover:scale-110 transition-transform border-4 border-white shadow-lg"
          >
            <img
              src="/cartoon-character-ai-assistant.jpg"
              alt="AI Friend"
              className="w-14 h-14 rounded-full object-cover"
            />
          </button>
        </div>
      </div>

      {/* AI Friend Card (when friend is selected) */}
      {selectedProfile === "friend" && (
        <div className={`absolute right-8 lg:right-12 top-1/2 transform -translate-y-1/2 transition-all duration-500`}>
          <div className="border-8 border-gray-200 rounded-3xl">
            <ProfileCard
              profile={aiFriend}
              isSelected={selectedProfile === "friend"}
              onClick={() => {}}
              showCloseButton={true}
              onClose={() => setSelectedProfile(null)}
            />
          </div>
        </div>
      )}
    </div>
  )
}
