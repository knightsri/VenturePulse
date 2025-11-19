'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Navigation } from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { fetchModels, submitAnalysis, type OpenRouterModel } from '@/lib/api';
import { useDropzone } from 'react-dropzone';

export default function AnalyzePage() {
  const router = useRouter();
  const [projectName, setProjectName] = useState('');
  const [projectContent, setProjectContent] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [inputMode, setInputMode] = useState<'text' | 'file'>('text');

  // Fetch models
  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ['models'],
    queryFn: fetchModels,
  });

  // Submit analysis mutation
  const submitMutation = useMutation({
    mutationFn: submitAnalysis,
    onSuccess: (data) => {
      // Redirect to progress page with all job IDs
      router.push(`/progress?jobs=${data.jobIds.join(',')}`);
    },
  });

  // File dropzone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setUploadedFile(acceptedFiles[0]);
        setInputMode('file');
      }
    },
    accept: {
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleToggleModel = (modelId: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelId) ? prev.filter((id) => id !== modelId) : [...prev, modelId]
    );
  };

  const handleSubmit = async () => {
    if (!projectName) {
      alert('Please enter a project name');
      return;
    }

    if (selectedModels.length === 0) {
      alert('Please select at least one model');
      return;
    }

    if (inputMode === 'file' && !uploadedFile) {
      alert('Please upload a file');
      return;
    }

    if (inputMode === 'text' && projectContent.length < 100) {
      alert('Please enter at least 100 characters of project content');
      return;
    }

    submitMutation.mutate({
      projectName,
      projectContent: inputMode === 'text' ? projectContent : undefined,
      file: inputMode === 'file' ? uploadedFile! : undefined,
      models: selectedModels,
    });
  };

  // Calculate total cost
  const totalCost = models
    ? selectedModels.reduce((sum, modelId) => {
        const model = models.find((m) => m.id === modelId);
        return sum + (model?.estimatedCost || 0);
      }, 0)
    : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">New Analysis</h1>
          <p className="mt-2 text-lg text-gray-600">
            Upload your project description or paste it below, then select AI models to analyze it.
          </p>
        </div>

        {/* Step 1: Project Information */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Step 1: Project Information</CardTitle>
            <CardDescription>Provide your project name and description</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Project Name *
              </label>
              <Input
                placeholder="e.g., SmartPlate - AI Meal Planning App"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
              />
            </div>

            <div>
              <div className="flex gap-4 mb-4">
                <Button
                  variant={inputMode === 'text' ? 'default' : 'outline'}
                  onClick={() => setInputMode('text')}
                >
                  Paste Text
                </Button>
                <Button
                  variant={inputMode === 'file' ? 'default' : 'outline'}
                  onClick={() => setInputMode('file')}
                >
                  Upload File
                </Button>
              </div>

              {inputMode === 'text' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project Description * (min 100 characters)
                  </label>
                  <Textarea
                    placeholder="Describe your product idea in detail. Include the problem you're solving, target audience, key features, business model, etc."
                    className="min-h-[200px]"
                    value={projectContent}
                    onChange={(e) => setProjectContent(e.target.value)}
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    {projectContent.length} characters
                  </p>
                </div>
              ) : (
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                    isDragActive
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-gray-300 hover:border-indigo-500'
                  }`}
                >
                  <input {...getInputProps()} />
                  {uploadedFile ? (
                    <div>
                      <p className="text-lg font-medium text-gray-900">{uploadedFile.name}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {(uploadedFile.size / 1024).toFixed(2)} KB
                      </p>
                      <Button
                        variant="outline"
                        className="mt-4"
                        onClick={(e) => {
                          e.stopPropagation();
                          setUploadedFile(null);
                        }}
                      >
                        Remove File
                      </Button>
                    </div>
                  ) : (
                    <div>
                      <p className="text-lg font-medium text-gray-900">
                        {isDragActive ? 'Drop file here' : 'Drag & drop file here'}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        or click to select (.txt, .md, .docx, .pdf, max 10MB)
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Step 2: Model Selection */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Step 2: Select AI Models</CardTitle>
            <CardDescription>
              Choose one or more models to analyze your project. Each model provides unique insights.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {modelsLoading ? (
              <div className="text-center py-8">Loading models...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {models?.slice(0, 10).map((model) => (
                  <div
                    key={model.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedModels.includes(model.id)
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-indigo-300'
                    }`}
                    onClick={() => handleToggleModel(model.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{model.name}</h4>
                        <p className="text-sm text-gray-500">{model.provider}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedModels.includes(model.id)}
                        onChange={() => handleToggleModel(model.id)}
                        className="mt-1"
                      />
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      {model.estimatedCost === 0 ? (
                        <Badge variant="success">Free</Badge>
                      ) : (
                        <Badge variant="secondary">${model.estimatedCost.toFixed(2)}</Badge>
                      )}
                      {model.speed && (
                        <Badge variant="outline">{model.speed}</Badge>
                      )}
                      {model.recommended && (
                        <Badge variant="default">Recommended</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {selectedModels.length > 0 && (
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium text-gray-700">
                      {selectedModels.length} model(s) selected
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      Estimated time: {selectedModels.length * 15} minutes
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-gray-900">
                      ${totalCost.toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-500">Total cost</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Submit Button */}
        <div className="flex justify-end gap-4">
          <Button variant="outline" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={submitMutation.isPending}
          >
            {submitMutation.isPending ? 'Submitting...' : 'Start Analysis'}
          </Button>
        </div>

        {submitMutation.isError && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">
              Error: {(submitMutation.error as Error).message}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
