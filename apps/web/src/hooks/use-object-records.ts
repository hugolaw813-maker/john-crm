"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import type { FilterGroup, SortConfig } from "@openclaw-crm/shared";

interface AttributeDef {
  id: string;
  slug: string;
  title: string;
  type: string;
  isRequired: boolean;
  isMultiselect: boolean;
  options?: { id: string; title: string; color: string }[];
  statuses?: { id: string; title: string; color: string; isActive: boolean }[];
}

interface ObjectData {
  id: string;
  slug: string;
  singularName: string;
  pluralName: string;
  icon: string;
  attributes: AttributeDef[];
}

function buildColumnFilterGroup(
  attributes: AttributeDef[],
  columnFilterValues: Record<string, unknown>
): FilterGroup {
  const conditions: FilterGroup["conditions"] = [];

  for (const attr of attributes) {
    const rawValue = columnFilterValues[attr.slug];
    const value = typeof rawValue === "string" ? rawValue.trim() : rawValue;

    if (value === undefined || value === null || value === "") continue;

    switch (attr.type) {
      case "text":
      case "email_address":
      case "phone_number":
      case "domain":
      case "personal_name":
      case "location":
        conditions.push({ attribute: attr.slug, operator: "contains", value });
        break;
      case "number":
      case "currency":
      case "rating":
        conditions.push({ attribute: attr.slug, operator: "equals", value: Number(value) });
        break;
      case "date":
      case "timestamp":
      case "select":
      case "status":
      case "checkbox":
        conditions.push({ attribute: attr.slug, operator: "equals", value });
        break;
      default:
        break;
    }
  }

  return {
    operator: "and",
    conditions,
  };
}

interface RecordRow {
  id: string;
  values: Record<string, unknown>;
}

const EMPTY_FILTER: FilterGroup = { operator: "and", conditions: [] };

export function useObjectRecords(slug: string, columnFilterValues: Record<string, unknown> = {}) {
  const [object, setObject] = useState<ObjectData | null>(null);
  const [records, setRecords] = useState<RecordRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Search, filter & sort state
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [filter, setFilter] = useState<FilterGroup>(EMPTY_FILTER);
  const [sorts, setSorts] = useState<SortConfig[]>([]);

  const autoFilter = useMemo(
    () => buildColumnFilterGroup(object?.attributes ?? [], columnFilterValues),
    [object?.attributes, columnFilterValues]
  );

  // Track whether search/filter/sort have active values
  const hasSearch = debouncedSearch.trim().length > 0;
  const hasFilter = filter.conditions.length > 0;
  const hasSort = sorts.length > 0;

  // Fetch object definition once per slug change
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await fetch(`/api/v1/objects/${slug}`);
      if (res.ok && !cancelled) {
        const data = await res.json();
        setObject(data.data);
      }
    })();
    return () => { cancelled = true; };
  }, [slug]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 200);

    return () => window.clearTimeout(timer);
  }, [search]);

  // Fetch records when slug, search, filter, or sorts change
  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      let recData: any;
      const effectiveFilter =
        hasFilter && autoFilter.conditions.length > 0
          ? { operator: "and" as const, conditions: [filter, autoFilter] }
          : hasFilter
            ? filter
            : autoFilter.conditions.length > 0
              ? autoFilter
              : undefined;

      if (hasFilter || hasSort || hasSearch || autoFilter.conditions.length > 0) {
        const queryRes = await fetch(`/api/v1/objects/${slug}/records/query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            limit: 200,
            ...(hasSearch ? { search: debouncedSearch } : {}),
            ...(effectiveFilter ? { filter: effectiveFilter } : {}),
            ...(hasSort ? { sorts } : {}),
          }),
        });
        if (queryRes.ok) {
          recData = await queryRes.json();
        }
      } else {
        const params = new URLSearchParams({ limit: "200" });
        const recRes = await fetch(`/api/v1/objects/${slug}/records?${params.toString()}`);
        if (recRes.ok) {
          recData = await recRes.json();
        }
      }

      if (recData) {
        setRecords(recData.data.records);
        setTotal(recData.data.pagination.total);
      }
    } finally {
      setLoading(false);
    }
  }, [slug, filter, sorts, debouncedSearch, hasSearch, hasFilter, hasSort, autoFilter]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const updateRecord = useCallback(
    async (recordId: string, attrSlug: string, value: unknown) => {
      setRecords((prev) =>
        prev.map((r) =>
          r.id === recordId
            ? { ...r, values: { ...r.values, [attrSlug]: value } }
            : r
        )
      );

      await fetch(`/api/v1/objects/${slug}/records/${recordId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ values: { [attrSlug]: value } }),
      });
    },
    [slug]
  );

  const createRecord = useCallback(
    async (values: Record<string, unknown>) => {
      const res = await fetch(`/api/v1/objects/${slug}/records`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ values }),
      });

      if (res.ok) {
        fetchRecords();
      }
    },
    [slug, fetchRecords]
  );

  // Filter helpers
  const removeFilterCondition = useCallback(
    (index: number) => {
      setFilter((prev) => ({
        ...prev,
        conditions: prev.conditions.filter((_, i) => i !== index),
      }));
    },
    []
  );

  const clearFilters = useCallback(() => {
    setFilter(EMPTY_FILTER);
  }, []);

  const clearSorts = useCallback(() => {
    setSorts([]);
  }, []);

  return {
    object,
    records,
    total,
    loading,
    fetchData: fetchRecords,
    updateRecord,
    createRecord,
    setRecords,
    // Search/filter/sort
    search,
    setSearch,
    hasSearch,
    filter,
    setFilter,
    sorts,
    setSorts,
    hasFilter,
    hasSort,
    removeFilterCondition,
    clearFilters,
    clearSorts,
  };
}
