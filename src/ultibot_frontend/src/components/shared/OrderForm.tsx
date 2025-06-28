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
import { Input } from "@/components/base/Input";
import { Label } from "@/components/base/Label"; // I will create Label component next

interface OrderFormProps {
  onSubmit: (order: any) => void; // Placeholder for order type
}

const OrderForm: React.FC<OrderFormProps> = ({ onSubmit }) => {
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // Placeholder for form data handling
    const formData = new FormData(event.currentTarget as HTMLFormElement);
    const orderData = Object.fromEntries(formData.entries());
    onSubmit(orderData);
  };

  return (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Create Order</CardTitle>
        <CardDescription>Place a new trade order.</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent>
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="symbol">Symbol</Label>
              <Input id="symbol" name="symbol" placeholder="e.g., BTC/USDT" />
            </div>
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="quantity">Quantity</Label>
              <Input id="quantity" name="quantity" type="number" placeholder="0.00" />
            </div>
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="price">Price</Label>
              <Input id="price" name="price" type="number" placeholder="0.00" />
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button type="submit">Place Order</Button>
        </CardFooter>
      </form>
    </Card>
  );
};

export default OrderForm;
