"use client"

import { useState } from "react"
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
}

export default function EventDashboard({ sidebarOpen, onMenuClick }: EventDashboardProps) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<"create" | "find" | "edit" | "delete">("find")
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingEvent, setEditingEvent] = useState<Event | null>(null)

  const [events, setEvents] = useState<Event[]>([
    {
      id: "1",
      host_phone: "+15551234567",
      title: "Summer Music Festival",
      description: "Join us for an amazing summer music festival!",
      datetime: "2025-12-06 12:30",
      location: "Central Park, New York",
      capacity: 100,
      participants: ["+15559876543", "+15551112222"],
      status: "open",
    },
    {
      id: "2",
      host_phone: "+15559999999",
      title: "Tech Conference 2025",
      description: "Latest in tech and innovation",
      datetime: "2025-12-15 09:00",
      location: "San Francisco Convention Center",
      capacity: 500,
      participants: ["+15553334444"],
      status: "open",
    },
  ])
  const [userEvents, setUserEvents] = useState<Event[]>([
    {
      id: "3",
      host_phone: "+15550000000",
      title: "Hackathon Networking",
      description: "Connect with fellow hackers",
      datetime: "2025-12-20 18:00",
      location: "Downtown Tech Hub",
      capacity: 50,
      participants: [],
      status: "open",
    },
  ])

  const handleCreateEvent = (eventData: Partial<Event>) => {
    const newEvent: Event = {
      id: Date.now().toString(),
      host_phone: "+15550000000", // Placeholder - would come from user session
      title: eventData.title || "",
      description: eventData.description || "",
      datetime: eventData.datetime || "",
      location: eventData.location || "",
      capacity: eventData.capacity ?? null,
      participants: [],
      status: "open",
    }
    setUserEvents([...userEvents, newEvent])
    setShowCreateModal(false)
    setActiveTab("find")
  }

  const handleDeleteEvent = (eventId: string) => {
    setUserEvents(userEvents.filter((e) => e.id !== eventId))
  }

  const handleEditEvent = (eventId: string) => {
    const eventToEdit = userEvents.find((e) => e.id === eventId)
    if (eventToEdit) {
      setEditingEvent(eventToEdit)
      setShowEditModal(true)
    }
  }

  const handleSaveEdit = (eventData: Partial<Event>) => {
    if (editingEvent) {
      setUserEvents(userEvents.map((e) => (e.id === editingEvent.id ? { ...e, ...eventData, id: e.id } : e)))
      setShowEditModal(false)
      setEditingEvent(null)
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

        {activeTab === "find" && !showCreateModal && !showEditModal && (
          <div>
            <EventList events={events} showJoinButton />
          </div>
        )}

        {activeTab === "edit" && !showCreateModal && !showEditModal && (
          <div>
            <EventList events={userEvents} showEditButton onEdit={handleEditEvent} />
          </div>
        )}

        {activeTab === "delete" && !showCreateModal && !showEditModal && (
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
