"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Plus,
  StickyNote,
  Star,
  ArrowUpDown,
  Building2,
  ChevronDown,
  ChevronRight,
  Phone,
  NotebookPen,
  CheckSquare,
  Calendar,
  Search,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ChooseRecordDialog } from "@/components/records/choose-record-dialog";
import { NoteEditorPanel } from "@/components/notes/note-editor-panel";
import { isToday, isYesterday, isThisWeek, format } from "date-fns";

// ─── Types ───────────────────────────────────────────────────────────

interface Note {
  id: string;
  recordId: string;
  title: string;
  content: unknown;
  noteType: string;
  noteDate: string;
  createdAt: string;
  updatedAt: string;
  recordDisplayName?: string;
  objectSlug?: string;
  objectName?: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────

type DateGroup = "today" | "yesterday" | "this_week" | "older";

function getDateGroup(dateStr: string): DateGroup {
  const d = new Date(dateStr);
  if (isToday(d)) return "today";
  if (isYesterday(d)) return "yesterday";
  if (isThisWeek(d, { weekStartsOn: 1 })) return "this_week";
  return "older";
}

const GROUP_LABELS: Record<DateGroup, string> = {
  today: "Created today",
  yesterday: "Yesterday",
  this_week: "This week",
  older: "Older",
};

const GROUP_ORDER: DateGroup[] = ["today", "yesterday", "this_week", "older"];

const OBJECT_COLORS: Record<string, string> = {
  companies: "bg-blue-500",
  people: "bg-purple-500",
  deals: "bg-orange-500",
};

function getContentPreview(content: unknown): string {
  if (!content) return "This note has no content.";
  try {
    const doc = content as { content?: Array<{ content?: Array<{ text?: string }> }> };
    if (doc.content) {
      for (const block of doc.content) {
        if (block.content) {
          for (const inline of block.content) {
            if (inline.text && inline.text.trim()) {
              return inline.text.trim().slice(0, 100);
            }
          }
        }
      }
    }
  } catch {
    // ignore
  }
  return "This note has no content.";
}

function getContentText(content: unknown): string {
  if (!content) return "";
  try {
    const doc = content as { content?: Array<{ content?: Array<{ text?: string }> }> };
    if (!doc.content) return "";
    const texts: string[] = [];
    for (const block of doc.content) {
      if (block.content) {
        for (const inline of block.content) {
          if (inline.text && inline.text.trim()) {
            texts.push(inline.text.trim());
          }
        }
      }
    }
    return texts.join(" ");
  } catch {
    return "";
  }
}

function getRelativeDate(dateStr: string): string {
  const d = new Date(dateStr);
  if (isToday(d)) return "Today";
  if (isYesterday(d)) return "Yesterday";
  return format(d, "MMM d");
}

const NOTE_TYPE_COLORS: Record<string, string> = {
  call: "bg-blue-100 text-blue-800",
  meeting: "bg-green-100 text-green-800",
  zoom: "bg-purple-100 text-purple-800",
  note: "bg-gray-100 text-gray-800",
  task: "bg-orange-100 text-orange-800",
};

function getNoteTypeLabel(type: string): string {
  if (type === "call") return "Call";
  if (type === "meeting") return "Meeting";
  if (type === "zoom") return "Zoom";
  if (type === "task") return "Task";
  return "Note";
}

// ─── Main Component ─────────────────────────────────────────────────

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'createdAt' | 'updatedAt'>('createdAt');
  const [selectedNoteType, setSelectedNoteType] = useState<"call" | "meeting" | "note">("note");
  const [searchQuery, setSearchQuery] = useState("");

  // Choose record dialog
  const [chooseRecordOpen, setChooseRecordOpen] = useState(false);

