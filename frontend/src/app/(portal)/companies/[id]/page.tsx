import { CompanyDetailPage } from "@/features/companyDetail";

export default function CompanyDetailRoute({
  params,
}: {
  params: { id: string };
}) {
  return <CompanyDetailPage company_id={params.id} />;
}
