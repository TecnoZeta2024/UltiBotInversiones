import React from "react";
import { BentoCard, BentoGrid } from "@/components/magicui/bento-grid";
import ChartWrapper from "@/components/shared/ChartWrapper";
import { DataTable } from "@/components/shared/DataTable";
import OpportunityCard from "@/components/shared/OpportunityCard";
import TerminalPanel from "@/components/TerminalPanel";
import type { ColumnDef } from "@tanstack/react-table";
import { RocketIcon, BarChartIcon, TableIcon, CodeIcon } from "@radix-ui/react-icons";

// Define columns for DataTable
export const columns: ColumnDef<any>[] = [
    { accessorKey: "symbol", header: "Symbol" },
    { accessorKey: "price", header: "Price" },
    { accessorKey: "change", header: "Change" },
    { accessorKey: "volume", header: "Volume" },
];

// Mock data for DataTable - replace with actual data fetching
const mockData = [
  { id: "1", symbol: "BTC/USDT", price: 65000, change: "+2.5%", volume: 12000000 },
  { id: "2", symbol: "ETH/USDT", price: 3500, change: "-1.2%", volume: 8000000 },
];

const handleAnalyze = (id: string) => {
  console.log(`Analyzing opportunity ${id}`);
  // Placeholder for analyze logic
};

const handleExecute = (id: string) => {
  console.log(`Executing opportunity ${id}`);
  // Placeholder for execute logic
};

const features = [
  {
    Icon: BarChartIcon,
    name: "Portfolio Overview",
    description: "Visualize portfolio performance.",
    href: "#",
    cta: "View Details",
    className: "col-span-3 lg:col-span-2",
    background: (
      <ChartWrapper title="Portfolio Performance">
        <div>Chart Placeholder</div>
      </ChartWrapper>
    ),
  },
  {
    Icon: CodeIcon,
    name: "Live Terminal",
    description: "Real-time system logs.",
    href: "#",
    cta: "Open",
    className: "col-span-3 lg:col-span-1",
    background: <TerminalPanel />,
  },
  {
    Icon: RocketIcon,
    name: "Top Opportunities",
    description: "AI-driven trading signals.",
    href: "#",
    cta: "Analyze",
    className: "col-span-3 lg:col-span-1",
    background: (
      <div className="p-2 space-y-2 overflow-y-auto h-full flex flex-col items-center">
        <OpportunityCard 
          opportunity={{ id: '1', symbol: 'ADA/USDT', description: 'AI analysis suggests strong upward momentum.', potentialProfit: 150, aiConfidence: 0.85 }} 
          onAnalyze={handleAnalyze}
          onExecute={handleExecute}
        />
        <OpportunityCard 
          opportunity={{ id: '2', symbol: 'SOL/USDT', description: 'Nearing resistance level.', potentialProfit: 95, aiConfidence: 0.78 }} 
          onAnalyze={handleAnalyze}
          onExecute={handleExecute}
        />
      </div>
    ),
  },
  {
    Icon: TableIcon,
    name: "Market Data",
    description: "Live market prices and data.",
    href: "#",
    cta: "Explore",
    className: "col-span-3 lg:col-span-2",
    background: <DataTable columns={columns} data={mockData} />,
  },
];

export default function DashboardView() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <BentoGrid className="lg:grid-rows-2">
        {features.map((feature, idx) => (
          <BentoCard key={idx} {...feature} />
        ))}
      </BentoGrid>
    </div>
  );
}
