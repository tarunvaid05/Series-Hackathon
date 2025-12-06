"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Menu } from "lucide-react"
import CreateEventModal from "./create-event-modal"
import EventList from "./event-list"

interface Event {
  id: string
  host_phone: string
  title: string
  description: string
  datetime: string
  location: string
  capacity: number | null
  participants: string[]
  status: 'open' | 'closed'
}

interface EventDashboardProps {
  sidebarOpen: boolean
  onMenuClick: () => void
  userPhone: string
}

export default function EventDashboard({ sidebarOpen, onMenuClick, userPhone }: EventDashboardProps) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<"create" | "find" | "edit" | "delete">("find")
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingEvent, setEditingEvent] = useState<Event | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [events, setEvents] = useState<Event[]>([])
  const [userEvents, setUserEvents] = useState<Event[]>([])

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/events')
      if (!res.ok) {
        throw new Error('Failed to fetch events')
      }
      const data: Event[] = await res.json()
      const mine = data.filter(e => e.host_phone === userPhone)
      const others = data.filter(e => e.host_phone !== userPhone)
      setUserEvents(mine)
      setEvents(others)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }, [userPhone])

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  const handleCreateEvent = async (eventData: Partial<Event>) => {
    setError(null)
    try {
      const res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...eventData,
          host_phone: userPhone
        })
      })
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.error || 'Failed to create event')
      }
      await fetchEvents()
      setShowCreateModal(false)
      setActiveTab("find")
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create event')
    }
  }

  const handleDeleteEvent = async (eventId: string) => {
    setError(null)
    try {
      const res = await fetch(`/api/events/${eventId}`, {
        method: 'DELETE'
      })
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.error || 'Failed to delete event')
      }
      await fetchEvents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete event')
    }
  }

  const handleEditEvent = (eventId: string) => {
    const eventToEdit = userEvents.find((e) => e.id === eventId)
    if (eventToEdit) {
      setEditingEvent(eventToEdit)
      setShowEditModal(true)
    }
  }

  const handleSaveEdit = async (eventData: Partial<Event>) => {
    if (!editingEvent) return
    setError(null)
    try {
      const res = await fetch(`/api/events/${editingEvent.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventData)
      })
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.error || 'Failed to update event')
      }
      await fetchEvents()
      setShowEditModal(false)
      setEditingEvent(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update event')
    }
  }

  const handleJoinEvent = async (eventId: string) => {
    setError(null)
    try {
      const res = await fetch(`/api/events/${eventId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: userPhone })
      })
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.error || 'Failed to join event')
      }
      await fetchEvents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join event')
    }
  }

  const handleCancelCreate = () => {
    setShowCreateModal(false)
    setActiveTab("find")
  }

  return (
    <div className="w-full min-h-screen bg-white">
      {/* Header */}
      <div className="px-8 pt-8">
        <div className="relative flex items-center justify-center mb-6">
          {!sidebarOpen && (
            <button
              onClick={onMenuClick}
              className="absolute left-0 p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Menu size={24} className="text-foreground" />
            </button>
          )}
          <h1 className="text-lg font-medium text-foreground">Event Dashboard</h1>
        </div>

        {/* Tab Navigation - Full width tabs, evenly spaced */}
        <div className="flex border-b border-gray-200 mb-8">
          <button
            onClick={() => {
              setActiveTab("create")
              setShowCreateModal(true)
            }}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "create" ? "text-black border-b-2 border-black" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Create Event
          </button>
          <button
            onClick={() => setActiveTab("find")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "find" ? "text-black border-b-2 border-black" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Find Events
          </button>
          <button
            onClick={() => setActiveTab("edit")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "edit" ? "text-black border-b-2 border-black" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Edit Your Events
          </button>
          <button
            onClick={() => setActiveTab("delete")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "delete" ? "text-black border-b-2 border-black" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Delete Your Events
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-8 pb-32">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {showCreateModal && <CreateEventModal onSubmit={handleCreateEvent} onClose={handleCancelCreate} />}

        {showEditModal && editingEvent && (
          <CreateEventModal
            onSubmit={handleSaveEdit}
            onClose={() => {
              setShowEditModal(false)
              setEditingEvent(null)
            }}
            initialData={editingEvent}
            isEditing={true}
          />
        )}

        {loading && !showCreateModal && !showEditModal && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading events...</p>
          </div>
        )}

        {!loading && activeTab === "find" && !showCreateModal && !showEditModal && (
          <div>
            <EventList events={events} showJoinButton onJoin={handleJoinEvent} />
          </div>
        )}

        {!loading && activeTab === "edit" && !showCreateModal && !showEditModal && (
          <div>
            <EventList events={userEvents} showEditButton onEdit={handleEditEvent} />
          </div>
        )}

        {!loading && activeTab === "delete" && !showCreateModal && !showEditModal && (
          <div>
            <EventList events={userEvents} showDeleteButton onDelete={handleDeleteEvent} />
          </div>
        )}
      </div>

      <div className="fixed bottom-8 right-8 z-10">
        <button
          onClick={() => router.push("/")}
          className="bg-black hover:bg-gray-800 text-white px-6 py-3 rounded-lg text-sm font-medium transition-colors"
        >
          Back to Profile Preview
        </button>
      </div>
    </div>
  )
}
