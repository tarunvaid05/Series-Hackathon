"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"

interface CreateEventModalProps {
  onSubmit: (data: any) => void
  onClose: () => void
  initialData?: {
    title?: string
    datetime?: string
    location?: string
    capacity?: number | null
    description?: string
  }
  isEditing?: boolean
}

function convertDisplayDateToInputFormat(displayDate: string): string {
  if (!displayDate) return ""
  // Check if already in YYYY-MM-DD format
  if (displayDate.match(/^\d{4}-\d{2}-\d{2}$/)) return displayDate

  // Convert from MM/DD/YYYY to YYYY-MM-DD
  const parts = displayDate.split("/")
  if (parts.length === 3) {
    const [month, day, year] = parts
    return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`
  }
  return displayDate
}

function convertDisplayTimeToInputFormat(displayTime: string): string {
  if (!displayTime) return ""
  // Check if already in HH:MM format
  if (displayTime.match(/^\d{2}:\d{2}$/)) return displayTime

  // Convert from 12-hour to 24-hour format
  const match = displayTime.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i)
  if (match) {
    let hours = Number.parseInt(match[1], 10)
    const minutes = match[2]
    const period = match[3].toUpperCase()

    if (period === "PM" && hours !== 12) {
      hours += 12
    } else if (period === "AM" && hours === 12) {
      hours = 0
    }

    return `${hours.toString().padStart(2, "0")}:${minutes}`
  }
  return displayTime
}

function parseDatetime(datetime: string): { date: string; time: string } {
  if (!datetime) return { date: "", time: "" }
  // Handle ISO format or "YYYY-MM-DD HH:MM" format
  const parts = datetime.split(/[T ]/)
  return {
    date: parts[0] || "",
    time: parts[1]?.substring(0, 5) || "",
  }
}

function getDefaultDate(): string {
  const today = new Date()
  const year = today.getFullYear()
  const month = (today.getMonth() + 1).toString().padStart(2, "0")
  const day = today.getDate().toString().padStart(2, "0")
  return `${year}-${month}-${day}`
}

function getDefaultTime(): string {
  const now = new Date()
  const hours = now.getHours().toString().padStart(2, "0")
  const minutes = now.getMinutes().toString().padStart(2, "0")
  return `${hours}:${minutes}`
}

export default function CreateEventModal({ onSubmit, onClose, initialData, isEditing }: CreateEventModalProps) {
  const [formData, setFormData] = useState({
    title: "",
    date: getDefaultDate(),
    time: getDefaultTime(),
    location: "",
    capacity: "",
    description: "",
  })

  useEffect(() => {
    if (initialData) {
      const { date, time } = parseDatetime(initialData.datetime || "")
      setFormData({
        title: initialData.title || "",
        date: convertDisplayDateToInputFormat(date) || getDefaultDate(),
        time: convertDisplayTimeToInputFormat(time) || getDefaultTime(),
        location: initialData.location || "",
        capacity: initialData.capacity?.toString() || "",
        description: initialData.description || "",
      })
    }
  }, [initialData])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Combine date and time into datetime string
    const datetime = `${formData.date} ${formData.time}`
    const submitData = {
      title: formData.title,
      datetime,
      location: formData.location,
      capacity: formData.capacity ? parseInt(formData.capacity, 10) : null,
      description: formData.description,
    }
    onSubmit(submitData)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold text-foreground mb-6">{isEditing ? "Edit Event" : "Create Event"}</h2>

        {/* Event Title */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-foreground mb-2">Event Title</label>
          <Input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="e.g., Summer Music Festival"
            required
          />
        </div>

        {/* Date and Time */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Date</label>
            <Input type="date" name="date" value={formData.date} onChange={handleChange} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Time</label>
            <Input type="time" name="time" value={formData.time} onChange={handleChange} required />
          </div>
        </div>

        {/* Location */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-foreground mb-2">Location</label>
          <Input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            placeholder="e.g., Central Park, New York"
            required
          />
        </div>

        {/* Capacity */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-foreground mb-2">Capacity (Optional)</label>
          <Input
            type="number"
            name="capacity"
            value={formData.capacity}
            onChange={handleChange}
            placeholder="e.g., 100 (leave empty for unlimited)"
          />
        </div>

        {/* Description */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-foreground mb-2">Event Description</label>
          <Textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Tell us about your event..."
            className="min-h-24"
          />
        </div>

        {/* Buttons */}
        <div className="flex gap-3 justify-end">
          <Button
            type="button"
            onClick={onClose}
            className="px-6 py-2 bg-gray-200 text-foreground rounded-lg font-semibold hover:bg-gray-300"
          >
            Cancel
          </Button>
          <Button type="submit" className="px-6 py-2 bg-black text-white rounded-lg font-semibold hover:bg-gray-800">
            {isEditing ? "Save Changes" : "Create Event"}
          </Button>
        </div>
      </form>
    </div>
  )
}
