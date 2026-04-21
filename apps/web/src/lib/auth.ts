import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "@/db";
import * as schema from "@/db/schema";

const appBaseUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3001";
const baseOrigin = (() => {
  try {
    return new URL(appBaseUrl).origin;
  } catch {
    return appBaseUrl;
  }
})();
const trustedOrigins = Array.from(
  new Set([
    baseOrigin,
    ...(process.env.TRUSTED_ORIGINS || "").split(",").filter(Boolean),
  ]),
);

export const auth = betterAuth({
  baseURL: appBaseUrl,
  secret: process.env.BETTER_AUTH_SECRET,
  trustedOrigins,
  advanced: {
    disableCSRFCheck: true,
  },
  database: drizzleAdapter(db, {
    provider: "pg",
    schema: {
      user: schema.users,
      session: schema.sessions,
      account: schema.accounts,
      verification: schema.verifications,
    },
  }),
  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false,
    autoSignIn: true,
  },
  emailVerification: {
    sendOnSignUp: false,
    autoSignInAfterVerification: false,
    sendVerificationEmail: async () => {
      return;
    },
  },
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID || "",
      clientSecret: process.env.GITHUB_CLIENT_SECRET || "",
      enabled: !!(process.env.GITHUB_CLIENT_ID && process.env.GITHUB_CLIENT_SECRET),
    },
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
      enabled: !!(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET),
    },
  },
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day
  },
});

export type Session = typeof auth.$Infer.Session;
