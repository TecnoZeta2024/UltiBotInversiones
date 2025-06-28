import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/base/Card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/base/Table";

// Mock data - replace with actual data fetching
const portfolioAssets = [
  { asset: 'Bitcoin', symbol: 'BTC', quantity: 1.5, value: 90000, allocation: '45%' },
  { asset: 'Ethereum', symbol: 'ETH', quantity: 10, value: 40000, allocation: '20%' },
  { asset: 'Cardano', symbol: 'ADA', quantity: 5000, value: 2500, allocation: '1.25%' },
  { asset: 'USDT', symbol: 'USDT', quantity: 67500, value: 67500, allocation: '33.75%' },
];

export default function PortfolioView() {
  return (
    <div className="p-4">
      <Card>
        <CardHeader>
          <CardTitle>Portfolio Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Asset</TableHead>
                <TableHead>Symbol</TableHead>
                <TableHead>Quantity</TableHead>
                <TableHead>Value (USD)</TableHead>
                <TableHead>Allocation</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {portfolioAssets.map((asset) => (
                <TableRow key={asset.symbol}>
                  <TableCell>{asset.asset}</TableCell>
                  <TableCell>{asset.symbol}</TableCell>
                  <TableCell>{asset.quantity}</TableCell>
                  <TableCell>${asset.value.toLocaleString()}</TableCell>
                  <TableCell>{asset.allocation}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
