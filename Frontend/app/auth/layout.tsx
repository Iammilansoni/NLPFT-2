/**
 * Auth Layout - Premium SaaS Split-Screen Design
 * Left: Gradient blue panel with product preview
 * Right: Clean white form area
 */

import React from 'react';
import { Zap, LayoutGrid, FileJson, MessageSquare, BarChart3 } from 'lucide-react';
import Link from 'next/link';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Gradient Blue with Product Preview */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-[45%] relative overflow-hidden">
        {/* Gradient Background */}
        <div 
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(135deg, #4F46E5 0%, #3B82F6 30%, #6366F1 60%, #4338CA 100%)',
          }}
        />
        
        {/* Geometric shapes */}
        <div className="absolute inset-0 overflow-hidden">
          <div 
            className="absolute top-0 left-0 w-full h-full opacity-20"
            style={{
              backgroundImage: `
                linear-gradient(45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                linear-gradient(-45deg, rgba(255,255,255,0.1) 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.05) 75%),
                linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.05) 75%)
              `,
              backgroundSize: '60px 60px',
            }}
          />
          {/* Large geometric triangle shapes */}
          <div className="absolute -top-20 -right-20 w-96 h-96 bg-white/5 rotate-45 transform" />
          <div className="absolute top-1/4 -left-10 w-64 h-64 bg-white/5 rotate-12 transform" />
          <div className="absolute bottom-1/3 right-1/4 w-48 h-48 bg-white/5 -rotate-12 transform" />
        </div>
        
        {/* Content */}
        <div className="relative z-10 flex flex-col justify-between p-8 lg:p-12 w-full">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 w-fit">
            <div className="w-10 h-10 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-white">NLPForge</span>
          </Link>
          
          {/* Middle content - Tagline and Preview */}
          <div className="flex-1 flex flex-col justify-center py-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4 leading-tight">
              Designed for<br />
              <span className="text-blue-200">AI-Powered Testing</span>
            </h2>
            <p className="text-white/70 text-lg mb-8 max-w-md">
              Generate intelligent test datasets and validate APIs remotely, from anywhere.
            </p>
            
            {/* Pagination indicator */}
            <div className="flex gap-2 mb-8">
              <div className="w-8 h-1.5 rounded-full bg-white" />
              <div className="w-2 h-1.5 rounded-full bg-white/30" />
              <div className="w-2 h-1.5 rounded-full bg-white/30" />
            </div>
            
            {/* Floating preview card */}
            <div className="relative max-w-lg">
              {/* App preview window */}
              <div className="bg-white rounded-xl shadow-2xl overflow-hidden transform hover:scale-[1.02] transition-transform duration-300">
                {/* Window header */}
                <div className="bg-slate-50 border-b border-slate-200 px-4 py-3 flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-primary/10 flex items-center justify-center">
                      <LayoutGrid className="w-3.5 h-3.5 text-primary" />
                    </div>
                    <span className="text-sm font-medium text-slate-700">API Test Templates</span>
                  </div>
                </div>
                
                {/* Preview content */}
                <div className="p-4 space-y-3">
                  {/* Sample rows */}
                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <FileJson className="w-5 h-5 text-blue-500" />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-700">NLP Intent Classification</div>
                      <div className="text-xs text-slate-400">Semantic matching • 95%+ accuracy</div>
                    </div>
                    <div className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">Active</div>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <MessageSquare className="w-5 h-5 text-purple-500" />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-700">Query-to-API Matching</div>
                      <div className="text-xs text-slate-400">Vector search • Re-ranking</div>
                    </div>
                    <div className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">Ready</div>
                  </div>
                  
                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <BarChart3 className="w-5 h-5 text-amber-500" />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-700">AI Dataset Generation</div>
                      <div className="text-xs text-slate-400">LLM-powered • Multi-provider</div>
                    </div>
                    <div className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">Active</div>
                  </div>
                </div>
              </div>
              
              {/* Floating avatar */}
              <div className="absolute -top-4 -right-4 w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 border-4 border-white shadow-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">JD</span>
              </div>
            </div>
          </div>
          
          {/* Bottom - Trust indicators */}
          <div className="text-white/50 text-sm">
            <p>Trusted by 1,000+ developers worldwide</p>
          </div>
        </div>
      </div>
      
      {/* Right Panel - Form Area */}
      <div className="w-full lg:w-1/2 xl:w-[55%] flex items-center justify-center bg-background">
        <div className="w-full max-w-md px-6 py-8 lg:px-12">
          {children}
        </div>
      </div>
    </div>
  );
}
