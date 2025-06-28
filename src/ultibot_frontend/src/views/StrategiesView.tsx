import React, { useState, useEffect } from 'react';
import { File, Folder, Tree, type TreeViewElement } from "@/components/magicui/file-tree";
import { Card, CardContent } from "@/components/base/Card";
import apiClient from '@/lib/apiClient'; // Import the API client

const renderTree = (elements: TreeViewElement[], handleSelect: (id: string) => void): React.ReactNode => {
    return elements.map((element) => {
      if (element.children) {
        return (
          <Folder key={element.id} element={element.name} value={element.id}>
            {renderTree(element.children, handleSelect)}
          </Folder>
        );
      }
      return (
        <File key={element.id} value={element.id} handleSelect={() => handleSelect(element.id)}>
          {element.name}
        </File>
      );
    });
};

export default function StrategiesView() {
  const [strategies, setStrategies] = useState<TreeViewElement[]>([]);
  const [selectedFile, setSelectedFile] = useState<{id: string} | undefined>(undefined);
  const [activeFileContent, setActiveFileContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        setIsLoading(true);
        // NOTE: This endpoint does not exist yet. It needs to be created in the backend.
        const response = await apiClient.get('/strategies/files');
        setStrategies(response.data);
        setError(null);
      } catch (err) {
        setError("Failed to fetch strategies. Please make sure the backend is running.");
        console.error(err);
        // Fallback to mock data on error
        setStrategies([{ id: "error", name: "Error loading strategies" }]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStrategies();
  }, []);

  const handleSelect = async (id: string) => {
    // id is the full path of the file, which is what the backend needs
    setSelectedFile({id});
    try {
        // The backend endpoint is /strategies/files/{file_path:path}
        // We need to extract the relative path from the full id.
        const basePath = "src/ultibot_backend/strategies/";
        const relativePath = id.startsWith(basePath) ? id.substring(basePath.length) : id;

        const response = await apiClient.get(`/strategies/files/${relativePath}`);
        setActiveFileContent(response.data.content);
    } catch (err) {
        setActiveFileContent(`Could not load content for file: ${id}.`);
        console.error(err);
    }
  };

  return (
    <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4 h-[calc(100vh-80px)]">
      <div className="col-span-1">
        <h2 className="text-xl font-semibold mb-2">Strategy Files</h2>
        <Card className="h-full">
          <CardContent className="p-2">
            {isLoading ? (
              <p>Loading strategies...</p>
            ) : error ? (
              <p className="text-red-500">{error}</p>
            ) : (
              <Tree
                className="overflow-hidden rounded-md bg-background"
                initialSelectedId={selectedFile?.id}
                elements={strategies}
              >
                {renderTree(strategies, handleSelect)}
              </Tree>
            )}
          </CardContent>
        </Card>
      </div>
      <div className="col-span-2">
        <h2 className="text-xl font-semibold mb-2">Code Editor</h2>
        <Card className="h-full">
            <CardContent className="p-0 h-full">
                <textarea
                    className="w-full h-full p-4 bg-gray-900 text-green-400 font-mono rounded-md border-0 focus:ring-0"
                    value={activeFileContent}
                    onChange={(e) => setActiveFileContent(e.target.value)}
                    placeholder="Select a file to view its content..."
                    readOnly={!selectedFile} // Make it read-only until a file is selected
                />
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
