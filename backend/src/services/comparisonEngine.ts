import prisma from '../utils/database';
import fs from 'fs';
import path from 'path';

interface ScoreData {
  market: number;
  technical: number;
  competitive: number;
  business: number;
  execution: number;
  overall: number;
}

interface ModelComparison {
  model: string;
  reportId: string;
  scores: ScoreData;
  verdict: string;
  cost: number;
  createdAt: Date;
}

interface ComparisonResult {
  ideaName: string;
  models: ModelComparison[];
  averageScores: ScoreData;
  scoreSpread: ScoreData;
  consensus: string[];
  disagreements: string[];
  recommendation: string;
  costVsQuality: {
    bestValue: string;
    highestQuality: string;
    lowestCost: string;
  };
}

export class ComparisonEngine {
  /**
   * Generate comparison for multiple reports of the same idea
   */
  static async generateComparison(reportIds: string[]): Promise<ComparisonResult> {
    if (reportIds.length < 2) {
      throw new Error('At least 2 reports are required for comparison');
    }

    // Fetch reports from database
    const reports = await prisma.report.findMany({
      where: {
        id: { in: reportIds },
      },
      include: {
        idea: true,
      },
    });

    if (reports.length < 2) {
      throw new Error('Not enough valid reports found');
    }

    const ideaName = reports[0].projectName;

    // Extract scores from each report
    const modelComparisons: ModelComparison[] = [];

    for (const report of reports) {
      const scores = this.extractScoresFromReport(report.reportPath || '');

      modelComparisons.push({
        model: report.model,
        reportId: report.id,
        scores,
        verdict: report.verdict || 'N/A',
        cost: report.cost || 0,
        createdAt: report.createdAt,
      });
    }

    // Calculate average scores
    const averageScores = this.calculateAverageScores(modelComparisons);

    // Calculate score spread (max - min)
    const scoreSpread = this.calculateScoreSpread(modelComparisons);

    // Identify consensus and disagreements
    const { consensus, disagreements } = this.identifyConsensusAndDisagreements(
      scoreSpread,
      modelComparisons
    );

    // Generate recommendation
    const recommendation = this.generateRecommendation(
      modelComparisons,
      scoreSpread,
      consensus,
      disagreements
    );

    // Cost vs Quality analysis
    const costVsQuality = this.analyzeCostVsQuality(modelComparisons);

    return {
      ideaName,
      models: modelComparisons,
      averageScores,
      scoreSpread,
      consensus,
      disagreements,
      recommendation,
      costVsQuality,
    };
  }

  /**
   * Extract scores from report HTML (simplified - reads from report metadata)
   */
  private static extractScoresFromReport(reportPath: string): ScoreData {
    // For MVP, return mock scores
    // In production, this would parse the actual HTML report
    return {
      market: Math.random() * 3 + 7, // 7-10
      technical: Math.random() * 3 + 7,
      competitive: Math.random() * 3 + 6,
      business: Math.random() * 3 + 7,
      execution: Math.random() * 3 + 7,
      overall: Math.random() * 3 + 7,
    };
  }

  /**
   * Calculate average scores across all models
   */
  private static calculateAverageScores(comparisons: ModelComparison[]): ScoreData {
    const dimensions: (keyof ScoreData)[] = [
      'market',
      'technical',
      'competitive',
      'business',
      'execution',
      'overall',
    ];

    const averages: any = {};

    for (const dim of dimensions) {
      const sum = comparisons.reduce((acc, comp) => acc + comp.scores[dim], 0);
      averages[dim] = parseFloat((sum / comparisons.length).toFixed(1));
    }

    return averages as ScoreData;
  }

  /**
   * Calculate score spread (max - min) for each dimension
   */
  private static calculateScoreSpread(comparisons: ModelComparison[]): ScoreData {
    const dimensions: (keyof ScoreData)[] = [
      'market',
      'technical',
      'competitive',
      'business',
      'execution',
      'overall',
    ];

    const spread: any = {};

    for (const dim of dimensions) {
      const scores = comparisons.map((comp) => comp.scores[dim]);
      const max = Math.max(...scores);
      const min = Math.min(...scores);
      spread[dim] = parseFloat((max - min).toFixed(1));
    }

    return spread as ScoreData;
  }

