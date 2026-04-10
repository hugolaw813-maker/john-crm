"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  Plus,
  Check,
  Circle,
  Calendar,
  Eye,
  EyeOff,
  ArrowUpDown,
  ChevronDown,
  ChevronRight,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { TaskDialog } from "./task-dialog";
import { Popover } from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import {
  isToday,
  isTomorrow,
  isYesterday,
  isPast,
  isFuture,
  isThisWeek,
  differenceInDays,
  format,
} from "date-fns";

// ─── Types ───────────────────────────────────────────────────────────

interface Task {
  id: string;
  content: string;
  deadline: string | null;
  priority: string;
  isCompleted: boolean;
  completedAt: string | null;
  createdBy: string | null;
  createdAt: string;
  linkedRecords: { id: string; displayName: string; objectSlug: string }[];
  assignees: { id: string; displayName: string; objectSlug: string }[];
}

interface CurrentUser {
  id: string;
  name: string;
  email: string;
}

interface PersonSearchResult {
  id: string;
  displayName: string;
  subtitle?: string;
  objectSlug: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────

function getRelativeDateLabel(deadline: string): {
  label: string;
  color: string;
} {
  const d = new Date(deadline);
  const now = new Date();
  now.setHours(0, 0, 0, 0);

  if (isToday(d)) return { label: "Due today", color: "text-orange-400" };
  if (isTomorrow(d)) return { label: "Due tomorrow", color: "text-orange-400" };
  if (isYesterday(d)) return { label: "Due yesterday", color: "text-destructive" };

  const days = differenceInDays(d, now);
  if (days < 0) {
    return {
      label: `Overdue ${Math.abs(days)}d`,
      color: "text-destructive",
    };
  }
  if (days <= 7)
    return {
      label: `Due ${format(d, "EEEE")}`,
      color: "text-orange-400",
    };
  return { label: `Due ${format(d, "MMM d")}`, color: "text-muted-foreground" };
}

type GroupKey =
  | "overdue"
  | "today"
  | "this_week"
  | "next_week"
  | "later"
  | "no_date"
  | "completed";

function getGroupKey(task: Task): GroupKey {
  if (task.isCompleted) return "completed";
  if (!task.deadline) return "no_date";

  const d = new Date(task.deadline);
  const now = new Date();
  now.setHours(0, 0, 0, 0);

  if (isPast(d) && !isToday(d)) return "overdue";
  if (isToday(d)) return "today";
  if (isThisWeek(d, { weekStartsOn: 1 })) return "this_week";

  const days = differenceInDays(d, now);
  if (days <= 14) return "next_week";
  return "later";
}

const GROUP_LABELS: Record<GroupKey, string> = {
  overdue: "Overdue",
  today: "Today",
  this_week: "This week",
  next_week: "Next week",
  later: "Later",
  no_date: "No date",
  completed: "Completed",
};

const GROUP_ORDER: GroupKey[] = [
  "overdue",
  "today",
  "this_week",
  "next_week",
  "later",
  "no_date",
  "completed",
];

// ─── Main Component ─────────────────────────────────────────────────

export function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showCompleted, setShowCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<"create" | "edit">("create");
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  // Collapsed groups
  const [collapsedGroups, setCollapsedGroups] = useState<Set<GroupKey>>(
    new Set()
  );

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/v1/tasks?showCompleted=${showCompleted}&limit=200`
      );
      if (res.ok) {
        const data = await res.json();
        setTasks(data.data.tasks);
        setTotal(data.data.pagination.total);
      } else {
        const data = await res.json().catch(() => null);
        setError(
          data?.error?.message || `Failed to load tasks (${res.status})`
        );
      }
    } catch {
      setError("Network error — could not load tasks");
    } finally {
      setLoading(false);
    }
  }, [showCompleted]);

  // Fetch current user
  useEffect(() => {
    fetch("/api/auth/get-session")
      .then((r) => r.json())
      .then((data) => {
        if (data?.user) {
          setCurrentUser({
            id: data.user.id,
            name: data.user.name || "",
            email: data.user.email || "",
          });
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  async function toggleComplete(taskId: string, isCompleted: boolean) {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId ? { ...t, isCompleted: !isCompleted } : t
      )
    );

    await fetch(`/api/v1/tasks/${taskId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ isCompleted: !isCompleted }),
    });
  }

  function openCreateDialog() {
    setDialogMode("create");
    setEditingTask(null);
    setDialogOpen(true);
  }

  function openEditDialog(task: Task) {
    setDialogMode("edit");
    setEditingTask(task);
    setDialogOpen(true);
  }

  async function handleSave(data: {
    content: string;
    deadline: string | null;
    priority: string;
    recordIds: string[];
    assigneeIds: string[];
  }) {
    if (dialogMode === "create") {
      const res = await fetch("/api/v1/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.error?.message || "Failed to create task");
      }
    } else if (editingTask) {
      const res = await fetch(`/api/v1/tasks/${editingTask.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.error?.message || "Failed to update task");
      }
    }
    fetchTasks();
  }

  async function handleDelete() {
    if (!editingTask) return;
    await fetch(`/api/v1/tasks/${editingTask.id}`, { method: "DELETE" });
    fetchTasks();
  }

  async function updateTaskPerson(taskId: string, personId: string) {
    const res = await fetch(`/api/v1/tasks/${taskId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recordIds: personId ? [personId] : [] }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.error?.message || "Failed to update task person");
    }
    fetchTasks();
  }

  function toggleGroup(key: GroupKey) {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  // Group tasks
  const groups = new Map<GroupKey, Task[]>();
  for (const task of tasks) {
    const key = getGroupKey(task);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(task);
  }

  const visibleGroups = GROUP_ORDER.filter((key) => groups.has(key));

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">Tasks</h1>
          <span className="text-sm text-muted-foreground">
            {total} {total === 1 ? "task" : "tasks"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Sort pill */}
          <div className="flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs text-muted-foreground">
            <ArrowUpDown className="h-3 w-3" />
            <span>Due date</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCompleted(!showCompleted)}
            className="text-xs gap-1"
          >
            {showCompleted ? (
              <EyeOff className="h-3.5 w-3.5" />
            ) : (
              <Eye className="h-3.5 w-3.5" />
            )}
            {showCompleted ? "Hide completed" : "Show completed"}
          </Button>
          <Button size="sm" onClick={openCreateDialog}>
            <Plus className="mr-1 h-4 w-4" />
            New task
          </Button>
        </div>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-[1fr_120px_120px_150px_120px] gap-2 border-b border-border px-4 py-1.5 text-xs font-medium text-muted-foreground">
        <span>Task</span>
        <span>Due date</span>
        <span>Status</span>
        <span>Person</span>
        <span>Assigned to</span>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-4 mt-2 rounded-md bg-destructive/10 border border-destructive/20 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Task list */}
      <div className="flex-1 overflow-auto">
        {loading && tasks.length === 0 && (
          <p className="text-muted-foreground text-center py-12">Loading...</p>
        )}

        {!loading && tasks.length === 0 && (
          <div className="text-center py-12 space-y-2">
            <p className="text-muted-foreground">
              No tasks yet! Create your first task to get started.
            </p>
            <Button size="sm" variant="outline" onClick={openCreateDialog}>
              <Plus className="mr-1 h-4 w-4" />
              New task
            </Button>
          </div>
        )}

        {visibleGroups.map((groupKey) => {
          const groupTasks = groups.get(groupKey)!;
          const isCollapsed = collapsedGroups.has(groupKey);

          return (
            <div key={groupKey}>
              {/* Group header */}
              <button
                onClick={() => toggleGroup(groupKey)}
                className="flex w-full items-center gap-2 border-b border-border/50 bg-muted/20 px-4 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted/30"
              >
                {isCollapsed ? (
                  <ChevronRight className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
                <span
                  className={cn(
                    groupKey === "overdue" && "text-destructive"
                  )}
                >
                  {GROUP_LABELS[groupKey]}
                </span>
                <span className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium">
                  {groupTasks.length}
                </span>
              </button>

              {/* Group rows */}
              {!isCollapsed &&
                groupTasks.map((task) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    onToggle={() => toggleComplete(task.id, task.isCompleted)}
                    onPersonChange={(personId) => updateTaskPerson(task.id, personId)}
                    onClick={() => openEditDialog(task)}
                  />
                ))}
            </div>
          );
        })}
      </div>

      {/* Task Dialog */}
      <TaskDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        mode={dialogMode}
        currentUserId={currentUser?.id}
        initialData={
          editingTask
            ? {
                id: editingTask.id,
                content: editingTask.content,
                deadline: editingTask.deadline
                  ? new Date(editingTask.deadline)
                  : null,
                assigneeIds: editingTask.assignees.map((a) => a.id),
                priority: editingTask.priority,
                recordIds: editingTask.linkedRecords.map((r) => r.id),
                linkedRecords: editingTask.linkedRecords,
                assignees: editingTask.assignees,
              }
            : undefined
        }
        onSave={handleSave}
        onDelete={dialogMode === "edit" ? handleDelete : undefined}
      />
    </div>
  );
}

