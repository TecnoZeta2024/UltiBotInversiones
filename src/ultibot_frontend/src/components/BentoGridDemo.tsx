import React from "react";
import { BentoCard, BentoGrid } from "@/components/magicui/bento-grid";
import HealthCheckPanel from "./HealthCheckPanel";
import HighchartsPanel from "./HighchartsPanel";
import TerminalPanel from "./TerminalPanel";
import ConfidencePanel from "./ConfidencePanel";
import { FileTextIcon } from "@radix-ui/react-icons";

const features = [
  {
    Icon: FileTextIcon,
    name: "Health Check",
    description: "System health and status.",
    href: "/",
    cta: "Learn more",
    className: "col-span-3 lg:col-span-1",
    background: <HealthCheckPanel />,
  },
  {
    Icon: FileTextIcon,
    name: "Confidence",
    description: "AI confidence levels.",
    href: "/",
    cta: "Learn more",
    className: "col-span-3 lg:col-span-1",
    background: <ConfidencePanel />,
  },
  {
    Icon: FileTextIcon,
    name: "Terminal",
    description: "Live operational terminal.",
    href: "/",
    cta: "Learn more",
    className: "col-span-3 lg:col-span-1",
    background: <TerminalPanel />,
  },
  {
    Icon: FileTextIcon,
    name: "Highcharts",
    description: "Data visualization.",
    href: "/",
    cta: "Learn more",
    className: "col-span-3 lg:col-span-3",
    background: <HighchartsPanel />,
  },
];

export default function BentoGridDemo() {
  return (
    <BentoGrid className="lg:grid-rows-3">
      {features.map((feature, idx) => (
        <BentoCard key={idx} {...feature} />
      ))}
    </BentoGrid>
  );
}
