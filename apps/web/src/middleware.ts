import { NextRequest, NextResponse } from "next/server";

const publicPaths = ["/login", "/register", "/api/auth", "/docs", "/blog", "/compare"];
const workspaceSetupPaths = ["/select-workspace", "/api/v1/workspaces"];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // TEMPORARY: Disable auth for development
  // Skip all auth checks and workspace checks
  if (process.env.DISABLE_AUTH === "true") {
    // Still need to set a dummy workspace cookie for the app to work
    const response = NextResponse.next();
    // Set a dummy active-workspace-id cookie if not present
    if (!req.cookies.get("active-workspace-id")) {
      response.cookies.set("active-workspace-id", "dev-workspace");
    }
    return response;
  }

  // Allow public paths and static assets
  if (
    publicPaths.some((p) => pathname.startsWith(p)) ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname === "/"
  ) {
    return NextResponse.next();
  }

  // Allow API requests with Bearer tokens (auth checked in getAuthContext)
  if (
    pathname.startsWith("/api/") &&
    req.headers.get("authorization")?.startsWith("Bearer ")
  ) {
    return NextResponse.next();
  }

  // Allow public API spec endpoints and SEO files without auth
  if (pathname === "/openapi.json" || pathname === "/llms.txt" || pathname === "/llms-api.txt" || pathname === "/llms-full.txt" || pathname === "/robots.txt" || pathname === "/sitemap.xml") {
    return NextResponse.next();
  }

  // Check for Better Auth session cookie
  const sessionCookie =
    req.cookies.get("better-auth.session_token") ||
    req.cookies.get("__Secure-better-auth.session_token");

  if (!sessionCookie) {
    const loginUrl = new URL("/login", req.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Allow workspace setup paths (need auth but no active workspace)
  if (workspaceSetupPaths.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Check for active workspace cookie
  const activeWorkspace = req.cookies.get("active-workspace-id");
  if (!activeWorkspace) {
    // Redirect to workspace selection
    return NextResponse.redirect(new URL("/select-workspace", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Match all paths except static files
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
