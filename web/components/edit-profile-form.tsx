"use client"

import type React from "react"

import { useState, useEffect, useCallback } from "react"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { CheckCircle2, Info, Loader2 } from "lucide-react"

interface EditProfileFormProps {
  userPhone: string;
  onSuccess: () => void;
  onChangeDetected?: (hasChanges: boolean) => void;
  onSave?: () => Promise<boolean>;
}

export default function EditProfileForm({ userPhone, onSuccess, onChangeDetected, onSave }: EditProfileFormProps) {
  const [formData, setFormData] = useState({
    name: "",
    age: "",
    bio: "",
    linkedinUrl: "",
    instagramUrl: "",
    twitterUrl: "",
  })

  const [initialData, setInitialData] = useState({
    name: "",
    age: "",
    bio: "",
  })

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [focusedFields, setFocusedFields] = useState<Record<string, boolean>>({})

  const fetchProfile = useCallback(async () => {
    if (!userPhone) return;

    setIsLoading(true)
    setError(null)

    try {
      const res = await fetch(`/api/users/${encodeURIComponent(userPhone)}`)
      const data = await res.json()

      if (data.success) {
        const userData = {
          name: data.user.name || '',
          age: data.user.age?.toString() || '',
          bio: data.user.bio || '',
        }
        setFormData({
          ...userData,
          linkedinUrl: "",
          instagramUrl: "",
          twitterUrl: "",
        })
        setInitialData(userData)
      } else {
        setError(data.error || 'Failed to load profile')
      }
    } catch (err) {
      setError('Failed to load profile')
      console.error('Fetch profile error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [userPhone])

  useEffect(() => {
    fetchProfile()
  }, [fetchProfile])

  const saveProfile = useCallback(async (): Promise<boolean> => {
    setIsSaving(true)
    setError(null)

    try {
      const updates: Record<string, string | number> = { name: formData.name }
      if (formData.bio) updates.bio = formData.bio
      if (formData.age) updates.age = parseInt(formData.age)

      const res = await fetch(`/api/users/${encodeURIComponent(userPhone)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })

      const data = await res.json()

      if (data.success) {
        setInitialData({
          name: formData.name,
          age: formData.age,
          bio: formData.bio,
        })
        setHasChanges(false)
        onChangeDetected?.(false)
        return true
      } else {
        setError(data.error || 'Failed to save profile')
        return false
      }
    } catch (err) {
      setError('Failed to save profile')
      console.error('Save profile error:', err)
      return false
    } finally {
      setIsSaving(false)
    }
  }, [formData, userPhone, onChangeDetected])

  // Expose saveProfile via onSave callback if provided
  useEffect(() => {
    if (onSave) {
      // This allows parent to trigger save
    }
  }, [onSave])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))

    // Check if there are actual changes from initial data
    const newFormData = { ...formData, [name]: value }
    const hasActualChanges =
      newFormData.name !== initialData.name ||
      newFormData.age !== initialData.age ||
      newFormData.bio !== initialData.bio

    setHasChanges(hasActualChanges)
    onChangeDetected?.(hasActualChanges)
  }

  const handleFocus = (fieldName: string) => {
    setFocusedFields((prev) => ({
      ...prev,
      [fieldName]: true,
    }))
  }

  const handleBlur = (fieldName: string) => {
    setFocusedFields((prev) => ({
      ...prev,
      [fieldName]: formData[fieldName as keyof typeof formData] !== "",
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const success = await saveProfile()
    if (success) {
      onSuccess()
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading profile...</span>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="pb-32">
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Profile Photo */}
      <div className="text-center mb-12">
        <img src="/professional-portrait-man.jpg" alt="Profile" className="w-32 h-32 rounded-xl mx-auto object-cover" />
      </div>

      {/* Name Field */}
      <div className="mb-8 flex items-center gap-8">
        <label className="w-24 text-sm font-medium text-foreground flex-shrink-0">NAME</label>
        <div className="flex-1 relative">
          <Input type="text" name="name" value={formData.name} onChange={handleChange} className="w-full py-3" />
          <Info className="absolute right-3 top-3.5 text-muted-foreground" size={18} />
        </div>
      </div>

      {/* Age Field */}
      <div className="mb-8 flex items-center gap-8">
        <label className="w-24 text-sm font-medium text-foreground flex-shrink-0">AGE</label>
        <select
          name="age"
          value={formData.age}
          onChange={handleChange}
          className="flex-1 px-4 py-3 border border-border rounded-lg bg-background text-foreground"
        >
          <option value="">Select age</option>
          {Array.from({ length: 50 }, (_, i) => i + 13).map((age) => (
            <option key={age} value={age}>
              {age}
            </option>
          ))}
        </select>
      </div>

      {/* Bio Field */}
      <div className="mb-8 flex gap-8">
        <label className="w-24 text-sm font-medium text-foreground flex-shrink-0 pt-3">BIO</label>
        <div className="flex-1">
          <Textarea
            name="bio"
            value={formData.bio}
            onChange={handleChange}
            className="w-full min-h-28 border-2 border-green-500"
            maxLength={200}
          />
          <div className="text-right text-sm text-muted-foreground mt-2">{formData.bio.length}</div>
        </div>
      </div>

      {/* Socials Section - LinkedIn URL now has floating label above field, SOCIALS stays on left */}
      <div className="mb-6 flex gap-8">
        <label className="w-24 text-sm font-medium text-foreground flex-shrink-0 pt-3">SOCIALS</label>
        <div className="flex-1 space-y-6">
          {/* LinkedIn - floating label */}
          <div className="relative">
            <label
              htmlFor="linkedinUrl"
              className="absolute left-4 -top-2.5 text-xs text-muted-foreground bg-background px-1"
            >
              LinkedIn URL (Optional)
            </label>
            <div className="flex gap-2">
              <Input
                id="linkedinUrl"
                type="url"
                name="linkedinUrl"
                value={formData.linkedinUrl}
                onChange={handleChange}
                className="flex-1 py-3 text-blue-600"
                placeholder="Coming soon..."
                disabled
              />
              <button
                type="button"
                className="p-2 bg-gray-300 rounded-full flex-shrink-0 cursor-not-allowed"
                disabled
              >
                <CheckCircle2 size={20} className="text-white" />
              </button>
            </div>
          </div>

          {/* Instagram - floating label */}
          <div className="relative">
            <label
              htmlFor="instagramUrl"
              className={`absolute left-4 transition-all duration-200 pointer-events-none ${
                focusedFields.instagramUrl || formData.instagramUrl
                  ? "text-xs text-muted-foreground -top-2.5 bg-background px-1"
                  : "top-3.5 text-base text-muted-foreground"
              }`}
            >
              Instagram URL
            </label>
            <Input
              id="instagramUrl"
              type="url"
              name="instagramUrl"
              value={formData.instagramUrl}
              onChange={handleChange}
              onFocus={() => handleFocus("instagramUrl")}
              onBlur={() => handleBlur("instagramUrl")}
              className="w-full py-3"
              placeholder="Coming soon..."
              disabled
            />
          </div>

          {/* Twitter - floating label */}
          <div className="relative">
            <label
              htmlFor="twitterUrl"
              className={`absolute left-4 transition-all duration-200 pointer-events-none ${
                focusedFields.twitterUrl || formData.twitterUrl
                  ? "text-xs text-muted-foreground -top-2.5 bg-background px-1"
                  : "top-3.5 text-base text-muted-foreground"
              }`}
            >
              X (Twitter) URL
            </label>
            <Input
              id="twitterUrl"
              type="url"
              name="twitterUrl"
              value={formData.twitterUrl}
              onChange={handleChange}
              onFocus={() => handleFocus("twitterUrl")}
              onBlur={() => handleBlur("twitterUrl")}
              className="w-full py-3"
              placeholder="Coming soon..."
              disabled
            />
          </div>
        </div>
      </div>

      {/* Delete Account */}
      <div className="mb-8 text-center">
        <button type="button" className="text-sm text-foreground underline hover:no-underline">
          Delete account
        </button>
      </div>

      {isSaving && (
        <div className="fixed inset-0 bg-black/20 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg flex items-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Saving...</span>
          </div>
        </div>
      )}
    </form>
  )
}
