"use client";

import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Stack,
  Typography,
} from "@mui/material";

import { useCompanyDetail, useGenerateReport } from "../hooks";

interface CompanyDetailPageProps {
  company_id: string;
}

export function CompanyDetailPage({ company_id }: CompanyDetailPageProps) {
  const { data, isLoading, isError, error } = useCompanyDetail(company_id);
  const { mutate: generateReportMutate, isPending: isGenerating } =
    useGenerateReport();

  const handleGenerateReport = () => {
    generateReportMutate({ companyId: company_id, format: "pdf" });
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    return (
      <Box p={2}>
        <Typography color="error">
          エラーが発生しました: {error?.message}
        </Typography>
      </Box>
    );
  }

  if (!data) {
    return (
      <Box p={2}>
        <Typography color="text.secondary">データが見つかりません</Typography>
      </Box>
    );
  }

  const { securities_code, name, industry, market_cap, scoring, financial, signals_support, signals_counter } = data;

  return (
    <Box sx={{ p: 4 }}>
      {/* 企業ヘッダ */}
      <Box sx={{ mb: 3 }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="flex-start"
        >
          <Box>
            <Typography variant="h4" fontWeight="bold">
              {name}
            </Typography>
            <Typography color="text.secondary">
              証券コード: {securities_code}
            </Typography>
            {industry && (
              <Typography color="text.secondary">業種: {industry}</Typography>
            )}
            {market_cap !== null && market_cap !== undefined && (
              <Typography color="text.secondary">
                時価総額: {(market_cap / 1_000_000_000).toFixed(1)}十億円
              </Typography>
            )}
          </Box>
          <Button
            variant="contained"
            onClick={handleGenerateReport}
            disabled={isGenerating}
            aria-label="PDFレポートを出力"
          >
            PDFレポートを出力
          </Button>
        </Stack>
      </Box>

      {/* スコアカード */}
      {scoring && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              総合スコア
            </Typography>
            <Typography variant="h3" fontWeight="bold" color="primary.main">
              {scoring.total_score}
            </Typography>
            <Divider sx={{ my: 1 }} />
            <Stack spacing={1}>
              <Typography>
                構造スコア: {scoring.structure_score}
              </Typography>
              <Typography>
                イベントスコア: {scoring.event_score}
              </Typography>
              <Typography>
                確信度: {scoring.confidence}
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* 財務データ */}
      {financial && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              定量指標
            </Typography>
            <Stack spacing={1}>
              {financial.pbr !== null && financial.pbr !== undefined && (
                <Typography>PBR: {financial.pbr}</Typography>
              )}
              {financial.unrealized_gain !== null && financial.unrealized_gain !== undefined && (
                <Typography>
                  含み益: {(financial.unrealized_gain / 1_000_000_000).toFixed(1)}十億円
                </Typography>
              )}
              {financial.roic_wacc_gap !== null &&
                financial.roic_wacc_gap !== undefined &&
                financial.roic_wacc_gap < 0 && (
                  <Box sx={{ mt: 1, p: 1, bgcolor: "warning.light", borderRadius: 1 }}>
                    <Typography>
                      ROIC: {financial.roic !== null && financial.roic !== undefined ? (financial.roic * 100).toFixed(1) : "-"}%
                      {"  "}
                      WACC: {financial.wacc !== null && financial.wacc !== undefined ? (financial.wacc * 100).toFixed(1) : "-"}%
                      {"  "}
                      売却合理性あり
                    </Typography>
                  </Box>
                )}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* 定性シグナル（売却支持） */}
      {signals_support && signals_support.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            売却支持シグナル
          </Typography>
          <Stack spacing={2}>
            {signals_support.map((signal) => (
              <Card key={signal.signal_id} variant="outlined">
                <CardContent>
                  <Typography>{signal.quote_text}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    シグナルタイプ: {signal.signal_type} / ページ: {signal.source_page}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Box>
      )}

      {/* 定性シグナル（反対） */}
      {signals_counter && signals_counter.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            売却反対シグナル
          </Typography>
          <Stack spacing={2}>
            {signals_counter.map((signal) => (
              <Card key={signal.signal_id} variant="outlined">
                <CardContent>
                  <Typography>{signal.quote_text}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    シグナルタイプ: {signal.signal_type} / ページ: {signal.source_page}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Box>
      )}

      {/* AI判定 */}
      {scoring?.ai_judgment && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              AI判定
            </Typography>
            <Typography>{scoring.ai_judgment}</Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
