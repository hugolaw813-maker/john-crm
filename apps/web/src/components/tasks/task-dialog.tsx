"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import {
  Calendar as CalendarIcon,
  User,
  Link2,
  X,
  Search,
  Check,
  Building2,
  Flag,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  format,
  isToday,
  isTomorrow,
  addDays,
  startOfWeek,
  endOfWeek,
  addWeeks,
} from "date-fns";

// ─── Types ───────────────────────────────────────────────────────────

interface TaskFormData {
  id?: string;
  content: string;
  deadline: Date | null;
  priority: string;
  assigneeIds: string[];
  recordIds: string[];
  linkedRecords?: { id: string; displayName: string; objectSlug: string }[];
  assignees?: { id: string; displayName: string; objectSlug: string }[];
}

interface SearchResult {
  id: string;
  displayName: string;
  subtitle: string;
  objectSlug: string;
  objectName: string;
}

interface TaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: "create" | "edit";
  initialData?: TaskFormData;
  currentUserId?: string;
  /** Pre-link to a specific record when creating from a record page */
  defaultRecordId?: string;
  defaultRecordName?: string;
  defaultRecordSlug?: string;
  onSave: (data: {
    content: string;
    deadline: string | null;
    priority: string;
    recordIds: string[];
    assigneeIds: string[];
  }) => Promise<void>;
  onDelete?: () => Promise<void>;
}

// ─── Component ───────────────────────────────────────────────────────

