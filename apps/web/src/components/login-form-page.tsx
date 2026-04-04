"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState, useTransition } from "react";

import { SiteBrand } from "@/components/site-brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { login } from "@/lib/api";

type LoginFormPageProps = {
  nextPath: string | null;
};

export function LoginFormPage({ nextPath }: LoginFormPageProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    startTransition(() => {
      void (async () => {
        try {
          const user = await login(email, password);
          router.push(user.must_change_password ? "/profile" : (nextPath ?? "/competitions"));
          router.refresh();
        } catch (loginError) {
          setError(
            loginError instanceof Error
              ? loginError.message
              : "Login failed.",
          );
        }
      })();
    });
  }

  return (
    <main className="min-h-screen bg-white text-slate-950 md:grid md:grid-cols-2">
      <section className="relative hidden bg-[#f3f3f3] md:block">
        <div className="px-8 py-8">
          <SiteBrand />
        </div>
        <p className="absolute bottom-8 left-8 text-xs text-black">Very Nice</p>
      </section>

      <section className="relative flex min-h-screen items-center justify-center px-6 py-8">
        <div className="absolute left-6 top-8 md:hidden">
          <SiteBrand />
        </div>
        <div className="w-full max-w-[350px]">
          <div className="text-center">
            <h1 className="text-[2rem] font-semibold tracking-[-0.04em] text-black">
              Login
            </h1>
            <p className="mt-2 text-sm text-[#777777]">
              Enter your email and password below to login
            </p>
          </div>
          <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <Input
                className="h-9 rounded-md border-[#ebebeb] bg-white px-3 text-xs shadow-none placeholder:text-[#b1b1b1] focus-visible:ring-1"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="name@example.com"
                type="email"
                value={email}
              />
              <Input
                className="h-9 rounded-md border-[#ebebeb] bg-white px-3 text-xs shadow-none placeholder:text-[#b1b1b1] focus-visible:ring-1"
                onChange={(event) => setPassword(event.target.value)}
                placeholder="password"
                type="password"
                value={password}
              />
            </div>

            {error ? (
              <p className="text-center text-xs text-[#b14d4d]">{error}</p>
            ) : null}

            <Button className="h-9 w-full rounded-md bg-[#1f1f1f] text-xs font-semibold hover:bg-[#111111]">
              {isPending ? "Logging in..." : "Login"}
            </Button>
          </form>
        </div>
      </section>
    </main>
  );
}
