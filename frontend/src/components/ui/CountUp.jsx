import { animate, useMotionValue } from "framer-motion";
import { useEffect, useState } from "react";

function formatValue(value, prefix, suffix, decimals) {
  return `${prefix}${Number(value).toFixed(decimals)}${suffix}`;
}

export default function CountUp({ value, suffix = "", prefix = "", decimals = 0, className = "" }) {
  const motionValue = useMotionValue(0);
  const [displayValue, setDisplayValue] = useState(formatValue(0, prefix, suffix, decimals));

  useEffect(() => {
    setDisplayValue(formatValue(0, prefix, suffix, decimals));

    const controls = animate(motionValue, value, {
      duration: 1.2,
      ease: "easeOut",
      onUpdate: (latest) => {
        setDisplayValue(formatValue(latest, prefix, suffix, decimals));
      },
    });

    return () => controls.stop();
  }, [decimals, motionValue, prefix, suffix, value]);

  return <span className={className}>{displayValue}</span>;
}
