import { pgTable, text, timestamp, jsonb, index } from "drizzle-orm/pg-core";
import { records } from "./records";
import { users } from "./auth";

export const notes = pgTable(
  "notes",
  {
    id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
    recordId: text("record_id")
      .notNull()
      .references(() => records.id, { onDelete: "cascade" }),
    noteType: text("note_type").notNull().default("note"),
    noteDate: timestamp("note_date").notNull().defaultNow(),
    title: text("title").notNull().default(""),
    content: jsonb("content"), // TipTap JSON format
    linkedTaskId: text("linked_task_id"),
    createdBy: text("created_by").references(() => users.id, { onDelete: "set null" }),
    createdAt: timestamp("created_at").notNull().defaultNow(),
    updatedAt: timestamp("updated_at").notNull().defaultNow(),
  },
  (table) => [
    index("notes_record_id").on(table.recordId),
  ]
);
