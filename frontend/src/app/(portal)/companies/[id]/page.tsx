import { CompanyDetailPage } from "@/features/companyDetail";

export default async function CompanyDetailRoute({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <CompanyDetailPage company_id={id} />;
}
