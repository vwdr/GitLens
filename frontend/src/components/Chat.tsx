import React from 'react';
import './Chat.css'; // Import CSS file for styling
import arrowup from "../assets/arrowup.svg";

export const Chat = () => {
  return (
    <div className="input-container">
      <input type="text" placeholder="What do you want to know..." />
      <img src={arrowup} alt="Icon" className="icon" />
    </div>
  );
}