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
  pending_requests?: string[]
  denied_requests?: string[]
}

interface EventDashboardProps {
  sidebarOpen: boolean
  onMenuClick: () => void
  userPhone: string
}

export default function EventDashboard({ sidebarOpen, onMenuClick, userPhone }: EventDashboardProps) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<"create" | "find" | "my-events">("find")
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deletingEventId, setDeletingEventId] = useState<string | null>(null)
  const [editingEvent, setEditingEvent] = useState<Event | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [events, setEvents] = useState<Event[]>([])
  const [userEvents, setUserEvents] = useState<Event[]>([])
  const [joinedEvents, setJoinedEvents] = useState<Event[]>([])
  const [userNames, setUserNames] = useState<Record<string, { name: string }>>({})
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Collect all phone numbers from user events for lookup
  const collectPhoneNumbers = useCallback((events: Event[]): string[] => {
    const phones = new Set<string>()
    for (const event of events) {
      for (const phone of event.participants || []) {
        phones.add(phone)
      }
      for (const phone of event.pending_requests || []) {
        phones.add(phone)
      }
    }
    return Array.from(phones)
  }, [])

  // Fetch user names for all participants and pending requests
  const fetchUserNames = useCallback(async (phones: string[]) => {
    if (phones.length === 0) return
    try {
      const res = await fetch('/api/users/lookup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phones })
      })
      if (res.ok) {
        const data = await res.json()
        setUserNames(data)
      }
    } catch (err) {
      console.error('Failed to fetch user names:', err)
    }
  }, [])

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
      const joined = data.filter(e => e.host_phone !== userPhone && e.participants?.includes(userPhone))
      setUserEvents(mine)
      setEvents(others)
      setJoinedEvents(joined)

      // Fetch user names for participants and pending requests in user's events
      const phones = collectPhoneNumbers(mine)
      await fetchUserNames(phones)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }, [userPhone, collectPhoneNumbers, fetchUserNames])

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

  const handleDeleteClick = (eventId: string) => {
    setDeletingEventId(eventId)
    setShowDeleteConfirm(true)
  }

  const handleConfirmDelete = async () => {
    if (!deletingEventId) return
    setError(null)
    try {
      const res = await fetch(`/api/events/${deletingEventId}`, {
        method: 'DELETE'
      })
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.error || 'Failed to delete event')
      }
      await fetchEvents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete event')
    } finally {
      setShowDeleteConfirm(false)
      setDeletingEventId(null)
    }
  }

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false)
    setDeletingEventId(null)
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
    setSuccessMessage(null)
    try {
      const res = await fetch(`/api/events/${eventId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: userPhone })
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || 'Failed to join event')
      }
      // Handle pending request response (requires host approval per Section 18)
      setSuccessMessage(data.message || 'Request sent!')
      setTimeout(() => setSuccessMessage(null), 5000)
      await fetchEvents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join event')
    }
  }

  const handleApproveRequest = async (eventId: string, phone: string) => {
    setError(null)
    try {
      const res = await fetch(`/api/events/${eventId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone })
      })
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.error || 'Failed to approve request')
      }
      await fetchEvents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve request')
    }
  }

  const handleDenyRequest = async (eventId: string, phone: string) => {
    setError(null)
    try {
      const res = await fetch(`/api/events/${eventId}/deny`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone })
      })
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.error || 'Failed to deny request')
      }
      await fetchEvents()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to deny request')
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
            onClick={() => setActiveTab("my-events")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "my-events" ? "text-black border-b-2 border-black" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            My Events
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

        {successMessage && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {successMessage}
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

        {!loading && activeTab === "my-events" && !showCreateModal && !showEditModal && (
          <div className="space-y-8">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Events I'm Hosting</h2>
              <EventList
                events={userEvents}
                showEditButton
                showDeleteButton
                onEdit={handleEditEvent}
                onDelete={handleDeleteClick}
                onApprove={handleApproveRequest}
                onDeny={handleDenyRequest}
                userNames={userNames}
              />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Joined Events</h2>
              <EventList events={joinedEvents} />
            </div>
          </div>
        )}

        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Event?</h3>
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete this event? This action cannot be undone and all participants will be notified.
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={handleCancelDelete}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmDelete}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
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
