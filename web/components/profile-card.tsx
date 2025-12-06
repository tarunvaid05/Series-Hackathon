"use client"

import { X, Linkedin } from "lucide-react"

interface Profile {
  name: string
  age: number
  bio: string
  image: string
  linkedinUrl?: string
}

interface ProfileCardProps {
  profile: Profile
  isSelected: boolean
  onClick: () => void
  showCloseButton: boolean
  onClose: () => void
}

export default function ProfileCard({ profile, isSelected, onClick, showCloseButton, onClose }: ProfileCardProps) {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-2xl p-6 shadow-xl cursor-pointer transition-all duration-300 ${
        isSelected ? "w-96" : "w-80"
      }`}
    >
      {showCloseButton && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onClose()
          }}
          className="absolute top-4 right-4 p-1 hover:bg-gray-100 rounded-lg"
        >
          <X size={20} className="text-gray-400" />
        </button>
      )}

      <h2 className="text-2xl font-bold text-foreground mb-4">{profile.name}</h2>

      {/* Profile Image */}
      <div className="relative mb-4">
        <img
          src={profile.image || "/placeholder.svg"}
          alt={profile.name}
          className="w-full h-48 object-cover rounded-xl"
        />
        <div className="absolute bottom-3 left-3 bg-white bg-opacity-80 px-3 py-1 rounded-full text-sm font-semibold text-foreground">
          👤 {profile.age}
        </div>
      </div>

      {/* Bio Section */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Bio</h3>
        <p className="text-foreground text-sm leading-relaxed">{profile.bio}</p>
      </div>

      {/* LinkedIn Link */}
      {profile.linkedinUrl && (
        <div className="flex items-center gap-2 text-blue-600 hover:text-blue-700">
          <Linkedin size={20} />
          <a href={profile.linkedinUrl} target="_blank" rel="noopener noreferrer" className="text-sm font-medium">
            LinkedIn
          </a>
        </div>
      )}
    </div>
  )
}
