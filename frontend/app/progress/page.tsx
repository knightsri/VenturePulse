'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Navigation } from '@/components/Navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { streamJobProgress, type JobProgress } from '@/lib/api';

interface JobState {
  jobId: string;
  status: 'waiting' | 'active' | 'completed' | 'failed';
  progress?: JobProgress;
  reportPath?: string;
  error?: string;
}

export default function ProgressPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobsParam = searchParams.get('jobs');
  const jobIds = jobsParam ? jobsParam.split(',') : [];

  const [jobs, setJobs] = useState<Record<string, JobState>>({});
  const [allCompleted, setAllCompleted] = useState(false);

  useEffect(() => {
    if (jobIds.length === 0) {
      router.push('/');
      return;
    }

    // Initialize job states
    const initialJobs: Record<string, JobState> = {};
    jobIds.forEach((jobId) => {
      initialJobs[jobId] = {
        jobId,
        status: 'waiting',
      };
    });
    setJobs(initialJobs);

    // Set up SSE streams for each job
    const cleanupFunctions: (() => void)[] = [];

    jobIds.forEach((jobId) => {
      const cleanup = streamJobProgress(
        jobId,
        (progress) => {
          setJobs((prev) => ({
            ...prev,
            [jobId]: {
              ...prev[jobId],
              status: 'active',
              progress,
            },
          }));
        },
        (reportPath) => {
          setJobs((prev) => ({
            ...prev,
            [jobId]: {
              ...prev[jobId],
              status: 'completed',
              reportPath,
            },
          }));
        },
        (error) => {
          setJobs((prev) => ({
            ...prev,
            [jobId]: {
              ...prev[jobId],
              status: 'failed',
              error,
            },
          }));
        }
      );

      cleanupFunctions.push(cleanup);
    });

    return () => {
      cleanupFunctions.forEach((cleanup) => cleanup());
    };
  }, [jobsParam, router]);

  useEffect(() => {
    // Check if all jobs are completed
    const completed = Object.values(jobs).every(
      (job) => job.status === 'completed' || job.status === 'failed'
    );

    if (completed && Object.keys(jobs).length > 0) {
      setAllCompleted(true);
    }
  }, [jobs]);

  const handleViewReports = () => {
    // Get the first completed report
    const completedJob = Object.values(jobs).find((job) => job.status === 'completed');
    if (completedJob?.reportPath) {
      const reportId = completedJob.reportPath.split('/').pop();
      router.push(`/results/${reportId}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Analysis in Progress</h1>
          <p className="mt-2 text-lg text-gray-600">
            {allCompleted
              ? 'All analyses complete!'
              : 'Generating comprehensive reports... This may take 10-15 minutes per model.'}
          </p>
        </div>

        <div className="space-y-6">
          {Object.values(jobs).map((job) => (
            <Card key={job.jobId}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl">
                    Analysis Job {job.jobId.substring(0, 8)}
                  </CardTitle>
                  <Badge
                    variant={
                      job.status === 'completed'
                        ? 'success'
                        : job.status === 'failed'
                        ? 'destructive'
                        : job.status === 'active'
                        ? 'default'
                        : 'secondary'
                    }
                  >
                    {job.status}
                  </Badge>
                </div>
                {job.progress && (
                  <CardDescription>
                    Section {job.progress.currentSection} of {job.progress.totalSections}:{' '}
                    {job.progress.sectionName}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                {job.status === 'active' && job.progress && (
                  <div className="space-y-2">
                    <Progress value={job.progress.percentage} />
                    <p className="text-sm text-gray-600 text-right">
                      {job.progress.percentage}% complete
                    </p>
                  </div>
                )}

                {job.status === 'completed' && (
                  <div className="text-center py-4">
                    <p className="text-green-600 font-medium">✓ Report generated successfully!</p>
                  </div>
                )}

                {job.status === 'failed' && (
                  <div className="text-center py-4">
                    <p className="text-red-600 font-medium">✗ Analysis failed</p>
                    {job.error && <p className="text-sm text-gray-600 mt-1">{job.error}</p>}
                  </div>
                )}

                {job.status === 'waiting' && (
                  <div className="text-center py-4">
                    <p className="text-gray-500">Waiting to start...</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {allCompleted && (
          <div className="mt-8 flex justify-center gap-4">
            <Button onClick={handleViewReports} size="lg">
              View Reports
            </Button>
            <Button variant="outline" onClick={() => router.push('/dashboard')} size="lg">
              Go to Dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
