import Link from 'next/link';
import { Navigation } from '@/components/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <Navigation />

      {/* Hero Section */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl">
            AI-Powered Product
            <span className="text-indigo-600"> Viability Analysis</span>
          </h1>
          <p className="mt-6 text-xl text-gray-600 max-w-3xl mx-auto">
            Transform weeks of research into comprehensive, investor-ready reports in just 15 minutes.
            Get deep insights across 9 critical dimensions with multiple AI models.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Link href="/analyze">
              <Button size="lg" className="text-lg px-8">
                Start Free Analysis
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline" className="text-lg px-8">
                View Reports
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Why VenturePulse?</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card>
            <CardHeader>
              <CardTitle>Comprehensive Analysis</CardTitle>
              <CardDescription>9 Critical Dimensions</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Market Landscape & Opportunity</li>
                <li>• Technical Feasibility Assessment</li>
                <li>• Competitive Advantage Analysis</li>
                <li>• Business Model Validation</li>
                <li>• MVP Roadmap & Timeline</li>
                <li>• Success Metrics Framework</li>
                <li>• Go-to-Market Strategy</li>
                <li>• Risk Analysis & Mitigation</li>
                <li>• Executive Summary</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Multi-Model Insights</CardTitle>
              <CardDescription>Compare AI Perspectives</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">
                Run your analysis across multiple AI models simultaneously:
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Claude Sonnet 4.5 (Deep reasoning)</li>
                <li>• GPT-4o (Broad knowledge)</li>
                <li>• Gemini 2.0 Flash (Fast & free)</li>
                <li>• Compare results side-by-side</li>
                <li>• Identify consensus and gaps</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Professional Reports</CardTitle>
              <CardDescription>Investor-Ready Output</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">
                Get beautifully formatted reports with:
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Visual scoring matrices</li>
                <li>• Competitive benchmarking tables</li>
                <li>• Risk assessment heatmaps</li>
                <li>• Actionable recommendations</li>
                <li>• Download as HTML or PDF</li>
                <li>• Share with team or investors</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-indigo-600 rounded-2xl p-12 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to validate your product idea?
          </h2>
          <p className="text-xl text-indigo-100 mb-8 max-w-2xl mx-auto">
            Upload your project description or paste your idea, select AI models, and get comprehensive analysis in minutes.
          </p>
          <Link href="/analyze">
            <Button size="lg" variant="secondary" className="text-lg px-8">
              Start Your First Analysis
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 border-t border-gray-200">
        <div className="text-center text-sm text-gray-500">
          <p>Powered by OpenRouter • Support for 100+ AI models</p>
        </div>
      </footer>
    </div>
  );
}
