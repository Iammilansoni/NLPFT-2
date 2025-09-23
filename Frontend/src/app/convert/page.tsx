"use client";

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { ConvertRequest, ConvertResponse } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { 
  Zap, 
  Download, 
  Copy, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  FileText,
  Code,
  Sparkles
} from 'lucide-react';
import { toast } from 'sonner';

export default function ConvertPage() {
  const [inputText, setInputText] = useState('');
  const [result, setResult] = useState<ConvertResponse | null>(null);

  const convertMutation = useMutation({
    mutationFn: (request: ConvertRequest) => api.convertText(request),
    onSuccess: (data) => {
      setResult(data);
      toast.success('Text converted successfully!');
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to convert text';
      toast.error(errorMessage);
    },
  });

  const handleConvert = () => {
    if (!inputText.trim()) {
      toast.error('Please enter some text to convert');
      return;
    }

    convertMutation.mutate({
      text: inputText.trim(),
    });
  };

  const handleCopyResult = async () => {
    if (!result) return;
    
    try {
      await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      toast.success('Result copied to clipboard!');
    } catch {
      toast.error('Failed to copy result');
    }
  };

  const handleDownloadResult = () => {
    if (!result) return;
    
    api.downloadJson(result, `convert-result-${new Date().toISOString().slice(0, 10)}.json`);
    toast.success('Result downloaded successfully!');
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500/10 text-green-700 dark:text-green-400';
    if (confidence >= 0.6) return 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400';
    return 'bg-red-500/10 text-red-700 dark:text-red-400';
  };

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.8) return <CheckCircle className="h-3 w-3" />;
    if (confidence >= 0.6) return <AlertCircle className="h-3 w-3" />;
    return <AlertCircle className="h-3 w-3" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Text Converter</h1>
        <p className="text-muted-foreground">
          Convert natural language text into structured function calls using the Enhanced Rule Engine
        </p>
      </div>

      {/* Input Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Input Text
          </CardTitle>
          <CardDescription>
            Enter the natural language text you want to convert into structured function calls
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="input-text">Text to Convert</Label>
            <Textarea
              id="input-text"
              placeholder="Enter your text here... (e.g., 'Create a user named John Doe with email john@example.com')"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              rows={6}
              className="resize-none"
            />
          </div>
          
          <div className="flex gap-2">
            <Button 
              onClick={handleConvert}
              disabled={convertMutation.isPending || !inputText.trim()}
              className="flex-1 sm:flex-none"
            >
              {convertMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                  Converting...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Convert Text
                </>
              )}
            </Button>
            
            {inputText && (
              <Button 
                variant="outline" 
                onClick={() => setInputText('')}
                disabled={convertMutation.isPending}
              >
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {result && (
        <div className="space-y-4">
          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Conversion Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">{result.steps.length}</div>
                  <div className="text-sm text-muted-foreground">Function Calls</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {result.overall_confidence ? (result.overall_confidence * 100).toFixed(1) : 0}%
                  </div>
                  <div className="text-sm text-muted-foreground">Overall Confidence</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {result.unresolved_tokens?.length || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Unresolved Tokens</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {result.processing_time_ms}ms
                  </div>
                  <div className="text-sm text-muted-foreground">Processing Time</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Function Steps */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Code className="h-5 w-5" />
                    Generated Function Calls
                  </CardTitle>
                  <CardDescription>
                    Structured function calls extracted from your input text
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleCopyResult}
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy JSON
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleDownloadResult}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {result.steps.map((step, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          Step {index + 1}
                        </Badge>
                        <h3 className="font-mono text-sm font-medium">
                          {step.function}
                        </h3>
                      </div>
                      <Badge className={getConfidenceColor(step.confidence)}>
                        {getConfidenceIcon(step.confidence)}
                        {(step.confidence * 100).toFixed(1)}%
                      </Badge>
                    </div>

                    {step.matched_text && (
                      <div className="text-sm">
                        <span className="text-muted-foreground">Matched text: </span>
                        <span className="bg-primary/10 text-primary px-2 py-1 rounded font-mono text-xs">
                          &ldquo;{step.matched_text}&rdquo;
                        </span>
                      </div>
                    )}

                    {step.template && (
                      <div className="text-sm">
                        <span className="text-muted-foreground">Template: </span>
                        <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
                          {step.template}
                        </span>
                      </div>
                    )}

                    <div className="bg-muted/50 rounded p-3">
                      <div className="text-xs text-muted-foreground mb-1">Arguments:</div>
                      <pre className="text-xs font-mono overflow-x-auto">
                        {JSON.stringify(step.args, null, 2)}
                      </pre>
                    </div>

                    {step.provenance && (
                      <div className="text-xs text-muted-foreground">
                        <Clock className="h-3 w-3 inline mr-1" />
                        Provenance: {step.provenance}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Unresolved Tokens */}
          {result.unresolved_tokens && result.unresolved_tokens.length > 0 && (
            <Card className="border-l-4 border-l-orange-500">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-orange-700 dark:text-orange-400">
                  <AlertCircle className="h-5 w-5" />
                  Unresolved Tokens
                </CardTitle>
                <CardDescription>
                  These tokens could not be mapped to function calls. Consider adding them to the dictionary.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {result.unresolved_tokens.map((token, index) => (
                    <Badge key={index} variant="outline" className="text-orange-700 dark:text-orange-400">
                      {token}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Raw JSON Output */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                Raw JSON Output
              </CardTitle>
              <CardDescription>
                Complete API response in JSON format
              </CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted/50 rounded p-4 text-xs overflow-x-auto font-mono">
                {JSON.stringify(result, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Example Usage */}
      {!result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Example Usage
            </CardTitle>
            <CardDescription>
              Try these example inputs to see how the converter works
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-sm">User Management</h4>
                <div className="bg-muted/50 rounded p-3 text-sm font-mono">
                  &ldquo;Create a user named John Doe with email john@example.com and role admin&rdquo;
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setInputText("Create a user named John Doe with email john@example.com and role admin")}
                >
                  Try this example
                </Button>
              </div>

              <div className="space-y-2">
                <h4 className="font-medium text-sm">Data Operations</h4>
                <div className="bg-muted/50 rounded p-3 text-sm font-mono">
                  &ldquo;Update the product with ID 123 to set price to 29.99 and status to active&rdquo;
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setInputText("Update the product with ID 123 to set price to 29.99 and status to active")}
                >
                  Try this example
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}