import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/base/Card";

interface ChartWrapperProps {
  title: string;
  children: React.ReactNode;
}

const ChartWrapper: React.FC<ChartWrapperProps> = ({ title, children }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-96 w-full">
          {/* Charting library will be rendered here */}
          {children}
        </div>
      </CardContent>
    </Card>
  );
};

export default ChartWrapper;
