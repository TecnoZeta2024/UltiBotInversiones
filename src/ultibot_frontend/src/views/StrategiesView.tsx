import React, { useState } from 'react';
import { File, Folder, Tree, type TreeViewElement } from "@/components/magicui/file-tree";
import { Card, CardContent } from "@/components/base/Card";

// Mock data for FileTree - replace with actual data from the backend
const STRATEGIES_FILES: TreeViewElement[] = [
  {
    id: "1",
    name: "strategies",
    children: [
      {
        id: "2",
        name: "long_term",
        children: [
          { id: "3", name: "mean_reversion.py" },
          { id: "4", name: "momentum_dca.py" },
        ],
      },
      {
        id: "5",
        name: "short_term",
        children: [
          { id: "6", name: "scalping_rsi.py" },
          { id: "7", name: "arbitrage_bot.py" },
        ],
      },
       { id: "8", name: "custom_strategy.py" },
    ],
  },
];

// Mock content for files - replace with actual file content fetching
const fileContents: { [key: string]: string } = {
    "3": "print('Mean Reversion Strategy')",
    "4": "print('Momentum DCA Strategy')",
    "6": "print('Scalping RSI Strategy')",
    "7": "print('Arbitrage Bot Strategy')",
    "8": "print('Custom Strategy')",
};

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
  const [selectedFile, setSelectedFile] = useState<string | undefined>(undefined);
  const [activeFileContent, setActiveFileContent] = useState("");

  const handleSelect = (id: string) => {
    setSelectedFile(id);
    setActiveFileContent(fileContents[id] || `Content for ${id} not found.`);
  };

  return (
    <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4 h-[calc(100vh-80px)]">
      <div className="col-span-1">
        <h2 className="text-xl font-semibold mb-2">Strategy Files</h2>
        <Card className="h-full">
          <CardContent className="p-2">
            <Tree
              className="overflow-hidden rounded-md bg-background"
              initialSelectedId={selectedFile}
              elements={STRATEGIES_FILES}
            >
              {renderTree(STRATEGIES_FILES, handleSelect)}
            </Tree>
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
                />
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
