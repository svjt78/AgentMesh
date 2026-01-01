import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              AgentMesh
            </h1>
            <p className="text-2xl text-gray-600 mb-2">
              Production-Scale Multi-Agentic Insurance Framework
            </p>
            <p className="text-lg text-gray-500">
              Demonstrating scalable multi-agent orchestration with real-time streaming
            </p>
          </div>

          {/* Features */}
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Key Features</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start space-x-3">
                <span className="text-green-600 text-xl">✓</span>
                <div>
                  <h3 className="font-medium text-gray-900">7 Specialized Agents</h3>
                  <p className="text-sm text-gray-600">Orchestrator + 6 domain experts</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-green-600 text-xl">✓</span>
                <div>
                  <h3 className="font-medium text-gray-900">Real-time Streaming</h3>
                  <p className="text-sm text-gray-600">Live SSE progress updates</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-green-600 text-xl">✓</span>
                <div>
                  <h3 className="font-medium text-gray-900">Dynamic Discovery</h3>
                  <p className="text-sm text-gray-600">Registry-driven agent and tool lookup</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <span className="text-green-600 text-xl">✓</span>
                <div>
                  <h3 className="font-medium text-gray-900">Complete Observability</h3>
                  <p className="text-sm text-gray-600">Full event replay and evidence maps</p>
                </div>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center">Get Started</h2>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/run-claim"
                className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors"
              >
                Run Claim Triage
              </Link>
              <a
                href="http://localhost:8016/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center px-8 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
              >
                API Documentation
              </a>
            </div>
          </div>

          {/* Info Section */}
          <div className="mt-8 text-center text-gray-600">
            <p className="text-sm">
              Built with Next.js, FastAPI, and Bounded ReAct Agents
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
