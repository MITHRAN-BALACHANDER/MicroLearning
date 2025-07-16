// import React from "react";
import { TrendingUp } from "lucide-react";

export const getTrendIcon = (trend) => {
  switch (trend) {
    case "up":
      return <TrendingUp className="w-3 h-3 text-green-500" />;
    case "down":
      return <TrendingUp className="w-3 h-3 text-red-500 rotate-180" />;
    case "stable":
      return <div className="w-3 h-3 bg-gray-400 rounded-full" />;
    default:
      return null;
  }
};