  // Note editor panel
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorNoteId, setEditorNoteId] = useState<string | undefined>();
  const [editorRecordId, setEditorRecordId] = useState<string | undefined>();
  const [editorRecordName, setEditorRecordName] = useState<string | undefined>();
  const [editorObjectSlug, setEditorObjectSlug] = useState<string | undefined>();
  const [editorNoteType, setEditorNoteType] = useState<"call" | "meeting" | "note">("note");

  // Collapsed groups
  const [collapsedGroups, setCollapsedGroups] = useState<Set<DateGroup>>(
    new Set()
  );

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/notes?limit=100");
      if (res.ok) {
        const data = await res.json();
        setNotes(data.data.notes);
        setTotal(data.data.pagination.total);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  function handleNewNote() {
    startAction("note");
  }

  function startAction(noteType: "call" | "meeting" | "note") {
    setSelectedNoteType(noteType);
    setChooseRecordOpen(true);
  }

  function handleAddTask() {
    // TODO: implement task creation
    console.log("Add task clicked");
  }

  function handleRecordSelected(record: {
    recordId: string;
    displayName: string;
    objectSlug: string;
  }) {
    setEditorNoteId(undefined);
    setEditorRecordId(record.recordId);
    setEditorRecordName(record.displayName);
    setEditorObjectSlug(record.objectSlug);
    setEditorNoteType(selectedNoteType);
    setEditorOpen(true);
  }

  function handleNoteClick(note: Note) {
    setEditorNoteId(note.id);
    setEditorRecordId(note.recordId);
    setEditorRecordName(note.recordDisplayName);
    setEditorObjectSlug(note.objectSlug);
    setEditorOpen(true);
  }

  function handleNoteDateChange(noteId: string, newDate: string) {
    setNotes(prev => prev.map(note => 
      note.id === noteId ? { ...note, noteDate: newDate } : note
    ));
  }

  function toggleGroup(key: DateGroup) {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  // Filter notes based on search query
  const filteredNotes = searchQuery.trim() === "" 
    ? notes 
    : notes.filter(note => {
        const query = searchQuery.toLowerCase();
        const title = (note.title || "").toLowerCase();
        const recordName = (note.recordDisplayName || "").toLowerCase();
        const noteType = (note.noteType || "").toLowerCase();
        const contentText = getContentText(note.content).toLowerCase();
        
        return title.includes(query) ||
               recordName.includes(query) || 
               noteType.includes(query) ||
               contentText.includes(query);
      });
  
  const filteredCount = filteredNotes.length;

  // Sort notes based on current sort preference
  const sortedNotes = [...filteredNotes].sort((a, b) => {
    const aVal = new Date(sortBy === 'createdAt' ? a.createdAt : a.updatedAt);
    const bVal = new Date(sortBy === 'createdAt' ? b.createdAt : b.updatedAt);
    return bVal.getTime() - aVal.getTime(); // descending
  });

  // Group notes by date (using the same field as sorting for consistency)
  const groups = new Map<DateGroup, Note[]>();
  for (const note of sortedNotes) {
    const key = getDateGroup(sortBy === 'createdAt' ? note.createdAt : note.updatedAt);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(note);
  }

  const visibleGroups = GROUP_ORDER.filter((key) => groups.has(key));

  const groupLabels = {
    today: sortBy === 'createdAt' ? 'Created today' : 'Updated today',
    yesterday: sortBy === 'createdAt' ? 'Yesterday' : 'Updated yesterday',
    this_week: sortBy === 'createdAt' ? 'This week' : 'Updated this week',
    older: sortBy === 'createdAt' ? 'Older' : 'Older',
  };

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">Notes</h1>
          <span className="text-sm text-muted-foreground">
            {searchQuery ? `${filteredCount} of ${total}` : total}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Search input */}
          <div className="relative mr-2">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search names or words..."
              className="pl-9 pr-8 h-8 w-48 text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Sort pill */}
          <button
            type="button"
            onClick={() => setSortBy(sortBy === 'createdAt' ? 'updatedAt' : 'createdAt')}
            className="flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs text-muted-foreground hover:bg-muted/20 transition-colors"
          >
            <ArrowUpDown className="h-3 w-3" />
            <span>{sortBy === 'createdAt' ? 'Creation date' : 'Last updated'}</span>
          </button>

          <Button variant="ghost" size="sm" onClick={() => startAction("call")} className="text-xs">
            <Phone className="mr-1 h-3.5 w-3.5" />
            Log call
          </Button>
          <Button variant="ghost" size="sm" onClick={() => startAction("meeting")} className="text-xs">
            <NotebookPen className="mr-1 h-3.5 w-3.5" />
            Log meeting
          </Button>
          <Button variant="ghost" size="sm" onClick={() => startAction("note")} className="text-xs">
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add note
          </Button>
          <Button variant="ghost" size="sm" onClick={handleAddTask} className="text-xs">
            <CheckSquare className="mr-1 h-3.5 w-3.5" />
            Add task
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {/* Favorites section */}
        <div className="px-4 pt-4 pb-2">
          <h2 className="text-xs font-medium text-muted-foreground mb-3">
            Favorites
          </h2>
          <div className="rounded-lg border-2 border-dashed border-border/50 py-8 text-center">
            <Star className="h-6 w-6 text-muted-foreground/20 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Favorites</p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Notes that you favorite will appear here
            </p>
          </div>
        </div>

        {/* Loading / Empty states */}
        {loading && notes.length === 0 && (
          <p className="text-muted-foreground text-center py-12">Loading...</p>
        )}

        {!loading && notes.length === 0 && (
          <div className="text-center py-12">
            <StickyNote className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-muted-foreground">No notes yet.</p>
            <p className="text-sm text-muted-foreground/60 mt-1">
              Click &quot;+ New note&quot; to create your first note.
            </p>
          </div>
        )}

        {/* No search results */}
        {!loading && notes.length > 0 && filteredCount === 0 && searchQuery && (
          <div className="text-center py-12">
            <Search className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-muted-foreground">No notes match your search.</p>
            <p className="text-sm text-muted-foreground/60 mt-1">
              Try a different name or keyword.
            </p>
          </div>
        )}

        {/* Date-grouped notes */}
        {visibleGroups.map((groupKey) => {
          const groupNotes = groups.get(groupKey)!;
          const isCollapsed = collapsedGroups.has(groupKey);

          return (
            <div key={groupKey} className="px-4 pt-4">
              {/* Group header */}
              <button
                onClick={() => toggleGroup(groupKey)}
                className="flex items-center gap-2 mb-3 text-xs font-medium text-muted-foreground hover:text-foreground"
              >
                {isCollapsed ? (
                  <ChevronRight className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
                {groupLabels[groupKey]}
                <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px]">
                  {groupNotes.length}
                </span>
              </button>

              {/* Note cards */}
              {!isCollapsed && (
                <div className="space-y-2">
                  {groupNotes.map((note) => (
                    <NoteCard
                      key={note.id}
                      note={note}
                      onClick={() => handleNoteClick(note)}
                      onDateChange={handleNoteDateChange}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Choose Record Dialog */}
      <ChooseRecordDialog
        open={chooseRecordOpen}
        onOpenChange={setChooseRecordOpen}
        onSelect={handleRecordSelected}
      />

      {/* Note Editor Panel */}
      <NoteEditorPanel
        open={editorOpen}
        onOpenChange={(open) => {
          setEditorOpen(open);
          if (!open) fetchNotes(); // Refresh list when closing
        }}
        noteId={editorNoteId}
        recordId={editorRecordId}
        recordDisplayName={editorRecordName}
        objectSlug={editorObjectSlug}
        noteType={editorNoteType}
        onNoteCreated={fetchNotes}
        onNoteDeleted={fetchNotes}
      />
    </div>
  );
}

// ─── Note Card ───────────────────────────────────────────────────────

function NoteCard({
  note,
  onClick,
  onDateChange,
}: {
  note: Note;
  onClick: () => void;
  onDateChange?: (noteId: string, newDate: string) => void;
}) {
  const objectColor =
    OBJECT_COLORS[note.objectSlug || ""] || "bg-muted-foreground";
  const preview = getContentPreview(note.content);
  const noteTitle = note.title || "Untitled";
  const recordName = note.recordDisplayName || "Unknown";
  const displayDate = getRelativeDate(note.noteDate || note.updatedAt || note.createdAt);
  const noteTypeLabel = getNoteTypeLabel(note.noteType || "note");
  const noteTypeColor = NOTE_TYPE_COLORS[note.noteType || "note"] || "bg-gray-100 text-gray-800";

  const [isEditingDate, setIsEditingDate] = useState(false);
  const [tempDate, setTempDate] = useState("");
  const dateInputRef = useRef<HTMLInputElement>(null);

  // Initialize temp date
  useEffect(() => {
    if (note.noteDate) {
      const d = new Date(note.noteDate);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      setTempDate(`${yyyy}-${mm}-${dd}`);
    }
  }, [note.noteDate]);

  async function updateNoteField(field: "noteDate" | "noteType", value: string) {
    try {
      const res = await fetch(`/api/v1/notes/${note.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [field]: value }),
      });
      if (!res.ok) throw new Error("Failed to update note");
      // Notify parent of date change
      if (field === "noteDate" && onDateChange) {
        onDateChange(note.id, value);
      }
    } catch (err) {
      console.error("Error updating note:", err);
    }
  }

  function handleDateClick(e: React.MouseEvent) {
    e.stopPropagation();
    setIsEditingDate(true);
    setTimeout(() => dateInputRef.current?.focus(), 10);
  }

  function handleDateChange(e: React.ChangeEvent<HTMLInputElement>) {
    setTempDate(e.target.value);
  }

  function handleDateSave() {
    if (tempDate) {
      updateNoteField("noteDate", tempDate);
    }
    setIsEditingDate(false);
  }

  function handleDateCancel() {
    setIsEditingDate(false);
    // Reset temp date to original
    if (note.noteDate) {
      const d = new Date(note.noteDate);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      setTempDate(`${yyyy}-${mm}-${dd}`);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      handleDateSave();
    } else if (e.key === "Escape") {
      handleDateCancel();
    }
  }

  return (
    <div
      onClick={onClick}
      className="group rounded-lg border border-border/60 bg-card/30 px-4 py-3 hover:bg-muted/20 cursor-pointer transition-colors"
    >
      {/* First line: Name • Note • Type • Date */}
      <div className="flex items-center gap-2 mb-1.5 truncate">
        {/* Record icon and name */}
        <div className="flex items-center gap-1.5 shrink-0">
          <div
            className={cn(
              "h-3.5 w-3.5 rounded flex items-center justify-center shrink-0",
              objectColor
            )}
          >
            <Building2 className="h-2 w-2 text-white" />
          </div>
          <span className="text-xs font-medium text-muted-foreground truncate">
            {recordName}
          </span>
        </div>

        {/* Separator */}
        <span className="text-xs text-muted-foreground/40 shrink-0">•</span>

        {/* Note title */}
        <span className="text-xs font-medium truncate">
          {noteTitle}
        </span>

        {/* Separator */}
        <span className="text-xs text-muted-foreground/40 shrink-0">•</span>

        {/* Note type badge */}
        <Badge
          variant="outline"
          className={cn(
            "text-[10px] px-1.5 py-0 h-4 rounded-sm border-0",
            noteTypeColor
          )}
        >
          {noteTypeLabel}
        </Badge>

        {/* Date - editable */}
        <div className="ml-auto flex items-center gap-1 shrink-0">
          {isEditingDate ? (
            <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              <input
                ref={dateInputRef}
                type="date"
                value={tempDate}
                onChange={handleDateChange}
                onKeyDown={handleKeyDown}
                onBlur={handleDateSave}
                className="text-xs bg-transparent border border-border rounded px-1 py-0.5 w-24"
              />
              <Button
                size="icon"
                variant="ghost"
                className="h-4 w-4"
                onClick={handleDateSave}
              >
                <CheckSquare className="h-3 w-3" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-4 w-4"
                onClick={handleDateCancel}
              >
                <span className="text-xs">✕</span>
              </Button>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleDateClick}
              className="text-xs text-muted-foreground/60 hover:text-foreground flex items-center gap-0.5 transition-colors"
              title="Click to change date"
            >
              <Calendar className="h-3 w-3" />
              {displayDate}
            </button>
          )}
        </div>
      </div>

      {/* Second line: Detailed comment */}
      <p className="text-xs text-muted-foreground/60 truncate">
        {preview}
      </p>
    </div>
  );
}
