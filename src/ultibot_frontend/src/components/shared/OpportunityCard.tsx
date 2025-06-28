import * as React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/base/Card";
import { Button } from "@/components/base/Button";

// This is a placeholder interface. It will be replaced with the actual data model.
interface Opportunity {
  id: string;
  symbol: string;
  description: string;
  potentialProfit: number;
  aiConfidence: number;
}

interface OpportunityCardProps {
  opportunity: Opportunity;
  onAnalyze: (id: string) => void;
  onExecute: (id: string) => void;
}

const OpportunityCard: React.FC<OpportunityCardProps> = ({
  opportunity,
  onAnalyze,
  onExecute,
}) => {
  return (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>{opportunity.symbol}</CardTitle>
        <CardDescription>{opportunity.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid w-full items-center gap-4">
          <div className="flex flex-col space-y-1.5">
            <p>Potential Profit: <span className="font-bold">${opportunity.potentialProfit.toFixed(2)}</span></p>
            <p>AI Confidence: <span className="font-bold">{(opportunity.aiConfidence * 100).toFixed(1)}%</span></p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={() => onAnalyze(opportunity.id)}>
          Analyze
        </Button>
        <Button onClick={() => onExecute(opportunity.id)}>Execute</Button>
      </CardFooter>
    </Card>
  );
};

export default OpportunityCard;
