import { NextRequest } from "next/server";
import { getAuthContext, unauthorized, requireAdmin, success, badRequest } from "@/lib/api-utils";
import { db } from "@/db";
import { workspaces } from "@/db/schema";
import { eq } from "drizzle-orm";

interface WorkspaceSettings {
  aiProvider?: "openrouter" | "openai";
  openrouterApiKey?: string;
  openrouterModel?: string;
  openaiApiKey?: string;
  openaiModel?: string;
}

export async function GET(req: NextRequest) {
  const ctx = await getAuthContext(req);
  if (!ctx) return unauthorized();

  const [workspace] = await db
    .select({ settings: workspaces.settings })
    .from(workspaces)
    .where(eq(workspaces.id, ctx.workspaceId))
    .limit(1);

  const settings = (workspace?.settings ?? {}) as WorkspaceSettings;

  const provider = settings.aiProvider || "openrouter";

  return success({
    provider,
    model:
      provider === "openai"
        ? settings.openaiModel || "gpt-4o"
        : settings.openrouterModel || "anthropic/claude-sonnet-4",
    hasApiKey:
      provider === "openai"
        ? !!settings.openaiApiKey
        : !!settings.openrouterApiKey,
  });
}

export async function PATCH(req: NextRequest) {
  const ctx = await getAuthContext(req);
  if (!ctx) return unauthorized();

  const adminCheck = requireAdmin(ctx);
  if (adminCheck) return adminCheck;

  const body = await req.json();
  const { provider, apiKey, model } = body as {
    provider?: "openrouter" | "openai";
    apiKey?: string;
    model?: string;
  };

  if (!provider && !apiKey && !model) {
    return badRequest("Provide provider, apiKey, or model");
  }

  const [workspace] = await db
    .select({ settings: workspaces.settings })
    .from(workspaces)
    .where(eq(workspaces.id, ctx.workspaceId))
    .limit(1);

  const current = (workspace?.settings ?? {}) as WorkspaceSettings;
  const updated: WorkspaceSettings = { ...current };

  const nextProvider = provider || current.aiProvider || "openrouter";
  updated.aiProvider = nextProvider;

  if (nextProvider === "openai") {
    if (apiKey !== undefined) updated.openaiApiKey = apiKey;
    if (model !== undefined) updated.openaiModel = model;
  } else {
    if (apiKey !== undefined) updated.openrouterApiKey = apiKey;
    if (model !== undefined) updated.openrouterModel = model;
  }

  await db
    .update(workspaces)
    .set({ settings: updated, updatedAt: new Date() })
    .where(eq(workspaces.id, ctx.workspaceId));

  return success({
    provider: nextProvider,
    model:
      nextProvider === "openai"
        ? updated.openaiModel || "gpt-4o"
        : updated.openrouterModel || "anthropic/claude-sonnet-4",
    hasApiKey:
      nextProvider === "openai"
        ? !!updated.openaiApiKey
        : !!updated.openrouterApiKey,
  });
}
