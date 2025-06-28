import React from 'react';
import { AnimatedCircularProgressBar } from "@/components/magicui/animated-circular-progress-bar";

const ConfidencePanel: React.FC = () => {
  return (
    <div className="flex items-center justify-center h-full">
      <AnimatedCircularProgressBar
        max={100}
        min={0}
        value={75}
        gaugePrimaryColor="rgb(79 70 229)"
        gaugeSecondaryColor="rgba(0, 0, 0, 0.1)"
      />
    </div>
  );
}

export default ConfidencePanel;
