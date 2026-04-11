"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from "@tanstack/react-table";
import type { AttributeType, SortConfig } from "@openclaw-crm/shared";
import { AttributeCell } from "./attribute-cell";
import { AttributeEditor } from "./attribute-editor";
import { Plus, ExternalLink, ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface AttributeDef {
  id: string;
  slug: string;
  title: string;
  type: AttributeType;
  isMultiselect: boolean;
  options?: { id: string; title: string; color: string }[];
  statuses?: { id: string; title: string; color: string; isActive: boolean }[];
}

interface RecordRow {
  id: string;
  values: Record<string, unknown>;
}

interface RecordTableProps {
  attributes: AttributeDef[];
  records: RecordRow[];
  onUpdateRecord: (recordId: string, slug: string, value: unknown) => void;
  onCreateRecord: () => void;
  onColumnFilterChange: (slug: string, value: unknown) => void;
  onColumnSortToggle: (slug: string) => void;
  columnFilterValues: Record<string, unknown>;
  sorts: SortConfig[];
  objectSlug: string;
}

export function RecordTable({
  attributes,
  records,
  onUpdateRecord,
  onCreateRecord,
  onColumnFilterChange,
  onColumnSortToggle,
  columnFilterValues,
  sorts,
  objectSlug,
}: RecordTableProps) {
  const router = useRouter();
  const [editingCell, setEditingCell] = useState<{ rowId: string; colId: string } | null>(null);

  const columns = useMemo<ColumnDef<RecordRow>[]>(() => {
    const openCol: ColumnDef<RecordRow> = {
      id: "_open",
      header: "",
      size: 40,
      cell: ({ row }) => (
        <button
          onClick={() => router.push(`/objects/${objectSlug}/${row.original.id}`)}
          className="flex items-center justify-center opacity-0 group-hover/row:opacity-100 transition-opacity"
        >
          <ExternalLink className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
        </button>
      ),
    };

    const attrCols: ColumnDef<RecordRow>[] = attributes.map((attr) => ({
      id: attr.slug,
      header: attr.title,
      size: attr.type === "personal_name" ? 200 : attr.type === "text" ? 180 : 150,
      cell: ({ row }: { row: { original: RecordRow; id: string } }) => {
        const val = row.original.values[attr.slug];
        const isEditing =
          editingCell?.rowId === row.original.id &&
          editingCell?.colId === attr.slug;

        if (isEditing) {
          return (
            <div className="relative">
              <AttributeEditor
                type={attr.type}
                value={val}
                options={attr.options}
                statuses={attr.statuses}
                onSave={(newVal) => {
                  onUpdateRecord(row.original.id, attr.slug, newVal);
                  setEditingCell(null);
                }}
                onCancel={() => setEditingCell(null)}
              />
            </div>
          );
        }

        return (
          <div
            className="cursor-pointer truncate px-1"
            onClick={() =>
              setEditingCell({ rowId: row.original.id, colId: attr.slug })
            }
          >
            <AttributeCell
              type={attr.type}
              value={val}
              options={attr.options}
              statuses={attr.statuses}
            />
          </div>
        );
      },
    }));

    return [openCol, ...attrCols];
  }, [attributes, editingCell, onUpdateRecord, objectSlug, router]);

  const table = useReactTable({
    data: records,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getRowId: (row) => row.id,
  });

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10 bg-background">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-border align-top">
                {headerGroup.headers.map((header) => {
                  const currentSort = sorts.find((sort) => sort.attribute === header.id);
                  return (
                    <th
                      key={header.id}
                      className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
                      style={{ width: header.getSize() }}
                    >
                      {header.id === "_open" ? (
                        <div>{flexRender(header.column.columnDef.header, header.getContext())}</div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => onColumnSortToggle(header.id)}
                          className="flex items-center gap-1 hover:text-foreground"
                        >
                          <span>{flexRender(header.column.columnDef.header, header.getContext())}</span>
                          {currentSort ? (
                            currentSort.direction === "asc" ? (
                              <ArrowUp className="h-3 w-3" />
                            ) : (
                              <ArrowDown className="h-3 w-3" />
                            )
                          ) : (
                            <ArrowUpDown className="h-3 w-3 opacity-50" />
                          )}
                        </button>
                      )}
                      {header.id !== "_open" && (
                        <div className="mt-2 normal-case">
                          {renderColumnFilter(
                            attributes.find((attr) => attr.slug === header.id),
                            columnFilterValues[header.id],
                            (value) => onColumnFilterChange(header.id, value)
                          )}
                        </div>
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="group/row border-b border-border/50 hover:bg-muted/30 transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="h-10 px-3 text-sm"
                    style={{ width: cell.column.getSize() }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
            {records.length === 0 && (
              <tr>
                <td
                  colSpan={attributes.length + 1}
                  className="h-32 text-center text-muted-foreground"
                >
                  No matching records.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="border-t border-border p-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onCreateRecord}
          className="text-muted-foreground hover:text-foreground"
        >
          <Plus className="mr-1 h-4 w-4" />
          New record
        </Button>
      </div>
    </div>
  );
}

function renderColumnFilter(
  attribute: AttributeDef | undefined,
  value: unknown,
  onChange: (value: unknown) => void
) {
  if (!attribute) return null;

  if (attribute.type === "select" && attribute.options) {
    return (
      <select
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 w-full rounded-md border border-border bg-background px-2 text-xs font-normal"
      >
        <option value="">All</option>
        {attribute.options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.title}
          </option>
        ))}
      </select>
    );
  }

  if (attribute.type === "status" && attribute.statuses) {
    return (
      <select
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 w-full rounded-md border border-border bg-background px-2 text-xs font-normal"
      >
        <option value="">All</option>
        {attribute.statuses.map((status) => (
          <option key={status.id} value={status.id}>
            {status.title}
          </option>
        ))}
      </select>
    );
  }

  if (attribute.type === "checkbox") {
    return (
      <select
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value === "" ? "" : e.target.value === "true")}
        className="h-8 w-full rounded-md border border-border bg-background px-2 text-xs font-normal"
      >
        <option value="">All</option>
        <option value="true">Yes</option>
        <option value="false">No</option>
      </select>
    );
  }

  if (
    attribute.type === "number" ||
    attribute.type === "currency" ||
    attribute.type === "rating"
  ) {
    return (
      <Input
        type="number"
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 text-xs font-normal"
        placeholder="Filter..."
      />
    );
  }

  if (attribute.type === "date" || attribute.type === "timestamp") {
    return (
      <Input
        type="date"
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 text-xs font-normal"
      />
    );
  }

  if (attribute.type === "record_reference" || attribute.type === "actor_reference") {
    return <div className="h-8" />;
  }

  return (
    <Input
      type="text"
      value={String(value ?? "")}
      onChange={(e) => onChange(e.target.value)}
      className="h-8 text-xs font-normal"
      placeholder="Filter..."
    />
  );
}
