import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/base/Card";

// Mock data - replace with actual data fetching
const opportunityDetail = {
  symbol: 'BTC/USDT',
  exchange: 'Binance',
  entryPrice: 60000,
  targetPrice: 65000,
  stopLoss: 58000,
  strategy: 'Momentum DCA',
  aiAnalysis: 'The AI model predicts a high probability of an upward trend based on recent volume spikes and positive market sentiment. The recommended entry point is optimal for the current market structure.',
  status: 'Active'
};

export default function OpportunityDetailView() {
  return (
    <div className="p-4">
      <Card>
        <CardHeader>
          <CardTitle>Opportunity Detail: {opportunityDetail.symbol}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid grid-cols-2 gap-2">
            <div><strong>Exchange:</strong> {opportunityDetail.exchange}</div>
            <div><strong>Status:</strong> <span className="text-green-500">{opportunityDetail.status}</span></div>
            <div><strong>Entry Price:</strong> ${opportunityDetail.entryPrice}</div>
            <div><strong>Target Price:</strong> ${opportunityDetail.targetPrice}</div>
            <div><strong>Stop Loss:</strong> ${opportunityDetail.stopLoss}</div>
            <div><strong>Strategy:</strong> {opportunityDetail.strategy}</div>
          </div>
          <div>
            <h3 className="font-semibold">AI Analysis</h3>
            <p className="text-sm text-gray-400 mt-1">{opportunityDetail.aiAnalysis}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