// ─── Table Row ───────────────────────────────────────────────────────

function TaskPersonEditor({
  currentPerson,
  onSave,
}: {
  taskId: string;
  currentPerson?: { id: string; displayName: string; objectSlug: string };
  onSave: (personId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PersonSearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const loadPeople = useCallback(async (search = "") => {
    setLoading(true);
    try {
      if (search.trim()) {
        const res = await fetch(`/api/v1/search?q=${encodeURIComponent(search)}&limit=10`);
        if (res.ok) {
          const data = await res.json();
          setResults(
            (data.data || [])
              .filter((r: { type: string; objectSlug?: string }) => r.type === "record" && r.objectSlug === "people")
              .map((r: { id: string; title: string; subtitle?: string; objectSlug: string }) => ({
                id: r.id,
                displayName: r.title,
                subtitle: r.subtitle || "",
                objectSlug: r.objectSlug,
              }))
          );
        }
      } else {
        const res = await fetch(`/api/v1/records/browse?limit=30`);
        if (res.ok) {
          const data = await res.json();
          setResults(
            (data.data || [])
              .filter((r: { objectSlug?: string }) => r.objectSlug === "people")
              .map((r: { recordId: string; displayName: string; subtitle?: string; objectSlug: string }) => ({
                id: r.recordId,
                displayName: r.displayName,
                subtitle: r.subtitle || "",
                objectSlug: r.objectSlug,
              }))
          );
        }
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) loadPeople(query);
  }, [open, query, loadPeople]);

  return (
    <Popover
      open={open}
      onOpenChange={setOpen}
      trigger={
        <button
          type="button"
          onMouseDown={(e) => e.stopPropagation()}
          className="text-xs text-primary hover:underline truncate text-left"
          title="Edit from main People list"
        >
          {currentPerson?.displayName || "Set Person"}
        </button>
      }
      className="w-72 p-2"
    >
      <div className="space-y-2" onMouseDown={(e) => e.stopPropagation()}>
        <div className="relative">
          <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search the main People list..."
            className="h-8 pl-8 text-xs"
            autoFocus
          />
        </div>
        <div className="max-h-56 overflow-auto space-y-1">
          {loading && <p className="px-2 py-2 text-xs text-muted-foreground">Searching...</p>}
          {!loading && results.length === 0 && (
            <p className="px-2 py-2 text-xs text-muted-foreground">No People found</p>
          )}
          {results.map((person) => (
            <button
              key={person.id}
              type="button"
              onClick={() => {
                onSave(person.id);
                setOpen(false);
              }}
              className="flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-xs hover:bg-muted/50"
            >
              <span className="truncate">{person.displayName}</span>
              {currentPerson?.id === person.id && <Check className="h-3.5 w-3.5 text-primary" />}
            </button>
          ))}
        </div>
      </div>
    </Popover>
  );
}

function TaskRow({
  task,
  onToggle,
  onPersonChange,
  onClick,
}: {
  task: Task;
  onToggle: () => void;
  onPersonChange: (personId: string) => void;
  onClick: () => void;
}) {
  const dateInfo = task.deadline
    ? getRelativeDateLabel(task.deadline)
    : null;
  const linkedPeople = task.linkedRecords.filter(
    (record) => record.objectSlug === "people"
  );
  const displayRecords = linkedPeople.length > 0 ? linkedPeople : task.linkedRecords;

  const priorityClass =
    task.priority === "high"
      ? "bg-red-500/15 text-red-400 border-red-500/30"
      : task.priority === "low"
        ? "bg-slate-500/15 text-slate-300 border-slate-500/30"
        : "bg-amber-500/15 text-amber-300 border-amber-500/30";

  return (
    <div
      className="group grid grid-cols-[1fr_120px_120px_150px_120px] gap-2 items-center border-b border-border/30 px-4 py-2 hover:bg-muted/20 cursor-pointer"
      onClick={onClick}
    >
      {/* Task column */}
      <div className="flex items-center gap-2.5 min-w-0">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
          className="shrink-0"
        >
          {task.isCompleted ? (
            <div className="h-4 w-4 rounded-full bg-primary flex items-center justify-center">
              <Check className="h-2.5 w-2.5 text-primary-foreground" />
            </div>
          ) : (
            <Circle className="h-4 w-4 text-muted-foreground hover:text-primary transition-colors" />
          )}
        </button>
        <span
          className={cn(
            "text-sm truncate",
            task.isCompleted && "line-through text-muted-foreground"
          )}
        >
          {task.content}
        </span>
      </div>

      {/* Due date column */}
      <div>
        {dateInfo && (
          <span
            className={cn(
              "text-xs flex items-center gap-1",
              task.isCompleted ? "text-muted-foreground" : dateInfo.color
            )}
          >
            <Calendar className="h-3 w-3" />
            {dateInfo.label}
          </span>
        )}
      </div>

      {/* Status column */}
      <div>
        <span className={cn("inline-flex rounded-md border px-2 py-0.5 text-xs font-medium", priorityClass)}>
          {task.priority === "high" ? "High" : task.priority === "low" ? "Low" : "Medium"}
        </span>
      </div>

      {/* Person column */}
      <div className="min-w-0" onClick={(e) => e.stopPropagation()}>
        <TaskPersonEditor
          taskId={task.id}
          currentPerson={displayRecords[0]}
          onSave={onPersonChange}
        />
      </div>

      {/* Assigned to column */}
      <div className="min-w-0">
        {task.assignees.length > 0 && (
          <div className="flex items-center gap-1 truncate">
            {task.assignees.slice(0, 2).map((a) => (
              <button
                key={a.id}
                type="button"
                onMouseDown={(e) => e.stopPropagation()}
                onClick={(e) => {
                  e.stopPropagation();
                  onClick();
                }}
                className="text-xs text-primary hover:underline truncate text-left"
                title={`Edit Assigned to from main People list: ${a.displayName}`}
              >
                {a.displayName}
              </button>
            ))}
            {task.assignees.length > 2 && (
              <span className="text-xs text-muted-foreground">
                +{task.assignees.length - 2}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
