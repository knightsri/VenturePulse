"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createIdea, type CreateIdeaRequest } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";

export default function NewIdeaPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<CreateIdeaRequest>({
    name: "",
    description: "",
    industry: "",
    targetMarket: "",
    estimatedBudget: undefined,
    tags: [],
    notes: "",
  });
  const [tagInput, setTagInput] = useState("");

  const createMutation = useMutation({
    mutationFn: createIdea,
    onSuccess: (idea) => {
      router.push(`/ideas/${idea.id}`);
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim() || !formData.description.trim()) {
      alert("Please fill in the required fields (Name and Description)");
      return;
    }

    try {
      await createMutation.mutateAsync(formData);
    } catch (error) {
      alert("Failed to create idea. Please try again.");
    }
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...(formData.tags || []), tagInput.trim()],
      });
      setTagInput("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags?.filter((tag) => tag !== tagToRemove) || [],
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <Button
            onClick={() => router.push("/ideas")}
            className="mb-4 bg-gray-100 hover:bg-gray-200 text-gray-700"
          >
            ← Back to Ideas
          </Button>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Create New Idea</h1>
          <p className="text-lg text-gray-600">
            Capture your product idea and save it for future analysis
          </p>
        </div>

        {/* Form */}
        <Card className="p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Idea Name <span className="text-red-500">*</span>
              </label>
              <Input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., AI-Powered Task Manager"
                required
                className="w-full"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Description <span className="text-red-500">*</span>
              </label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe your product idea in detail. Include the problem it solves, target audience, key features, and unique value proposition."
                required
                rows={8}
                className="w-full"
              />
              <p className="mt-1 text-sm text-gray-500">
                Minimum 100 characters recommended for better analysis
              </p>
            </div>

            {/* Industry */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Industry
              </label>
              <Input
                type="text"
                value={formData.industry}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                placeholder="e.g., SaaS, E-commerce, FinTech"
                className="w-full"
              />
            </div>

            {/* Target Market */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Target Market
              </label>
              <Input
                type="text"
                value={formData.targetMarket}
                onChange={(e) => setFormData({ ...formData, targetMarket: e.target.value })}
                placeholder="e.g., Small businesses, Developers, Enterprise"
                className="w-full"
              />
            </div>

            {/* Estimated Budget */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Estimated Budget (USD)
              </label>
              <Input
                type="number"
                value={formData.estimatedBudget || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    estimatedBudget: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                placeholder="e.g., 50000"
                min="0"
                step="1000"
                className="w-full"
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Tags</label>
              <div className="flex gap-2 mb-2">
                <Input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddTag();
                    }
                  }}
                  placeholder="Add a tag and press Enter"
                  className="flex-1"
                />
                <Button
                  type="button"
                  onClick={handleAddTag}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Add Tag
                </Button>
              </div>
              {formData.tags && formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag, idx) => (
                    <div
                      key={idx}
                      className="inline-flex items-center gap-1 bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-blue-900"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Additional Notes
              </label>
              <Textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Any additional context, assumptions, or considerations..."
                rows={4}
                className="w-full"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-4 pt-4">
              <Button
                type="submit"
                disabled={createMutation.isPending}
                className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-3 text-lg font-semibold"
              >
                {createMutation.isPending ? "Creating..." : "Create Idea"}
              </Button>
              <Button
                type="button"
                onClick={() => router.push("/ideas")}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-8"
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>

        {/* Help Text */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">💡 Tips for Great Ideas</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Be specific about the problem you're solving</li>
            <li>• Clearly define your target audience</li>
            <li>• Highlight what makes your idea unique</li>
            <li>• Include realistic budget and timeline estimates</li>
            <li>• Use tags to organize and categorize your ideas</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