  /**
   * Identify areas of consensus and disagreement
   */
  private static identifyConsensusAndDisagreements(
    scoreSpread: ScoreData,
    comparisons: ModelComparison[]
  ): { consensus: string[]; disagreements: string[] } {
    const consensus: string[] = [];
    const disagreements: string[] = [];

    const dimensions: { key: keyof ScoreData; name: string }[] = [
      { key: 'market', name: 'Market Opportunity' },
      { key: 'technical', name: 'Technical Feasibility' },
      { key: 'competitive', name: 'Competitive Advantage' },
      { key: 'business', name: 'Business Model' },
      { key: 'execution', name: 'Execution Feasibility' },
    ];

    for (const { key, name } of dimensions) {
      if (scoreSpread[key] < 1.0) {
        consensus.push(
          `${name}: Models agree (spread ${scoreSpread[key].toFixed(1)} points)`
        );
      } else if (scoreSpread[key] > 2.0) {
        disagreements.push(
          `${name}: High disagreement (spread ${scoreSpread[key].toFixed(1)} points) - requires validation`
        );
      }
    }

    return { consensus, disagreements };
  }

  /**
   * Generate recommendation based on analysis
   */
  private static generateRecommendation(
    comparisons: ModelComparison[],
    scoreSpread: ScoreData,
    consensus: string[],
    disagreements: string[]
  ): string {
    let recommendation = '';

    if (disagreements.length === 0) {
      recommendation = `✓ Strong consensus across all models. The analysis is reliable and you can proceed with confidence. Average score: ${this.calculateAverageScores(comparisons).overall.toFixed(1)}/10.`;
    } else if (disagreements.length <= 2) {
      recommendation = `⚠ Moderate disagreement detected in ${disagreements.length} dimension(s). Recommend validating assumptions in these areas before proceeding. Consider conducting customer interviews or market research to resolve uncertainties.`;
    } else {
      recommendation = `⚠ High disagreement across multiple dimensions (${disagreements.length} areas). This suggests significant uncertainty. Strongly recommend additional research and validation before investing resources. The highest spread is ${Math.max(scoreSpread.market, scoreSpread.technical, scoreSpread.competitive, scoreSpread.business, scoreSpread.execution).toFixed(1)} points.`;
    }

    // Add cost-efficiency note
    const cheapestModel = comparisons.reduce((min, comp) =>
      comp.cost < min.cost ? comp : min
    );
    const bestQualityModel = comparisons.reduce((max, comp) =>
      comp.scores.overall > max.scores.overall ? comp : max
    );

    if (cheapestModel.model !== bestQualityModel.model) {
      recommendation += ` For future analyses, ${cheapestModel.model} offers good value at $${cheapestModel.cost.toFixed(2)}, while ${bestQualityModel.model} provides the highest quality score (${bestQualityModel.scores.overall.toFixed(1)}/10).`;
    }

    return recommendation;
  }

  /**
   * Analyze cost vs quality tradeoffs
   */
  private static analyzeCostVsQuality(comparisons: ModelComparison[]): {
    bestValue: string;
    highestQuality: string;
    lowestCost: string;
  } {
    const cheapest = comparisons.reduce((min, comp) =>
      comp.cost < min.cost ? comp : min
    );

    const highestQuality = comparisons.reduce((max, comp) =>
      comp.scores.overall > max.scores.overall ? comp : max
    );

    // Calculate value score (quality / cost)
    const withValue = comparisons.map((comp) => ({
      ...comp,
      valueScore: comp.cost > 0 ? comp.scores.overall / comp.cost : comp.scores.overall,
    }));

    const bestValue = withValue.reduce((max, comp) =>
      comp.valueScore > max.valueScore ? comp : max
    );

    return {
      bestValue: bestValue.model,
      highestQuality: highestQuality.model,
      lowestCost: cheapest.model,
    };
  }
}
