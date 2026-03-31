import { AdminEditCompetitionPage } from "@/components/admin-edit-competition-page";

type AdminEditCompetitionRouteProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function AdminEditCompetitionRoute({
  params,
}: AdminEditCompetitionRouteProps) {
  const { slug } = await params;
  return <AdminEditCompetitionPage slug={slug} />;
}
