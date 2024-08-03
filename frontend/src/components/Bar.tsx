import React from "react";
import "./Bar.css";

export const Bar = (props: { score: number }) => {
  const getColor = (score: number) => {
    if (score >= 7) {
      return "green";
    } else if (score >= 4 && score <= 6) {
      return "yellow";
    } else {
      return "red";
    }
  };

  const squares = Array.from({ length: props.score }, (_, index) => (
    <div key={index} className={`BarSquare ${getColor(props.score)}`} />
  ));

  return <div className="BarChart">{squares}</div>;
};
