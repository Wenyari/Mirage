import './ThreeDCubeTitle.css';

import React from 'react';

const CHARS = ['G', 'O', ' ', 'G', 'E', 'N', 'E', 'R', 'A', 'T', 'E'];

export const ThreeDCubeTitle = () => {
  return (
    <div className="landing-title-wrapper">
      {CHARS.map((char, index) => (
        <div key={index} className="landing-title-cube">
          <div className="landing-title-face landing-title-face-front">{char}</div>
          <div className="landing-title-face landing-title-face-back" />
          <div className="landing-title-face landing-title-face-right" />
          <div className="landing-title-face landing-title-face-left" />
          <div className="landing-title-face landing-title-face-top" />
          <div className="landing-title-face landing-title-face-bottom" />
        </div>
      ))}
    </div>
  );
};
