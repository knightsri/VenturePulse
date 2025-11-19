import axios from 'axios';
import { OpenRouterModel } from '../types';

const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

interface CachedModels {
  models: OpenRouterModel[];
  cachedAt: number;
}

let modelsCache: CachedModels | null = null;

export class OpenRouterClient {
  /**
   * Fetch available models from OpenRouter API
   */
  static async fetchAvailableModels(): Promise<OpenRouterModel[]> {
    // Check cache
    if (modelsCache && Date.now() - modelsCache.cachedAt < CACHE_DURATION) {
      console.log('[OpenRouter] Returning cached models');
      return modelsCache.models;
    }

    try {
      console.log('[OpenRouter] Fetching models from API...');
      const response = await axios.get(`${OPENROUTER_API_URL}/models`, {
        headers: {
          'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
        },
      });

      const rawModels = response.data.data || [];

      // Process and enrich model data
      const models: OpenRouterModel[] = rawModels
        .filter((model: any) => !model.id.includes('instruct') && !model.id.includes('vision'))
        .map((model: any) => {
          const estimatedCost = this.estimateAnalysisCost(model.pricing || {});

          return {
            id: model.id,
            name: model.name || model.id,
            provider: this.extractProvider(model.id),
            pricing: {
              prompt: model.pricing?.prompt || 0,
              completion: model.pricing?.completion || 0,
            },
            contextLength: model.context_length || 8000,
            estimatedCost,
            speed: this.estimateSpeed(model.id),
            recommended: this.isRecommended(model.id, estimatedCost),
          };
        })
        .sort((a, b) => {
          // Sort: free first, then by cost
          if (a.pricing.prompt === 0 && b.pricing.prompt !== 0) return -1;
          if (a.pricing.prompt !== 0 && b.pricing.prompt === 0) return 1;
          return (a.estimatedCost || 0) - (b.estimatedCost || 0);
        });

      // Cache the results
      modelsCache = {
        models,
        cachedAt: Date.now(),
      };

      console.log(`[OpenRouter] Fetched and cached ${models.length} models`);
      return models;
    } catch (error) {
      console.error('[OpenRouter] Error fetching models:', error);

      // If cache exists, return it even if stale
      if (modelsCache) {
        console.log('[OpenRouter] Returning stale cache due to error');
        return modelsCache.models;
      }

      throw new Error('Failed to fetch models from OpenRouter');
    }
  }

  /**
   * Estimate cost for a complete analysis
   * Average: ~2000 input tokens per section × 9 sections
   *         + ~8000 output tokens per section × 9 sections
   */
  static estimateAnalysisCost(pricing: { prompt?: number; completion?: number }): number {
    const inputTokens = 2000 * 9; // 18k input tokens
    const outputTokens = 8000 * 9; // 72k output tokens

    const promptCost = (inputTokens / 1000000) * (pricing.prompt || 0);
    const completionCost = (outputTokens / 1000000) * (pricing.completion || 0);

    return parseFloat((promptCost + completionCost).toFixed(2));
  }

  /**
   * Extract provider name from model ID
   */
  private static extractProvider(modelId: string): string {
    const provider = modelId.split('/')[0];
    const providerMap: { [key: string]: string } = {
      'anthropic': 'Anthropic',
      'openai': 'OpenAI',
      'google': 'Google',
      'meta-llama': 'Meta',
      'mistralai': 'Mistral AI',
      'cohere': 'Cohere',
      'nousresearch': 'Nous Research',
    };
    return providerMap[provider] || provider;
  }

  /**
   * Estimate speed based on model characteristics
   */
  private static estimateSpeed(modelId: string): 'slow' | 'medium' | 'fast' {
    const id = modelId.toLowerCase();

    if (id.includes('flash') || id.includes('mini') || id.includes('turbo')) {
      return 'fast';
    }

    if (id.includes('opus') || id.includes('large') || id.includes('405b')) {
      return 'slow';
    }

    return 'medium';
  }

  /**
   * Determine if model should be recommended
   */
  private static isRecommended(modelId: string, estimatedCost: number): boolean {
    // Recommend free models and good value models
    const recommendedModels = [
      'google/gemini-2.0-flash-exp:free',
      'google/gemini-flash-1.5',
      'anthropic/claude-sonnet-4.5',
      'openai/gpt-4o-mini',
    ];

    return recommendedModels.some(rec => modelId.includes(rec)) ||
           (estimatedCost > 0 && estimatedCost < 1.0);
  }

  /**
   * Clear model cache (for admin use)
   */
  static clearCache(): void {
    modelsCache = null;
    console.log('[OpenRouter] Cache cleared');
  }
}
