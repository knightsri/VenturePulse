"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { compareIdeaReports, fetchIdea } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Cell,
} from "recharts";

const COLORS = [
  "#3b82f6",
  "#8b5cf6",
  "#ec4899",
  "#f59e0b",
  "#10b981",
  "#6366f1",
];

export default function ComparisonPage() {
  const router = useRouter();
  const params = useParams();
  const ideaId = params.ideaId as string;

  const {
    data: idea,
    isLoading: ideaLoading,
  } = useQuery({
    queryKey: ["idea", ideaId],
    queryFn: () => fetchIdea(ideaId),
  });

  const {
    data: comparison,
    isLoading: comparisonLoading,
    error: comparisonError,
  } = useQuery({
    queryKey: ["comparison", ideaId],
    queryFn: () => compareIdeaReports(ideaId),
    retry: 1,
  });

  const isLoading = ideaLoading || comparisonLoading;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading comparison...</p>
        </div>
      </div>
    );
  }

  if (comparisonError || !comparison) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <p className="text-red-600 mb-4">
            {comparisonError
              ? "Not enough reports to compare. You need at least 2 completed analyses."
              : "Failed to load comparison"}
          </p>
          <Button
            onClick={() => router.push(`/ideas/${ideaId}`)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Back to Idea
          </Button>
        </Card>
      </div>
    );
  }

  // Prepare data for radar chart
  const radarData = [
    {
      dimension: "Market",
      ...comparison.models.reduce(
        (acc, model, idx) => ({ ...acc, [model.model]: model.scores.market }),
        {}
      ),
    },
    {
      dimension: "Technical",
      ...comparison.models.reduce(
        (acc, model, idx) => ({ ...acc, [model.model]: model.scores.technical }),
        {}
      ),
    },
    {
      dimension: "Competitive",
      ...comparison.models.reduce(
        (acc, model, idx) => ({ ...acc, [model.model]: model.scores.competitive }),
        {}
      ),
    },
    {
      dimension: "Business",
      ...comparison.models.reduce(
        (acc, model, idx) => ({ ...acc, [model.model]: model.scores.business }),
        {}
      ),
    },
    {
      dimension: "Execution",
      ...comparison.models.reduce(
        (acc, model, idx) => ({ ...acc, [model.model]: model.scores.execution }),
        {}
      ),
    },
  ];

  // Prepare data for cost vs quality scatter chart
  const scatterData = comparison.models.map((model) => ({
    name: model.model,
    cost: model.cost,
    quality: model.scores.overall,
  }));

  // Prepare data for bar chart (average scores)
  const barData = [
    { name: "Market", score: comparison.averageScores.market, spread: comparison.scoreSpread.market },
    { name: "Technical", score: comparison.averageScores.technical, spread: comparison.scoreSpread.technical },
    { name: "Competitive", score: comparison.averageScores.competitive, spread: comparison.scoreSpread.competitive },
    { name: "Business", score: comparison.averageScores.business, spread: comparison.scoreSpread.business },
    { name: "Execution", score: comparison.averageScores.execution, spread: comparison.scoreSpread.execution },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <Button
            onClick={() => router.push(`/ideas/${ideaId}`)}
            className="mb-4 bg-gray-100 hover:bg-gray-200 text-gray-700"
          >
            ← Back to Idea
          </Button>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Multi-Model Comparison
          </h1>
          <p className="text-lg text-gray-600">{comparison.ideaName}</p>
          <p className="text-sm text-gray-500 mt-1">
            Comparing {comparison.models.length} model analyses
          </p>
        </div>

        {/* Recommendation Banner */}
        <Card className="p-6 mb-8 bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200">
          <h2 className="text-xl font-bold text-gray-900 mb-3">
            📊 Analysis Recommendation
          </h2>
          <p className="text-gray-700 leading-relaxed">{comparison.recommendation}</p>
        </Card>

        {/* Overall Scores */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="p-6">
            <h3 className="text-sm font-semibold text-gray-500 mb-2">
              Average Overall Score
            </h3>
            <p className="text-4xl font-bold text-blue-600">
              {comparison.averageScores.overall.toFixed(1)}
              <span className="text-xl text-gray-400">/10</span>
            </p>
          </Card>

          <Card className="p-6">
            <h3 className="text-sm font-semibold text-gray-500 mb-2">
              Best Value Model
            </h3>
            <p className="text-2xl font-bold text-purple-600">
              {comparison.costVsQuality.bestValue}
            </p>
            <p className="text-sm text-gray-500 mt-1">Best quality per dollar</p>
          </Card>

          <Card className="p-6">
            <h3 className="text-sm font-semibold text-gray-500 mb-2">
              Highest Quality
            </h3>
            <p className="text-2xl font-bold text-green-600">
              {comparison.costVsQuality.highestQuality}
            </p>
            <p className="text-sm text-gray-500 mt-1">Most comprehensive analysis</p>
          </Card>
        </div>

        {/* Consensus and Disagreements */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Consensus */}
          <Card className="p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              ✓ Areas of Consensus
            </h2>
            {comparison.consensus.length > 0 ? (
              <ul className="space-y-2">
                {comparison.consensus.map((item, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">No strong consensus areas</p>
            )}
          </Card>

          {/* Disagreements */}
          <Card className="p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              ⚠ Areas of Disagreement
            </h2>
            {comparison.disagreements.length > 0 ? (
              <ul className="space-y-2">
                {comparison.disagreements.map((item, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-orange-500 mr-2">⚠</span>
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic">Strong agreement across all dimensions</p>
            )}
          </Card>
        </div>

        {/* Visualizations */}
        <div className="space-y-8 mb-8">
          {/* Radar Chart */}
          <Card className="p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">
              Dimension Comparison (Radar Chart)
            </h2>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="dimension" />
                <PolarRadiusAxis angle={90} domain={[0, 10]} />
                {comparison.models.map((model, idx) => (
                  <Radar
                    key={model.model}
                    name={model.model}
                    dataKey={model.model}
                    stroke={COLORS[idx % COLORS.length]}
                    fill={COLORS[idx % COLORS.length]}
                    fillOpacity={0.2}
                  />
                ))}
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </Card>

          {/* Average Scores Bar Chart */}
          <Card className="p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">
              Average Scores by Dimension
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 10]} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-semibold">{payload[0].payload.name}</p>
                          <p className="text-blue-600">
                            Avg: {payload[0].value?.toFixed(1)}/10
                          </p>
                          <p className="text-orange-600">
                            Spread: {payload[0].payload.spread.toFixed(1)} pts
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="score" radius={[8, 8, 0, 0]}>
                  {barData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.spread > 2 ? "#f59e0b" : "#3b82f6"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-sm text-gray-500 mt-2 text-center">
              Orange bars indicate high disagreement (spread &gt; 2 points)
            </p>
          </Card>

          {/* Cost vs Quality Scatter */}
          <Card className="p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">
              Cost vs Quality Analysis
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="cost"
                  name="Cost"
                  label={{ value: "Cost ($)", position: "insideBottom", offset: -5 }}
                />
                <YAxis
                  type="number"
                  dataKey="quality"
                  name="Quality"
                  domain={[0, 10]}
                  label={{ value: "Quality Score", angle: -90, position: "insideLeft" }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
                          <p className="font-semibold">{payload[0].payload.name}</p>
                          <p className="text-gray-600">Cost: ${payload[0].payload.cost.toFixed(2)}</p>
                          <p className="text-gray-600">
                            Quality: {payload[0].payload.quality.toFixed(1)}/10
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Scatter data={scatterData} fill="#8b5cf6">
                  {scatterData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
            <p className="text-sm text-gray-500 mt-2 text-center">
              Top-left is best value (high quality, low cost)
            </p>
          </Card>
        </div>

        {/* Detailed Model Breakdown */}
        <Card className="p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            Detailed Model Breakdown
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Model</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Market</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Technical</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Competitive</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Business</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Execution</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Overall</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Cost</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Verdict</th>
                </tr>
              </thead>
              <tbody>
                {comparison.models.map((model, idx) => (
                  <tr key={model.reportId} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                        />
                        <span className="font-medium text-gray-900">{model.model}</span>
                      </div>
                    </td>
                    <td className="text-center py-3 px-4">{model.scores.market.toFixed(1)}</td>
                    <td className="text-center py-3 px-4">{model.scores.technical.toFixed(1)}</td>
                    <td className="text-center py-3 px-4">{model.scores.competitive.toFixed(1)}</td>
                    <td className="text-center py-3 px-4">{model.scores.business.toFixed(1)}</td>
                    <td className="text-center py-3 px-4">{model.scores.execution.toFixed(1)}</td>
                    <td className="text-center py-3 px-4">
                      <Badge
                        className={
                          model.scores.overall >= 8
                            ? "bg-green-500 text-white"
                            : model.scores.overall >= 6
                            ? "bg-blue-500 text-white"
                            : "bg-orange-500 text-white"
                        }
                      >
                        {model.scores.overall.toFixed(1)}
                      </Badge>
                    </td>
                    <td className="text-center py-3 px-4 text-gray-600">
                      ${model.cost.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600">{model.verdict}</td>
                  </tr>
                ))}
                {/* Average Row */}
                <tr className="bg-blue-50 font-semibold">
                  <td className="py-3 px-4">Average</td>
                  <td className="text-center py-3 px-4">{comparison.averageScores.market.toFixed(1)}</td>
                  <td className="text-center py-3 px-4">{comparison.averageScores.technical.toFixed(1)}</td>
                  <td className="text-center py-3 px-4">{comparison.averageScores.competitive.toFixed(1)}</td>
                  <td className="text-center py-3 px-4">{comparison.averageScores.business.toFixed(1)}</td>
                  <td className="text-center py-3 px-4">{comparison.averageScores.execution.toFixed(1)}</td>
                  <td className="text-center py-3 px-4">{comparison.averageScores.overall.toFixed(1)}</td>
                  <td className="text-center py-3 px-4">-</td>
                  <td className="py-3 px-4">-</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>

        {/* Individual Reports */}
        <div className="mt-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Individual Reports</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {comparison.models.map((model) => (
              <Card key={model.reportId} className="p-4">
                <h3 className="font-semibold text-gray-900 mb-2">{model.model}</h3>
                <Button
                  onClick={() => router.push(`/results/${model.reportId}`)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                >
                  View Full Report
                </Button>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
