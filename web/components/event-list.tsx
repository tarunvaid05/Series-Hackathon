"use client"

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
  showJoinButton?: boolean // Added showJoinButton
  onEdit?: (eventId: string) => void
  onDelete?: (eventId: string) => void
  onJoin?: (eventId: string) => void // Added onJoin
}

export default function EventList({
  events,
  showEditButton,
  showDeleteButton,
  showJoinButton,
  onEdit,
  onDelete,
  onJoin,
}: EventListProps) {
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
        return (
        <div key={event.id} className="py-4 flex items-center justify-between border-b border-gray-100 last:border-b-0">
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
          </div>
        </div>
        )
      })}
    </div>
  )
}
