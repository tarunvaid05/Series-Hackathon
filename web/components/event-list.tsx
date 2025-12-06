"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"

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

function formatDatetime(datetime: string): { date: string; time: string } {
  if (!datetime) return { date: "", time: "" }
  const parts = datetime.split(/[T ]/)
  const datePart = parts[0] || ""
  const timePart = parts[1]?.substring(0, 5) || ""

  // Convert date from YYYY-MM-DD to MM/DD/YYYY for display
  const [year, month, day] = datePart.split("-")
  const formattedDate = year && month && day ? `${month}/${day}/${year}` : datePart

  // Convert time from 24h to 12h format
  let formattedTime = timePart
  if (timePart) {
    const [hours, minutes] = timePart.split(":")
    const h = parseInt(hours, 10)
    const period = h >= 12 ? "PM" : "AM"
    const h12 = h % 12 || 12
    formattedTime = `${h12}:${minutes} ${period}`
  }

  return { date: formattedDate, time: formattedTime }
}

function formatCapacity(capacity: number | null, participantCount: number): string {
  if (capacity === null) {
    return `${participantCount} attending (unlimited)`
  }
  return `${participantCount}/${capacity} spots`
}

interface EventListProps {
  events: Event[]
  showEditButton?: boolean
  showDeleteButton?: boolean
  showJoinButton?: boolean
  onEdit?: (eventId: string) => void
  onDelete?: (eventId: string) => void
  onJoin?: (eventId: string) => void
  onApprove?: (eventId: string, phone: string) => void
  onDeny?: (eventId: string, phone: string) => void
  userNames?: Record<string, { name: string }>
}

export default function EventList({
  events,
  showEditButton,
  showDeleteButton,
  showJoinButton,
  onEdit,
  onDelete,
  onJoin,
  onApprove,
  onDeny,
  userNames = {},
}: EventListProps) {
  const [expandedEventIds, setExpandedEventIds] = useState<Set<string>>(new Set())

  const toggleExpanded = (eventId: string) => {
    setExpandedEventIds(prev => {
      const next = new Set(prev)
      if (next.has(eventId)) {
        next.delete(eventId)
      } else {
        next.add(eventId)
      }
      return next
    })
  }

  const getUserName = (phone: string): string => {
    return userNames[phone]?.name || "Unknown"
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No events found</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {events.map((event) => {
        const { date, time } = formatDatetime(event.datetime)
        const capacityDisplay = formatCapacity(event.capacity, event.participants.length)
        const isExpanded = expandedEventIds.has(event.id)
        const showAttendeesSection = showEditButton // Only show in My Events tab
        const pendingRequests = event.pending_requests || []
        const participants = event.participants || []

        return (
          <div key={event.id} className="py-4 border-b border-gray-100 last:border-b-0">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">{event.title}</h3>
                <div className="flex flex-wrap gap-x-6 gap-y-1 mt-1 text-sm text-muted-foreground">
                  <span>{date}</span>
                  <span>{time}</span>
                  <span>{event.location}</span>
                  <span>{capacityDisplay}</span>
                </div>
              </div>
              <div className="ml-4 flex gap-2">
                {showJoinButton && (
                  <button
                    onClick={() => onJoin?.(event.id)}
                    className="bg-black hover:bg-gray-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Join
                  </button>
                )}
                {showEditButton && onEdit && (
                  <button
                    onClick={() => onEdit(event.id)}
                    className="bg-black hover:bg-gray-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Edit
                  </button>
                )}
                {showDeleteButton && onDelete && (
                  <button
                    onClick={() => onDelete(event.id)}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Delete
                  </button>
                )}
                {showAttendeesSection && (
                  <button
                    onClick={() => toggleExpanded(event.id)}
                    className="flex items-center gap-1 text-gray-600 hover:text-gray-800 px-3 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-gray-100"
                  >
                    {isExpanded ? (
                      <>
                        <ChevronUp size={16} />
                        Hide
                      </>
                    ) : (
                      <>
                        <ChevronDown size={16} />
                        Attendees
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Expandable Attendees Section */}
            {showAttendeesSection && isExpanded && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                {/* Confirmed Attendees */}
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">
                    Attendees ({participants.length}):
                  </h4>
                  {participants.length > 0 ? (
                    <ul className="space-y-1">
                      {participants.map((phone) => (
                        <li key={phone} className="text-sm text-gray-600 flex items-center gap-2">
                          <span className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
                          {getUserName(phone)} ({phone})
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-gray-500 italic">No attendees yet</p>
                  )}
                </div>

                {/* Pending Requests */}
                {pendingRequests.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">
                      Pending Requests ({pendingRequests.length}):
                    </h4>
                    <ul className="space-y-2">
                      {pendingRequests.map((phone) => (
                        <li key={phone} className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 flex items-center gap-2">
                            <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full" />
                            {getUserName(phone)} ({phone})
                          </span>
                          <div className="flex gap-2">
                            <button
                              onClick={() => onApprove?.(event.id, phone)}
                              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => onDeny?.(event.id, phone)}
                              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs font-medium transition-colors"
                            >
                              Deny
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {participants.length === 0 && pendingRequests.length === 0 && (
                  <p className="text-sm text-gray-500 italic">No attendees or pending requests</p>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
