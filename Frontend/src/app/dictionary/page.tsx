"use client";

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { DictionaryFunction } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  FileText, 
  Plus, 
  Search, 
  Download, 
  Upload, 
  Edit2, 
  Trash2, 
  Eye,
  Tag,
  Calendar
} from 'lucide-react';
import { toast } from 'sonner';

export default function DictionaryPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFunction, setSelectedFunction] = useState<DictionaryFunction | null>(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { 
    data: functionsResponse, 
    isLoading, 
    error 
  } = useQuery<{ functions: DictionaryFunction[], totalCount: number }>({
    queryKey: ['dictionary-functions'],
    queryFn: api.getFunctionsWithMetadata,
  });

  // Ensure functions is always an array to prevent filter errors
  const functions = Array.isArray(functionsResponse?.functions) ? functionsResponse.functions : [];
  const totalCount = functionsResponse?.totalCount || 0;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteFunction(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dictionary-functions'] });
      setIsDeleteDialogOpen(false);
      setSelectedFunction(null);
      toast.success('Function deleted successfully!');
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete function';
      toast.error(errorMessage);
    },
  });

  const handleDelete = () => {
    if (selectedFunction?._id) {
      deleteMutation.mutate(selectedFunction._id);
    }
  };

  const handleExport = async () => {
    try {
      const data = await api.exportFunctions();
      api.downloadJson(data, `dictionary-export-${new Date().toISOString().slice(0, 10)}.json`);
      toast.success('Dictionary exported successfully!');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to export dictionary';
      toast.error(errorMessage);
    }
  };

  const handleView = (func: DictionaryFunction) => {
    setSelectedFunction(func);
    setIsViewDialogOpen(true);
  };

  const handleDeleteClick = (func: DictionaryFunction) => {
    setSelectedFunction(func);
    setIsDeleteDialogOpen(true);
  };

  const filteredFunctions = Array.isArray(functions) ? functions.filter(func =>
    func?.function_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    func?.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    func?.category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (func?.tags && Array.isArray(func.tags) && func.tags.some(tag => tag?.toLowerCase().includes(searchTerm.toLowerCase())))
  ) : [];

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="text-destructive mb-4">
            <FileText className="h-12 w-12 mx-auto mb-2" />
            <h2 className="text-xl font-semibold">Failed to Load Dictionary</h2>
          </div>
          <p className="text-muted-foreground mb-4">
            Unable to load the function dictionary. Please try again.
          </p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['dictionary-functions'] })}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">Function Dictionary</h1>
          <p className="text-muted-foreground">
            Manage the function dictionary used by the Enhanced Rule Engine for text conversion
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button variant="outline">
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Function
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Functions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCount}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {functions.length > 0 ? new Set(functions.map(f => f?.category).filter(Boolean)).size : 0}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">High Confidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {functions.filter(f => f?.confidence_threshold && f.confidence_threshold >= 0.8).length}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Tags</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {functions.length > 0 ? new Set(functions.flatMap(f => f?.tags || []).filter(Boolean)).size : 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search & Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by name, description, category, or tags..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Functions Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Functions ({filteredFunctions.length})
              </CardTitle>
              <CardDescription>
                Dictionary functions available for text conversion
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Function Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Tags</TableHead>
                    <TableHead>Updated</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredFunctions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                        {searchTerm ? 'No functions found matching your search.' : 'No functions available.'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredFunctions.map((func) => (
                      <TableRow key={func?._id || Math.random()}>
                        <TableCell className="font-medium font-mono text-sm">
                          {func?.function_name || 'N/A'}
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          {func?.description || 'N/A'}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{func?.category || 'Unknown'}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            className={
                              (func?.confidence_threshold || 0) >= 0.8 
                                ? 'bg-green-500/10 text-green-700 dark:text-green-400'
                                : (func?.confidence_threshold || 0) >= 0.6
                                ? 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400'
                                : 'bg-red-500/10 text-red-700 dark:text-red-400'
                            }
                          >
                            {((func?.confidence_threshold || 0) * 100).toFixed(0)}%
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {(func?.tags || []).slice(0, 2).map((tag, index) => (
                              <Badge key={`${tag}-${index}`} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                            {(func?.tags || []).length > 2 && (
                              <Badge variant="secondary" className="text-xs">
                                +{(func?.tags || []).length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDate(func?.updated_at)}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleView(func)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteClick(func)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* View Function Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {selectedFunction?.function_name}
            </DialogTitle>
            <DialogDescription>
              Function details and configuration
            </DialogDescription>
          </DialogHeader>
          
          {selectedFunction && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Function Name</label>
                  <p className="font-mono text-sm mt-1 p-2 bg-muted rounded">
                    {selectedFunction.function_name}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Category</label>
                  <p className="mt-1">
                    <Badge variant="outline">{selectedFunction.category}</Badge>
                  </p>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">Description</label>
                <p className="mt-1 p-2 bg-muted rounded text-sm">
                  {selectedFunction.description}
                </p>
              </div>

              {/* Tags */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">Tags</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {(selectedFunction.tags || []).map((tag, index) => (
                    <Badge key={`${tag}-${index}`} variant="secondary">
                      <Tag className="h-3 w-3 mr-1" />
                      {tag}
                    </Badge>
                  ))}
                  {(!selectedFunction.tags || selectedFunction.tags.length === 0) && (
                    <p className="text-sm text-muted-foreground">No tags</p>
                  )}
                </div>
              </div>

              {/* Confidence Threshold */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">Confidence Threshold</label>
                <p className="mt-1">
                  <Badge 
                    className={
                      selectedFunction.confidence_threshold >= 0.8 
                        ? 'bg-green-500/10 text-green-700 dark:text-green-400'
                        : selectedFunction.confidence_threshold >= 0.6
                        ? 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400'
                        : 'bg-red-500/10 text-red-700 dark:text-red-400'
                    }
                  >
                    {(selectedFunction.confidence_threshold * 100).toFixed(0)}%
                  </Badge>
                </p>
              </div>

              {/* Templates */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">Templates</label>
                <div className="space-y-2 mt-1">
                  {(selectedFunction.templates || []).map((template, index) => (
                    <div key={index} className="p-2 bg-muted rounded text-sm font-mono">
                      {template}
                    </div>
                  ))}
                  {(!selectedFunction.templates || selectedFunction.templates.length === 0) && (
                    <p className="text-sm text-muted-foreground">No templates</p>
                  )}
                </div>
              </div>

              {/* Examples */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">Examples</label>
                <div className="space-y-2 mt-1">
                  {(selectedFunction.examples || []).map((example, index) => (
                    <div key={index} className="p-2 bg-muted rounded text-sm">
                      {example}
                    </div>
                  ))}
                  {(!selectedFunction.examples || selectedFunction.examples.length === 0) && (
                    <p className="text-sm text-muted-foreground">No examples</p>
                  )}
                </div>
              </div>

              {/* Arguments */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">Arguments</label>
                <pre className="mt-1 p-2 bg-muted rounded text-xs overflow-x-auto">
                  {JSON.stringify(selectedFunction.args, null, 2)}
                </pre>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>Created: {formatDate(selectedFunction.created_at)}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>Updated: {formatDate(selectedFunction.updated_at)}</span>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsViewDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Trash2 className="h-5 w-5" />
              Delete Function
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this function? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          
          {selectedFunction && (
            <div className="p-4 bg-muted rounded">
              <p className="font-medium">{selectedFunction.function_name}</p>
              <p className="text-sm text-muted-foreground mt-1">
                {selectedFunction.description}
              </p>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}