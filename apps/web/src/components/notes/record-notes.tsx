"use client";

import { useState, useEffect, useCallback } from "react";
import { NoteEditor } from "./note-editor";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Trash2, ChevronDown, ChevronRight, Phone, NotebookPen, CheckSquare } from "lucide-react";

interface Note {
  id: string;
  noteType: string;
  title: string;
  content: unknown;
  linkedTaskId: string | null;
  createdAt: string;
  updatedAt: string;
}

interface RecordNotesProps {
  objectSlug: string;
  recordId: string;
  composeRequest?: { token: number; noteType: "call" | "meeting" | "note" };
  onAddTask?: () => void;
}

export function RecordNotes({ objectSlug, recordId, composeRequest, onAddTask }: RecordNotesProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // New note form
  const [newNoteType, setNewNoteType] = useState<"call" | "meeting" | "note">("note");
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState<unknown>(null);
  const [needsFollowUp, setNeedsFollowUp] = useState(false);
  const [followUpTaskContent, setFollowUpTaskContent] = useState("");
  const [followUpDeadline, setFollowUpDeadline] = useState("");

  const fetchNotes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `/api/v1/objects/${objectSlug}/records/${recordId}/notes`
      );
      if (res.ok) {
        const data = await res.json();
        setNotes(data.data);
      }
    } finally {
      setLoading(false);
    }
  }, [objectSlug, recordId]);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  useEffect(() => {
    if (!composeRequest?.token) return;
    setCreating(true);
    setExpandedId(null);
    setNewNoteType(composeRequest.noteType);
    if (composeRequest.noteType === "call" && !newTitle) setNewTitle("Call log");
    if (composeRequest.noteType === "meeting" && !newTitle) setNewTitle("Meeting log");
    if (composeRequest.noteType === "note" && !newTitle) setNewTitle("");
  }, [composeRequest?.token]);

  async function handleCreate() {
    if (!newTitle.trim() && !newContent) return;

    const res = await fetch(
      `/api/v1/objects/${objectSlug}/records/${recordId}/notes`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newTitle,
          content: newContent,
          noteType: newNoteType,
        }),
      }
    );

    if (res.ok) {
      const created = await res.json().then((r) => r.data);

      if (needsFollowUp && followUpTaskContent.trim()) {
        const taskRes = await fetch("/api/v1/tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: followUpTaskContent,
            deadline: followUpDeadline || null,
            recordIds: [recordId],
            sourceNoteId: created.id,
          }),
        });

        if (taskRes.ok) {
          const task = await taskRes.json().then((r) => r.data);
          await fetch(`/api/v1/notes/${created.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ linkedTaskId: task.id }),
          });
        }
      }

      setNewNoteType("note");
      setNewTitle("");
      setNewContent(null);
      setNeedsFollowUp(false);
      setFollowUpTaskContent("");
      setFollowUpDeadline("");
      setCreating(false);
      fetchNotes();
    }
  }

  async function handleUpdate(noteId: string, updates: { title?: string; content?: unknown }) {
    await fetch(`/api/v1/notes/${noteId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });

    setNotes((prev) =>
      prev.map((n) => (n.id === noteId ? { ...n, ...updates } : n))
    );
  }

  async function handleDelete(noteId: string) {
    await fetch(`/api/v1/notes/${noteId}`, { method: "DELETE" });
    setNotes((prev) => prev.filter((n) => n.id !== noteId));
  }

  function startCreate(noteType: "call" | "meeting" | "note") {
    setCreating(true);
    setExpandedId(null);
    setNewNoteType(noteType);
    setNewTitle(
      noteType === "call" ? "Call log" : noteType === "meeting" ? "Meeting log" : ""
    );
  }

  function getNoteTypeLabel(noteType: string) {
    if (noteType === "call") return "Call";
    if (noteType === "meeting") return "Meeting";
    return "Note";
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Notes</h3>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => startCreate("call")} className="text-xs">
            <Phone className="mr-1 h-3.5 w-3.5" />
            Log call
          </Button>
          <Button variant="ghost" size="sm" onClick={() => startCreate("meeting")} className="text-xs">
            <NotebookPen className="mr-1 h-3.5 w-3.5" />
            Log meeting
          </Button>
          <Button variant="ghost" size="sm" onClick={() => startCreate("note")} className="text-xs">
            <Plus className="mr-1 h-3.5 w-3.5" />
            Add note
          </Button>
          {onAddTask && (
            <Button variant="ghost" size="sm" onClick={onAddTask} className="text-xs">
              <CheckSquare className="mr-1 h-3.5 w-3.5" />
              Add task
            </Button>
          )}
        </div>
      </div>

      {/* Create form */}
      {creating && (
        <div className="space-y-2 rounded-lg border border-border p-3">
          <div className="flex flex-wrap gap-2">
            {(["call", "meeting", "note"] as const).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setNewNoteType(type)}
                className={`rounded-md border px-2 py-1 text-xs ${newNoteType === type ? "border-primary bg-primary/10 text-foreground" : "border-border text-muted-foreground"}`}
              >
                {getNoteTypeLabel(type)}
              </button>
            ))}
          </div>
          <Input
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder={newNoteType === "call" ? "Call title" : newNoteType === "meeting" ? "Meeting title" : "Note title"}
            className="h-8 text-sm"
          />
          <NoteEditor
            content={newContent}
            onChange={setNewContent}
            placeholder={newNoteType === "call" ? "What happened on the call?" : newNoteType === "meeting" ? "Meeting recap, decisions, next steps..." : "Write your note..."}
          />
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={needsFollowUp}
              onChange={(e) => setNeedsFollowUp(e.target.checked)}
            />
            Needs follow-up task
          </label>
          {needsFollowUp && (
            <div className="rounded-md border border-border/60 p-3 space-y-2">
              <Input
                value={followUpTaskContent}
                onChange={(e) => setFollowUpTaskContent(e.target.value)}
                placeholder="Follow-up task"
                className="h-8 text-sm"
              />
              <input
                type="date"
                value={followUpDeadline}
                onChange={(e) => setFollowUpDeadline(e.target.value)}
                className="flex h-8 w-full rounded-lg border border-border bg-transparent px-3 py-2 text-sm"
              />
            </div>
          )}
          <div className="flex justify-end gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setCreating(false);
                setNeedsFollowUp(false);
              }}
            >
              Cancel
            </Button>
            <Button size="sm" onClick={handleCreate}>
              Save
            </Button>
          </div>
        </div>
      )}

      {/* Notes list */}
      {loading && notes.length === 0 && (
        <p className="text-xs text-muted-foreground py-4 text-center">
          Loading...
        </p>
      )}

      {!loading && notes.length === 0 && !creating && (
        <p className="text-xs text-muted-foreground py-4 text-center">
          No notes yet
        </p>
      )}

      <div className="space-y-2">
        {notes.map((note) => {
          const isExpanded = expandedId === note.id;
          return (
            <div
              key={note.id}
              className="rounded-lg border border-border/60 bg-card/30"
            >
              {/* Header */}
              <div
                className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-muted/20"
                onClick={() => setExpandedId(isExpanded ? null : note.id)}
              >
                {isExpanded ? (
                  <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                ) : (
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                )}
                <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                  {getNoteTypeLabel(note.noteType)}
                </span>
                <span className="text-sm font-medium flex-1 truncate">
                  {note.title || "Untitled"}
                </span>
                {note.linkedTaskId && (
                  <span className="text-[10px] text-primary">Linked task</span>
                )}
                <span className="text-xs text-muted-foreground">
                  {new Date(note.updatedAt).toLocaleDateString()}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(note.id);
                  }}
                  className="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* Expanded content */}
              {isExpanded && (
                <div className="px-3 pb-3">
                  <NoteEditor
                    content={note.content}
                    onChange={(content) =>
                      handleUpdate(note.id, { content })
                    }
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
