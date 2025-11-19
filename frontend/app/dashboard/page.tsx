'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navigation } from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { fetchReports, deleteReport, type ReportMetadata } from '@/lib/api';
import { format } from 'date-fns';

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch reports
  const { data: reports, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: fetchReports,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });

  const handleDelete = async (reportId: string) => {
    if (confirm('Are you sure you want to delete this report?')) {
      deleteMutation.mutate(reportId);
    }
  };

  // Filter reports
  const filteredReports = reports?.filter((report) =>
    report.projectName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    report.model.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-lg text-gray-600">
            View and manage all your generated reports
          </p>
        </div>

        {/* Search and Actions */}
        <div className="mb-6 flex gap-4">
          <Input
            placeholder="Search by project name or model..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-md"
          />
          <Button onClick={() => router.push('/analyze')}>
            New Analysis
          </Button>
        </div>

        {/* Reports List */}
        {isLoading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading reports...</p>
          </div>
        ) : filteredReports.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <p className="text-lg text-gray-500 mb-4">
                  {searchQuery ? 'No reports match your search' : 'No reports yet'}
                </p>
                {!searchQuery && (
                  <Button onClick={() => router.push('/analyze')}>
                    Create Your First Analysis
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredReports.map((report) => (
              <Card key={report.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        {report.projectName}
                      </h3>
                      <div className="flex items-center gap-3 mb-2">
                        <Badge variant="secondary">{report.model}</Badge>
                        <Badge
                          variant={report.status === 'completed' ? 'success' : 'warning'}
                        >
                          {report.status}
                        </Badge>
                        <span className="text-sm text-gray-500">
                          {format(new Date(report.createdAt), 'MMM d, yyyy h:mm a')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">Report ID: {report.id}</p>
                    </div>
                    <div className="flex gap-2">
                      {report.status === 'completed' && (
                        <>
                          <Button
                            variant="default"
                            onClick={() => router.push(`/results/${report.id}`)}
                          >
                            View
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => window.open(`/api/reports/${report.id}?format=zip`, '_blank')}
                          >
                            Download
                          </Button>
                        </>
                      )}
                      <Button
                        variant="destructive"
                        onClick={() => handleDelete(report.id)}
                        disabled={deleteMutation.isPending}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Summary */}
        {!isLoading && reports && reports.length > 0 && (
          <div className="mt-8 text-center text-sm text-gray-500">
            Showing {filteredReports.length} of {reports.length} report(s)
          </div>
        )}
      </div>
    </div>
  );
}
