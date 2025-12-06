"use client"

import { useState } from "react"
import { Menu } from "lucide-react"
import Sidebar from "@/components/sidebar"
import { Button } from "@/components/ui/button"

export default function MessagesPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen bg-background">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 overflow-auto">
        <div className="absolute top-6 left-6 z-10 md:hidden">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-white rounded-lg transition-colors"
          >
            <Menu size={24} className="text-foreground" />
          </button>
        </div>

        <div className="max-w-4xl mx-auto py-8 px-4">
          <h1 className="text-3xl font-bold text-foreground mb-8 text-center">Message Your AI Friend</h1>

          <div className="bg-white rounded-lg p-8 border border-border">
            <div className="text-center py-12">
              <p className="text-muted-foreground text-lg">Chat feature coming soon! 💬</p>
              <Button
                className="mt-4 bg-purple-600 hover:bg-purple-700 text-white"
                onClick={() => window.history.back()}
              >
                Go Back
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
