import { NextRequest } from "next/server";
import { getAuthContext, unauthorized, success, badRequest } from "@/lib/api-utils";
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

export async function POST(req: NextRequest) {
  const ctx = await getAuthContext(req);
  if (!ctx) return unauthorized();

  const body = await req.json();
  let { provider, apiKey, model } = body as {
    provider?: "openrouter" | "openai";
    apiKey?: string;
    model?: string;
  };

  // If no key provided in request, use the stored one
  if (!apiKey || !provider || !model) {
    const [workspace] = await db
      .select({ settings: workspaces.settings })
      .from(workspaces)
      .where(eq(workspaces.id, ctx.workspaceId))
      .limit(1);

    const settings = (workspace?.settings ?? {}) as WorkspaceSettings;
    provider = provider || settings.aiProvider || "openrouter";
    if (provider === "openai") {
      apiKey = apiKey || settings.openaiApiKey;
      model = model || settings.openaiModel || "gpt-4o";
    } else {
      apiKey = apiKey || settings.openrouterApiKey;
      model = model || settings.openrouterModel || "anthropic/claude-sonnet-4";
    }
  }

  if (!apiKey) {
    return badRequest("No API key configured");
  }

  if (!provider) provider = "openrouter";
  if (!model) model = provider === "openai" ? "gpt-4o" : "anthropic/claude-sonnet-4";

  try {
    const res = await fetch(
      provider === "openai"
        ? "https://api.openai.com/v1/chat/completions"
        : "https://openrouter.ai/api/v1/chat/completions",
      {
        method: "POST",
        headers:
          provider === "openai"
            ? {
                Authorization: `Bearer ${apiKey}`,
                "Content-Type": "application/json",
              }
            : {
                Authorization: `Bearer ${apiKey}`,
                "Content-Type": "application/json",
                "HTTP-Referer": process.env.BETTER_AUTH_URL || "http://localhost:3001",
              },
      body: JSON.stringify({
        model,
        messages: [{ role: "user", content: "Say hello in one word." }],
        max_tokens: 10,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return success({
        success: false,
        error: (err as { error?: { message?: string } }).error?.message || `HTTP ${res.status}`,
      });
    }

    return success({ success: true });
  } catch (e) {
    return success({
      success: false,
      error: e instanceof Error ? e.message : "Connection failed",
    });
  }
}
