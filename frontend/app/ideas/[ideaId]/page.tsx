"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, useParams } from "next/navigation";
import {
  fetchIdea,
  updateIdea,
  deleteIdea,
  analyzeIdea,
  fetchIdeaReports,
  fetchModels,
  type UpdateIdeaRequest,
  type OpenRouterModel,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Tab = "overview" | "analyses" | "edit";

export default function IdeaDetailPage() {
  const router = useRouter();
  const params = useParams();
  const ideaId = params.ideaId as string;
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);

  // Fetch idea details
  const {
    data: idea,
    isLoading: ideaLoading,
    error: ideaError,
  } = useQuery({
    queryKey: ["idea", ideaId],
    queryFn: () => fetchIdea(ideaId),
    refetchInterval: 5000,
  });

  // Fetch reports for this idea
  const { data: reports = [] } = useQuery({
    queryKey: ["ideaReports", ideaId],
    queryFn: () => fetchIdeaReports(ideaId),
    refetchInterval: 5000,
  });

  // Fetch available models
  const { data: models = [] } = useQuery({
    queryKey: ["models"],
    queryFn: fetchModels,
  });

  // Edit form state
  const [editFormData, setEditFormData] = useState<UpdateIdeaRequest>({
    name: "",
    description: "",
    industry: "",
    targetMarket: "",
    estimatedBudget: undefined,
    tags: [],
    notes: "",
    changes: "",
  });

  // Initialize edit form when idea loads
  useState(() => {
    if (idea) {
      setEditFormData({
        name: idea.name,
        description: idea.description,
        industry: idea.industry || "",
        targetMarket: idea.targetMarket || "",
        estimatedBudget: idea.estimatedBudget,
        tags: idea.tags || [],
        notes: idea.notes || "",
        changes: "",
      });
    }
  });

  const updateMutation = useMutation({
    mutationFn: (data: UpdateIdeaRequest) => updateIdea(ideaId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["idea", ideaId] });
      setActiveTab("overview");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteIdea(ideaId),
    onSuccess: () => {
      router.push("/ideas");
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: (models: string[]) => analyzeIdea(ideaId, models),
    onSuccess: (data) => {
      setIsAnalyzing(false);
      setSelectedModels([]);
      queryClient.invalidateQueries({ queryKey: ["idea", ideaId] });
      queryClient.invalidateQueries({ queryKey: ["ideaReports", ideaId] });
      router.push(`/progress?jobs=${data.jobIds.join(",")}`);
    },
  });

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editFormData.changes.trim()) {
      alert("Please describe what changes you made");
      return;
    }
    try {
      await updateMutation.mutateAsync(editFormData);
    } catch (error) {
      alert("Failed to update idea. Please try again.");
    }
  };

  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this idea? This action cannot be undone.")) {
      try {
        await deleteMutation.mutateAsync();
      } catch (error) {
        alert("Failed to delete idea. Please try again.");
      }
    }
  };

  const handleAnalyze = async () => {
    if (selectedModels.length === 0) {
      alert("Please select at least one model");
      return;
    }
    try {
      await analyzeMutation.mutateAsync(selectedModels);
    } catch (error) {
      alert("Failed to start analysis. Please try again.");
    }
  };

  const toggleModel = (modelId: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelId) ? prev.filter((m) => m !== modelId) : [...prev, modelId]
    );
  };

  const totalCost = selectedModels.reduce((sum, modelId) => {
    const model = models.find((m) => m.id === modelId);
    return sum + (model?.estimatedCost || 0);
  }, 0);

  if (ideaLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading idea...</p>
        </div>
      </div>
    );
  }

  if (ideaError || !idea) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <Card className="p-8 text-center">
          <p className="text-red-600 mb-4">Failed to load idea</p>
          <Button onClick={() => router.push("/ideas")} className="bg-blue-600 hover:bg-blue-700 text-white">
            Back to Ideas
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <Button
            onClick={() => router.push("/ideas")}
            className="mb-4 bg-gray-100 hover:bg-gray-200 text-gray-700"
          >
            ← Back to Ideas
          </Button>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-4xl font-bold text-gray-900">{idea.name}</h1>
                <Badge
                  className={
                    idea.status === "ANALYZED"
                      ? "bg-green-500 text-white"
                      : idea.status === "ANALYZING"
                      ? "bg-blue-500 text-white"
                      : "bg-gray-500 text-white"
                  }
                >
                  {idea.status}
                </Badge>
              </div>
              <p className="text-gray-500">
                Created {new Date(idea.createdAt).toLocaleDateString()}
              </p>
            </div>
            <Button
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="bg-red-100 hover:bg-red-200 text-red-700"
            >
              Delete Idea
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <div className="flex gap-6">
            <button
              onClick={() => setActiveTab("overview")}
              className={`pb-3 px-1 font-semibold transition-colors ${
                activeTab === "overview"
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab("analyses")}
              className={`pb-3 px-1 font-semibold transition-colors ${
                activeTab === "analyses"
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              Analyses ({reports.length})
            </button>
            <button
              onClick={() => setActiveTab("edit")}
              className={`pb-3 px-1 font-semibold transition-colors ${
                activeTab === "edit"
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              Edit
            </button>
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            <Card className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Description</h2>
              <p className="text-gray-700 whitespace-pre-wrap">{idea.description}</p>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {idea.industry && (
                <Card className="p-6">
                  <h3 className="text-sm font-semibold text-gray-500 mb-2">Industry</h3>
                  <p className="text-lg text-gray-900">{idea.industry}</p>
                </Card>
              )}
              {idea.targetMarket && (
                <Card className="p-6">
                  <h3 className="text-sm font-semibold text-gray-500 mb-2">Target Market</h3>
                  <p className="text-lg text-gray-900">{idea.targetMarket}</p>
                </Card>
              )}
              {idea.estimatedBudget && (
                <Card className="p-6">
                  <h3 className="text-sm font-semibold text-gray-500 mb-2">Estimated Budget</h3>
                  <p className="text-lg text-gray-900">${idea.estimatedBudget.toLocaleString()}</p>
                </Card>
              )}
            </div>

            {idea.tags && idea.tags.length > 0 && (
              <Card className="p-6">
                <h3 className="text-sm font-semibold text-gray-500 mb-3">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {idea.tags.map((tag, idx) => (
                    <Badge key={idx} className="bg-blue-100 text-blue-800 border-blue-200">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </Card>
            )}

            {idea.notes && (
              <Card className="p-6">
                <h3 className="text-sm font-semibold text-gray-500 mb-3">Notes</h3>
                <p className="text-gray-700 whitespace-pre-wrap">{idea.notes}</p>
              </Card>
            )}
          </div>
        )}

        {/* Analyses Tab */}
        {activeTab === "analyses" && (
          <div className="space-y-6">
            {/* Analyze Button */}
            {!isAnalyzing && (
              <Card className="p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Start New Analysis</h2>
                <Button
                  onClick={() => setIsAnalyzing(true)}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                >
                  Analyze This Idea
                </Button>
              </Card>
            )}

            {/* Model Selection */}
            {isAnalyzing && (
              <Card className="p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Select Models</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {models.slice(0, 6).map((model) => (
                    <div
                      key={model.id}
                      onClick={() => toggleModel(model.id)}
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        selectedModels.includes(model.id)
                          ? "border-blue-600 bg-blue-50"
                          : "border-gray-200 hover:border-blue-300"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-gray-900">{model.name}</h3>
                        {model.recommended && (
                          <Badge className="bg-green-500 text-white text-xs">Recommended</Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{model.provider}</p>
                      <p className="text-sm font-medium text-blue-600">
                        ~${model.estimatedCost?.toFixed(2)} per analysis
                      </p>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div>
                    <p className="text-sm text-gray-600">
                      Selected: {selectedModels.length} model{selectedModels.length !== 1 ? "s" : ""}
                    </p>
                    <p className="text-lg font-semibold text-gray-900">
                      Total Cost: ${totalCost.toFixed(2)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => {
                        setIsAnalyzing(false);
                        setSelectedModels([]);
                      }}
                      className="bg-gray-200 hover:bg-gray-300 text-gray-700"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleAnalyze}
                      disabled={selectedModels.length === 0 || analyzeMutation.isPending}
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                    >
                      {analyzeMutation.isPending ? "Starting..." : "Start Analysis"}
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            {/* Reports List */}
            {reports.length === 0 && !isAnalyzing && (
              <Card className="p-12 text-center">
                <p className="text-gray-600 mb-4">No analyses yet for this idea</p>
                <Button
                  onClick={() => setIsAnalyzing(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Run First Analysis
                </Button>
              </Card>
            )}

            {reports.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-gray-900">Analysis Reports</h2>
                  {reports.length >= 2 && (
                    <Button
                      onClick={() => router.push(`/compare/${ideaId}`)}
                      className="bg-purple-600 hover:bg-purple-700 text-white"
                    >
                      Compare All Reports
                    </Button>
                  )}
                </div>
                <div className="space-y-4">
                  {reports.map((report) => (
                    <Card key={report.id} className="p-6 hover:shadow-lg transition-shadow">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900">{report.model}</h3>
                          <p className="text-sm text-gray-500">
                            {new Date(report.createdAt).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge
                            className={
                              report.status === "completed"
                                ? "bg-green-500 text-white"
                                : report.status === "failed"
                                ? "bg-red-500 text-white"
                                : "bg-blue-500 text-white"
                            }
                          >
                            {report.status}
                          </Badge>
                          {report.status === "completed" && (
                            <Button
                              onClick={() => router.push(`/results/${report.id}`)}
                              className="bg-blue-600 hover:bg-blue-700 text-white"
                            >
                              View Report
                            </Button>
                          )}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Edit Tab */}
        {activeTab === "edit" && (
          <Card className="p-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Edit Idea</h2>
            <form onSubmit={handleUpdate} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Name</label>
                <Input
                  type="text"
                  value={editFormData.name}
                  onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                <Textarea
                  value={editFormData.description}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, description: e.target.value })
                  }
                  rows={8}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Industry</label>
                <Input
                  type="text"
                  value={editFormData.industry}
                  onChange={(e) => setEditFormData({ ...editFormData, industry: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Target Market
                </label>
                <Input
                  type="text"
                  value={editFormData.targetMarket}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, targetMarket: e.target.value })
                  }
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Estimated Budget
                </label>
                <Input
                  type="number"
                  value={editFormData.estimatedBudget || ""}
                  onChange={(e) =>
                    setEditFormData({
                      ...editFormData,
                      estimatedBudget: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Notes</label>
                <Textarea
                  value={editFormData.notes}
                  onChange={(e) => setEditFormData({ ...editFormData, notes: e.target.value })}
                  rows={4}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  What changed? <span className="text-red-500">*</span>
                </label>
                <Textarea
                  value={editFormData.changes}
                  onChange={(e) => setEditFormData({ ...editFormData, changes: e.target.value })}
                  placeholder="Describe what you changed and why..."
                  rows={3}
                  required
                />
              </div>

              <div className="flex gap-4 pt-4">
                <Button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                >
                  {updateMutation.isPending ? "Saving..." : "Save Changes"}
                </Button>
                <Button
                  type="button"
                  onClick={() => setActiveTab("overview")}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-8"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </Card>
        )}
      </div>
    </div>
  );
}