export function TaskDialog({
  open,
  onOpenChange,
  mode,
  initialData,
  currentUserId,
  defaultRecordId,
  defaultRecordName,
  defaultRecordSlug,
  onSave,
  onDelete,
}: TaskDialogProps) {
  const [content, setContent] = useState("");
  const [deadline, setDeadline] = useState<Date | null>(null);
  const [priority, setPriority] = useState("medium");
  const [assigneeIds, setAssigneeIds] = useState<string[]>([]);
  const [linkedRecords, setLinkedRecords] = useState<
    { id: string; displayName: string; objectSlug: string }[]
  >([]);
  const [createMore, setCreateMore] = useState(false);
  const [saving, setSaving] = useState(false);

  // Pickers open state
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [priorityPickerOpen, setPriorityPickerOpen] = useState(false);
  const [assigneePickerOpen, setAssigneePickerOpen] = useState(false);
  const [recordPickerOpen, setRecordPickerOpen] = useState(false);

  // Data for pickers
  const [assigneeSearch, setAssigneeSearch] = useState("");
  const [recordSearch, setRecordSearch] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [assigneeResults, setAssigneeResults] = useState<SearchResult[]>([]);
  const [assigneeLoading, setAssigneeLoading] = useState(false);

  const contentRef = useRef<HTMLInputElement>(null);
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const datePickerRef = useRef<HTMLDivElement>(null);
  const priorityPickerRef = useRef<HTMLDivElement>(null);
  const assigneePickerRef = useRef<HTMLDivElement>(null);
  const recordPickerRef = useRef<HTMLDivElement>(null);

  // Close pickers on click outside
  useEffect(() => {
    function handleMouseDown(e: MouseEvent) {
      const target = e.target as Node;
      if (datePickerOpen && datePickerRef.current && !datePickerRef.current.contains(target)) {
        setDatePickerOpen(false);
      }
      if (priorityPickerOpen && priorityPickerRef.current && !priorityPickerRef.current.contains(target)) {
        setPriorityPickerOpen(false);
      }
      if (assigneePickerOpen && assigneePickerRef.current && !assigneePickerRef.current.contains(target)) {
        setAssigneePickerOpen(false);
      }
      if (recordPickerOpen && recordPickerRef.current && !recordPickerRef.current.contains(target)) {
        setRecordPickerOpen(false);
      }
    }
    document.addEventListener("mousedown", handleMouseDown);
    return () => document.removeEventListener("mousedown", handleMouseDown);
  }, [datePickerOpen, priorityPickerOpen, assigneePickerOpen, recordPickerOpen]);

  // Initialize form data
  useEffect(() => {
    if (open) {
      if (mode === "edit" && initialData) {
        setContent(initialData.content);
        setDeadline(initialData.deadline);
        setPriority(initialData.priority || "medium");
        setAssigneeIds(initialData.assigneeIds);
        setLinkedRecords(initialData.linkedRecords || []);
      } else {
        setContent("");
        setDeadline(null);
        setPriority("medium");
        setAssigneeIds([]);
        setLinkedRecords(
          defaultRecordId && defaultRecordName
            ? [
                {
                  id: defaultRecordId,
                  displayName: defaultRecordName,
                  objectSlug: defaultRecordSlug || "",
                },
              ]
            : []
        );
      }
      setDatePickerOpen(false);
      setPriorityPickerOpen(false);
      setAssigneePickerOpen(false);
      setRecordPickerOpen(false);
      setAssigneeSearch("");
      setRecordSearch("");
      setSearchResults([]);
      // Focus title input after dialog opens
      setTimeout(() => contentRef.current?.focus(), 100);
    }
  }, [
    open,
    mode,
    initialData,
    currentUserId,
    defaultRecordId,
    defaultRecordName,
    defaultRecordSlug,
  ]);

  // Load browse results (no query)
  const loadBrowseResults = useCallback(async () => {
    setSearchLoading(true);
    try {
      const res = await fetch("/api/v1/records/browse?limit=30");
      if (res.ok) {
        const data = await res.json();
        setSearchResults(
          (data.data || []).map(
            (r: { recordId: string; displayName: string; subtitle?: string; objectSlug: string; objectName: string }) => ({
              id: r.recordId,
              displayName: r.displayName,
              subtitle: r.subtitle || "",
              objectSlug: r.objectSlug,
              objectName: r.objectName,
            })
          )
        );
      }
    } catch {
      // ignore
    } finally {
      setSearchLoading(false);
    }
  }, []);

  const searchPeople = useCallback((query: string, setter: (results: SearchResult[]) => void, setLoadingState: (loading: boolean) => void) => {
    if (searchTimerRef.current !== null) clearTimeout(searchTimerRef.current);
    if (!query.trim()) {
      setLoadingState(true);
      fetch("/api/v1/records/browse?limit=30")
        .then((r) => r.json())
        .then((data) => {
          setter(
            (data.data || [])
              .map((r: { recordId: string; displayName: string; subtitle?: string; objectSlug: string; objectName: string }) => ({
                id: r.recordId,
                displayName: r.displayName,
                subtitle: r.subtitle || "",
                objectSlug: r.objectSlug,
                objectName: r.objectName,
              }))
              .filter((r: SearchResult) => r.objectSlug === "people")
          );
        })
        .catch(() => {})
        .finally(() => setLoadingState(false));
      return;
    }
    setLoadingState(true);
    searchTimerRef.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/v1/search?q=${encodeURIComponent(query)}&limit=10`
        );
        if (res.ok) {
          const data = await res.json();
          setter(
            (data.data || [])
              .filter((r: { type: string; objectSlug?: string }) => r.type === "record" && r.objectSlug === "people")
              .map(
                (r: {
                  id: string;
                  title: string;
                  subtitle: string;
                  objectSlug: string;
                  objectName: string;
                }) => ({
                  id: r.id,
                  displayName: r.title,
                  subtitle: r.subtitle || "",
                  objectSlug: r.objectSlug || "",
                  objectName: r.objectName || "",
                })
              )
          );
        }
      } catch {
        // ignore
      } finally {
        setLoadingState(false);
      }
    }, 300);
  }, []);

  // Search records with debounce
  const searchRecords = useCallback((query: string) => {
    if (searchTimerRef.current !== null) clearTimeout(searchTimerRef.current);
    if (!query.trim()) {
      loadBrowseResults();
      return;
    }
    setSearchLoading(true);
    searchTimerRef.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/v1/search?q=${encodeURIComponent(query)}&limit=10`
        );
        if (res.ok) {
          const data = await res.json();
          setSearchResults(
            (data.data || [])
              .filter((r: { type: string }) => r.type === "record")
              .map(
                (r: {
                  id: string;
                  title: string;
                  subtitle: string;
                  objectSlug: string;
                  objectName: string;
                }) => ({
                  id: r.id,
                  displayName: r.title,
                  subtitle: r.subtitle || "",
                  objectSlug: r.objectSlug || "",
                  objectName: r.objectName || "",
                })
              )
          );
        }
      } catch {
        // ignore
      } finally {
        setSearchLoading(false);
      }
    }, 300);
  }, [loadBrowseResults]);

  async function handleSave() {
    if (!content.trim()) return;
    setSaving(true);
    try {
      await onSave({
        content: content.trim(),
        deadline: deadline ? deadline.toISOString().split("T")[0] : null,
        priority,
        recordIds: linkedRecords.map((r) => r.id),
        assigneeIds,
      });
      if (createMore && mode === "create") {
        setContent("");
        setDeadline(null);
        setPriority("medium");
        setLinkedRecords(
          defaultRecordId && defaultRecordName
            ? [
                {
                  id: defaultRecordId,
                  displayName: defaultRecordName,
                  objectSlug: defaultRecordSlug || "",
                },
              ]
            : []
        );
        setTimeout(() => contentRef.current?.focus(), 50);
      } else {
        onOpenChange(false);
      }
    } finally {
      setSaving(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSave();
    }
  }

  // Date quick options
  function setQuickDate(option: "today" | "tomorrow" | "next_week" | "none") {
    const now = new Date();
    switch (option) {
      case "today":
        setDeadline(now);
        break;
      case "tomorrow":
        setDeadline(addDays(now, 1));
        break;
      case "next_week":
        setDeadline(startOfWeek(addWeeks(now, 1), { weekStartsOn: 1 }));
        break;
      case "none":
        setDeadline(null);
        break;
    }
    setDatePickerOpen(false);
  }

  function getDeadlineLabel(): string {
    if (!deadline) return "No date";
    if (isToday(deadline)) return "Today";
    if (isTomorrow(deadline)) return "Tomorrow";
    return format(deadline, "MMM d");
  }

  function getPriorityLabel(): string {
    if (priority === "high") return "High";
    if (priority === "low") return "Low";
    return "Medium";
  }

  function addRecord(record: SearchResult) {
    if (record.objectSlug !== "people") return;

    if (!linkedRecords.find((r) => r.id === record.id)) {
      setLinkedRecords((prev) => [
        ...prev,
        {
          id: record.id,
          displayName: record.displayName,
          objectSlug: record.objectSlug,
        },
      ]);
    }
    setRecordSearch("");
    setSearchResults([]);
  }

  function removeRecord(recordId: string) {
    setLinkedRecords((prev) => prev.filter((r) => r.id !== recordId));
  }

  function toggleAssignee(recordId: string) {
    setAssigneeIds((prev) =>
      prev.includes(recordId)
        ? prev.filter((id) => id !== recordId)
        : [...prev, recordId]
    );
  }

  const assignedMembers = (initialData?.assignees || [])
    .filter((m) => assigneeIds.includes(m.id))
    .concat(
      assigneeResults
        .filter((m) => assigneeIds.includes(m.id))
        .filter((m) => !(initialData?.assignees || []).some((a) => a.id === m.id))
        .map((m) => ({ id: m.id, displayName: m.displayName, objectSlug: m.objectSlug }))
    );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-md"
        onKeyDown={handleKeyDown}
      >
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Create task" : "Edit task"}
          </DialogTitle>
          <DialogDescription className="sr-only">
            {mode === "create"
              ? "Fill in the details to create a new task"
              : "Edit the task details"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Task content */}
          <Input
            ref={contentRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="What needs to be done?"
            className="text-sm"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                handleSave();
              }
            }}
          />

          {/* Action buttons row */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Date picker */}
            <div className="relative" ref={datePickerRef}>
              <Button
                variant="outline"
                size="sm"
                className={cn(
                  "text-xs gap-1.5",
                  deadline && "text-foreground",
                  !deadline && "text-muted-foreground"
                )}
                onClick={() => {
                  setDatePickerOpen(!datePickerOpen);
                  setPriorityPickerOpen(false);
                  setAssigneePickerOpen(false);
                  setRecordPickerOpen(false);
                }}
              >
                <CalendarIcon className="h-3.5 w-3.5" />
                {getDeadlineLabel()}
              </Button>
              {datePickerOpen && (
                <div className="absolute top-full left-0 z-50 mt-1 rounded-lg border border-border bg-popover shadow-lg">
                  <Calendar
                    mode="single"
                    selected={deadline || undefined}
                    onSelect={(date) => {
                      setDeadline(date || null);
                      setDatePickerOpen(false);
                    }}
                    defaultMonth={deadline || new Date()}
                  />
                  <div className="border-t border-border px-3 pb-3 pt-2 flex flex-wrap gap-1.5">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs h-7"
                      onClick={() => setQuickDate("today")}
                    >
                      Today
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs h-7"
                      onClick={() => setQuickDate("tomorrow")}
                    >
                      Tomorrow
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs h-7"
                      onClick={() => setQuickDate("next_week")}
                    >
                      Next week
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs h-7"
                      onClick={() => setQuickDate("none")}
                    >
                      No date
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Priority picker */}
            <div className="relative" ref={priorityPickerRef}>
              <Button
                variant="outline"
                size="sm"
                className={cn("text-xs gap-1.5", "text-foreground")}
                onClick={() => {
                  setPriorityPickerOpen(!priorityPickerOpen);
                  setDatePickerOpen(false);
                  setAssigneePickerOpen(false);
                  setRecordPickerOpen(false);
                }}
              >
                <Flag className="h-3.5 w-3.5" />
                {getPriorityLabel()}
              </Button>
              {priorityPickerOpen && (
                <div className="absolute top-full left-0 z-50 mt-1 w-36 rounded-lg border border-border bg-popover shadow-lg p-1">
                  {[
                    { value: "high", label: "High" },
                    { value: "medium", label: "Medium" },
                    { value: "low", label: "Low" },
                  ].map((option) => (
                    <button
                      key={option.value}
                      onClick={() => {
                        setPriority(option.value);
                        setPriorityPickerOpen(false);
                      }}
                      className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-xs hover:bg-muted/50"
                    >
                      <span>{option.label}</span>
                      {priority === option.value && (
                        <Check className="h-3.5 w-3.5 text-primary" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Assignee picker */}
            <div className="relative" ref={assigneePickerRef}>
              <Button
                variant="outline"
                size="sm"
                className={cn(
                  "text-xs gap-1.5",
                  assigneeIds.length > 0 && "text-foreground",
                  assigneeIds.length === 0 && "text-muted-foreground"
                )}
                onClick={() => {
                  const opening = !assigneePickerOpen;
                  setAssigneePickerOpen(opening);
                  setDatePickerOpen(false);
                  setPriorityPickerOpen(false);
                  setRecordPickerOpen(false);
                  if (opening) searchPeople("", setAssigneeResults, setAssigneeLoading);
                }}
              >
                <User className="h-3.5 w-3.5" />
                {assignedMembers.length > 0
                  ? `${assignedMembers.length} assigned person${assignedMembers.length > 1 ? "s" : ""}`
                  : "Assign person"}
              </Button>
              {assigneePickerOpen && (
                <div className="absolute top-full left-0 z-50 mt-1 w-56 rounded-lg border border-border bg-popover shadow-lg">
                  <div className="p-2">
                    <div className="relative">
                      <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        value={assigneeSearch}
                        onChange={(e) => {
                          setAssigneeSearch(e.target.value);
                          searchPeople(e.target.value, setAssigneeResults, setAssigneeLoading);
                        }}
                        placeholder="Find a person..."
                        className="h-8 pl-8 text-xs"
                        autoFocus
                      />
                    </div>
                  </div>
                  <div className="max-h-40 overflow-auto px-1 pb-2">
                    {assigneeLoading && assigneeResults.length === 0 && (
                      <p className="px-2 py-3 text-center text-xs text-muted-foreground">
                        Searching...
                      </p>
                    )}
                    {!assigneeLoading && assigneeResults.length === 0 && (
                      <p className="px-2 py-3 text-center text-xs text-muted-foreground">
                        No people
                      </p>
                    )}
                    {assigneeResults.map((m) => (
                      <button
                        key={m.id}
                        onClick={() => toggleAssignee(m.id)}
                        className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted/50"
                      >
                        <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-medium text-primary shrink-0">
                          {(m.displayName || "?")[0].toUpperCase()}
                        </div>
                        <span className="flex-1 truncate text-left text-xs">
                          {m.displayName}
                        </span>
                        {assigneeIds.includes(m.id) && (
                          <Check className="h-3.5 w-3.5 text-primary shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Person linking */}
            <div className="relative" ref={recordPickerRef}>
              <Button
                variant="outline"
                size="sm"
                className={cn(
                  "text-xs gap-1.5",
                  linkedRecords.length > 0 && "text-foreground",
                  linkedRecords.length === 0 && "text-muted-foreground"
                )}
                onClick={() => {
                  const opening = !recordPickerOpen;
                  setRecordPickerOpen(opening);
                  setDatePickerOpen(false);
                  setPriorityPickerOpen(false);
                  setAssigneePickerOpen(false);
                  if (opening) loadBrowseResults();
                }}
              >
                <Link2 className="h-3.5 w-3.5" />
                {linkedRecords.length > 0
                  ? `${linkedRecords.length} linked person${linkedRecords.length > 1 ? "s" : ""}`
                  : "Add person"}
              </Button>
              {recordPickerOpen && (
                <div className="absolute top-full left-0 z-50 mt-1 w-64 rounded-lg border border-border bg-popover shadow-lg">
                  {/* Show linked records with remove button */}
                  {linkedRecords.length > 0 && (
                    <div className="border-b border-border p-2 flex flex-wrap gap-1.5">
                      {linkedRecords.map((r) => {
                        const chipColor =
                          r.objectSlug === "companies"
                            ? "bg-blue-500"
                            : r.objectSlug === "people"
                              ? "bg-purple-500"
                              : r.objectSlug === "deals"
                                ? "bg-orange-500"
                                : "bg-muted-foreground";
                        return (
                          <div
                            key={r.id}
                            className="flex items-center gap-1.5 rounded-md border border-border px-2 py-1 text-xs bg-muted/30"
                          >
                            <div
                              className={cn(
                                "h-3 w-3 rounded flex items-center justify-center shrink-0",
                                chipColor
                              )}
                            >
                              <Building2 className="h-2 w-2 text-white" />
                            </div>
                            <span className="truncate max-w-[120px]">
                              {r.displayName}
                            </span>
                            <button
                              onClick={() => removeRecord(r.id)}
                              className="shrink-0 text-muted-foreground hover:text-destructive"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  <div className="p-2">
                    <div className="relative">
                      <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        value={recordSearch}
                        onChange={(e) => {
                          setRecordSearch(e.target.value);
                          searchRecords(e.target.value);
                        }}
                        placeholder="Search people..."
                        className="h-8 pl-8 text-xs"
                        autoFocus
                      />
                    </div>
                  </div>
                  <div className="max-h-48 overflow-auto px-1 pb-2">
                    {searchLoading && searchResults.length === 0 && (
                      <p className="px-2 py-3 text-center text-xs text-muted-foreground">
                        Searching...
                      </p>
                    )}
                    {!searchLoading && recordSearch && searchResults.length === 0 && (
                      <p className="px-2 py-3 text-center text-xs text-muted-foreground">
                        No results
                      </p>
                    )}
                    {searchResults
                      .filter(
                        (r) =>
                          r.objectSlug === "people" &&
                          !linkedRecords.find((lr) => lr.id === r.id)
                      )
                      .map((r) => {
                        const color =
                          r.objectSlug === "companies"
                            ? "bg-blue-500"
                            : r.objectSlug === "people"
                              ? "bg-purple-500"
                              : r.objectSlug === "deals"
                                ? "bg-orange-500"
                                : "bg-muted-foreground";
                        return (
                          <button
                            key={r.id}
                            onClick={() => addRecord(r)}
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted/50"
                          >
                            <div
                              className={cn(
                                "h-4 w-4 rounded flex items-center justify-center shrink-0",
                                color
                              )}
                            >
                              <Building2 className="h-2.5 w-2.5 text-white" />
                            </div>
                            <span className="font-medium truncate text-left text-xs">
                              {r.displayName}
                            </span>
                            {r.subtitle && r.subtitle !== r.objectName && (
                              <span className="text-[11px] text-muted-foreground shrink-0">
                                {r.subtitle}
                              </span>
                            )}
                          </button>
                        );
                      })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <DialogFooter className="flex-row items-center gap-2 sm:justify-between">
          <div className="flex items-center gap-2">
            {mode === "create" && (
              <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
                <input
                  type="checkbox"
                  checked={createMore}
                  onChange={(e) => setCreateMore(e.target.checked)}
                  className="rounded border-border"
                />
                Create more
              </label>
            )}
            {mode === "edit" && onDelete && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-destructive hover:text-destructive"
                onClick={async () => {
                  await onDelete();
                  onOpenChange(false);
                }}
              >
                Delete
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={!content.trim() || saving}
            >
              {saving ? "Saving..." : "Save"}
              <span className="ml-1.5 text-[10px] text-primary-foreground/60">
                Ctrl+Enter
              </span>
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
