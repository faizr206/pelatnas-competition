import { LoginFormPage } from "@/components/login-form-page";

type LoginPageProps = {
  searchParams?: Promise<{
    next?: string;
  }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;

  return <LoginFormPage nextPath={resolvedSearchParams?.next ?? null} />;
}
