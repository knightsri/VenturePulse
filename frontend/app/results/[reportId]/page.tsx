'use client';

import { useParams, useRouter } from 'next/navigation';
import { Navigation } from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { getReportUrl } from '@/lib/api';

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.reportId as string;

  const handleDownload = (format: 'html' | 'zip') => {
    const url = getReportUrl(reportId, format);
    window.open(url, '_blank');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analysis Report</h1>
            <p className="mt-1 text-sm text-gray-500">Report ID: {reportId}</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => handleDownload('html')}>
              Download HTML
            </Button>
            <Button variant="outline" onClick={() => handleDownload('zip')}>
              Download ZIP
            </Button>
            <Button variant="outline" onClick={() => router.push('/dashboard')}>
              Back to Dashboard
            </Button>
          </div>
        </div>

        {/* Report iframe */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden" style={{ height: 'calc(100vh - 250px)' }}>
          <iframe
            src={getReportUrl(reportId, 'html')}
            className="w-full h-full border-0"
            title="Analysis Report"
          />
        </div>
      </div>
    </div>
  );
}
