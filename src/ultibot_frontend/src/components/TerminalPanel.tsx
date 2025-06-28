import React from 'react';
import { Terminal, AnimatedSpan, TypingAnimation } from "@/components/magicui/terminal";

const TerminalPanel: React.FC = () => {
  return (
    <Terminal>
      <TypingAnimation>{`> npm run dev`}</TypingAnimation>
      <AnimatedSpan delay={1500} className="text-green-500">
        <span>✔ Backend connected.</span>
      </AnimatedSpan>
      <AnimatedSpan delay={2000} className="text-green-500">
        <span>✔ Highcharts rendered.</span>
      </AnimatedSpan>
      <AnimatedSpan delay={2500} className="text-green-500">
        <span>✔ Magic UI components loaded.</span>
      </AnimatedSpan>
      <TypingAnimation delay={3500} className="text-muted-foreground">
        PoC validation successful.
      </TypingAnimation>
    </Terminal>
  );
}

export default TerminalPanel;
