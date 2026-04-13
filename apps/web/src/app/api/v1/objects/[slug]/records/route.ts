import { NextRequest } from "next/server";
import { getAuthContext, unauthorized, notFound, badRequest, success } from "@/lib/api-utils";
import { getObjectBySlug } from "@/services/objects";
import { listRecords, createRecord } from "@/services/records";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const ctx = await getAuthContext(req);
  if (!ctx) return unauthorized();

  const { slug } = await params;
  const obj = await getObjectBySlug(ctx.workspaceId, slug);
  if (!obj) return notFound("Object not found");

  const { searchParams } = new URL(req.url);
  const limit = Math.min(Number(searchParams.get("limit") || 50), 200);
  const offset = Number(searchParams.get("offset") || 0);
  const search = searchParams.get("search") || undefined;

  const result = await listRecords(obj.id, { limit, offset, search });

  return success({
    records: result.records,
    pagination: { limit, offset, total: result.total },
  });
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const ctx = await getAuthContext(req);
  if (!ctx) return unauthorized();

  const { slug } = await params;
  const obj = await getObjectBySlug(ctx.workspaceId, slug);
  if (!obj) return notFound("Object not found");

  try {
    const body = await req.json();
    console.log('[DEBUG API POST] body:', JSON.stringify(body));
    const { values } = body;

    if (!values || typeof values !== "object") {
      return badRequest("values object is required");
    }

    console.log('[DEBUG API POST] creating record with values:', JSON.stringify(values));
    const record = await createRecord(obj.id, values, ctx.userId);
    console.log('[DEBUG API POST] record created:', record.id);
    return success(record, 201);
  } catch (error: any) {
    console.error('[DEBUG API POST] error:', error);
    console.error('[DEBUG API POST] error stack:', error.stack);
    return new Response(JSON.stringify({ error: error.message, stack: error.stack }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
