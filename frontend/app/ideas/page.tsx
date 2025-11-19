"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { fetchIdeas, deleteIdea, type Idea } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function IdeasPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const {
    data: ideas = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["ideas", searchQuery, statusFilter],
    queryFn: () =>
      fetchIdeas({
        search: searchQuery || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      }),
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  const deleteMutation = useMutation({
    mutationFn: deleteIdea,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ideas"] });
    },
  });

  const handleDelete = async (ideaId: string, ideaName: string) => {
    if (
      window.confirm(`Are you sure you want to delete "${ideaName}"? This action cannot be undone.`)
    ) {
      try {
        await deleteMutation.mutateAsync(ideaId);
      } catch (error) {
        alert("Failed to delete idea. Please try again.");
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "DRAFT":
        return "bg-gray-500";
      case "ANALYZING":
        return "bg-blue-500";
      case "ANALYZED":
        return "bg-green-500";
      case "ARCHIVED":
        return "bg-gray-400";
      default:
        return "bg-gray-500";
    }
  };

  const filteredIdeas = ideas;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Ideas Library</h1>
          <p className="text-lg text-gray-600">
            Save and manage your product ideas for future analysis
          </p>
        </div>

        {/* Search and Filters */}
        <div className="mb-8 flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Search ideas..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="DRAFT">Draft</option>
              <option value="ANALYZING">Analyzing</option>
              <option value="ANALYZED">Analyzed</option>
              <option value="ARCHIVED">Archived</option>
            </select>

            <Button
              onClick={() => router.push("/ideas/new")}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6"
            >
              + New Idea
            </Button>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading ideas...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <Card className="p-6 bg-red-50 border-red-200">
            <p className="text-red-600">Failed to load ideas. Please try again.</p>
          </Card>
        )}

        {/* Empty State */}
        {!isLoading && !error && filteredIdeas.length === 0 && (
          <Card className="p-12 text-center">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No ideas yet</h3>
            <p className="text-gray-600 mb-4">
              Start by creating your first idea to analyze and track.
            </p>
            <Button
              onClick={() => router.push("/ideas/new")}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
            >
              Create Your First Idea
            </Button>
          </Card>
        )}

        {/* Ideas Grid */}
        {!isLoading && !error && filteredIdeas.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredIdeas.map((idea) => (
              <Card
                key={idea.id}
                className="p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => router.push(`/ideas/${idea.id}`)}
              >
                {/* Status Badge */}
                <div className="flex items-start justify-between mb-3">
                  <Badge className={`${getStatusColor(idea.status)} text-white`}>
                    {idea.status}
                  </Badge>
                  {idea.reports && idea.reports.length > 0 && (
                    <Badge className="bg-purple-100 text-purple-800 border-purple-200">
                      {idea.reports.length} report{idea.reports.length > 1 ? "s" : ""}
                    </Badge>
                  )}
                </div>

                {/* Idea Name */}
                <h3 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
                  {idea.name}
                </h3>

                {/* Description */}
                <p className="text-gray-600 mb-4 line-clamp-3">{idea.description}</p>

                {/* Metadata */}
                <div className="space-y-2 mb-4">
                  {idea.industry && (
                    <div className="flex items-center text-sm text-gray-500">
                      <span className="font-medium mr-2">Industry:</span>
                      {idea.industry}
                    </div>
                  )}
                  {idea.targetMarket && (
                    <div className="flex items-center text-sm text-gray-500">
                      <span className="font-medium mr-2">Market:</span>
                      {idea.targetMarket}
                    </div>
                  )}
                  {idea.estimatedBudget && (
                    <div className="flex items-center text-sm text-gray-500">
                      <span className="font-medium mr-2">Budget:</span>$
                      {idea.estimatedBudget.toLocaleString()}
                    </div>
                  )}
                </div>

                {/* Tags */}
                {idea.tags && idea.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {idea.tags.slice(0, 3).map((tag, idx) => (
                      <Badge
                        key={idx}
                        className="bg-blue-50 text-blue-700 border-blue-200 text-xs"
                      >
                        {tag}
                      </Badge>
                    ))}
                    {idea.tags.length > 3 && (
                      <Badge className="bg-gray-50 text-gray-600 border-gray-200 text-xs">
                        +{idea.tags.length - 3}
                      </Badge>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t border-gray-200">
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/ideas/${idea.id}`);
                    }}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm"
                  >
                    View
                  </Button>
                  {idea.reports && idea.reports.length >= 2 && (
                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/compare/${idea.id}`);
                      }}
                      className="flex-1 bg-purple-600 hover:bg-purple-700 text-white text-sm"
                    >
                      Compare
                    </Button>
                  )}
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(idea.id, idea.name);
                    }}
                    className="bg-red-100 hover:bg-red-200 text-red-700 text-sm px-3"
                  >
                    Delete
                  </Button>
                </div>

                {/* Created Date */}
                <div className="mt-3 text-xs text-gray-400">
                  Created {new Date(idea.createdAt).toLocaleDateString()}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
