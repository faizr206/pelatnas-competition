import { CompetitionWorkspace } from "@/components/competition-workspace";

type CompetitionPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function CompetitionPage({
  params,
}: CompetitionPageProps) {
  const { slug } = await params;
  return <CompetitionWorkspace slug={slug} />;
}
