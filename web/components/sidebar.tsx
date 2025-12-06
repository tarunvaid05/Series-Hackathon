"use client"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ChevronLeft, ChevronRight, Edit, MessageCircle, Calendar, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { logout } from "@/lib/auth"

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
  onToggle: () => void
  userName?: string
  userPhone?: string
}

// Hardcoded AI Friend info as requested
const AI_FRIEND = {
  name: "Brady",
  phone: "+16463029478"
}

export default function Sidebar({ isOpen, onToggle, userName, userPhone }: SidebarProps) {
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  // Display name or fallback to phone
  const displayName = userName && !userName.startsWith('+') ? userName : 'User'

  return (
    <aside
      className={`fixed left-0 top-0 h-full w-64 bg-white border-r border-border z-50 transition-transform duration-300 flex flex-col ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 font-semibold">
            {displayName.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <p className="font-semibold text-foreground text-sm">{displayName}</p>
            <Link href="/" className="text-xs text-muted-foreground cursor-pointer hover:underline">
              View profile
            </Link>
          </div>
          <button onClick={onToggle} className="p-1 hover:bg-gray-100 rounded">
            {isOpen ? (
              <ChevronLeft size={20} className="text-foreground" />
            ) : (
              <ChevronRight size={20} className="text-foreground" />
            )}
          </button>
        </div>
      </div>

      {/* Menu Items */}
      <nav className="flex-1 p-4 space-y-1">
        <Link href="/edit-profile">
          <Button variant="ghost" className="w-full justify-start gap-3 text-foreground hover:bg-gray-100">
            <Edit size={18} />
            Edit profile
          </Button>
        </Link>

        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-foreground hover:bg-gray-100"
          onClick={() => {
            // Open SMS to AI friend number
            window.location.href = `sms:${AI_FRIEND.phone}`
          }}
        >
          <MessageCircle size={18} />
          Message your AI friend
        </Button>

        <Link href="/events">
          <Button variant="ghost" className="w-full justify-start gap-3 text-foreground hover:bg-gray-100">
            <Calendar size={18} />
            Event Manager
          </Button>
        </Link>

        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-red-500 hover:bg-red-50 hover:text-red-600"
          onClick={handleLogout}
        >
          <LogOut size={18} />
          Sign out
        </Button>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="font-medium">AI FRIEND</span>
          <span>{AI_FRIEND.name}</span>
          <span className="text-blue-500">{AI_FRIEND.phone}</span>
        </div>
      </div>
    </aside>
  )
}
