import React from "react";
import "./Button.css";
import { useState } from "react";
import checkmark from "../assets/checkmark.svg";

export const Button = (props) => {
  const bruh = props.text;
  const [active, setactive] = useState(false);
  const className = active ? "multi-select-filled" : "multi-select-unfilled";
  const showCheck = active ? "showCheck" : "hideCheck";

  const handleClick = () => {
    setactive(!active);
    props.onClick();
  };
  return (
    <div className="button" onClick={handleClick}>
      <div className={className}>
        <img className={showCheck} src={checkmark} />
        {bruh}
      </div>
    </div>
  );
};
