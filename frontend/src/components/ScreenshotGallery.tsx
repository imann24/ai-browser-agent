import React, { useState, useEffect } from 'react';
import { ScreenshotData } from './ChatContainer';

interface ScreenshotGalleryProps {
  screenshots: ScreenshotData[];
}

const ScreenshotGallery: React.FC<ScreenshotGalleryProps> = ({ screenshots }) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [gallery] = useState<string>(`gallery-${Date.now()}`);

  useEffect(() => {
    // When screenshots are added, show the latest one
    setActiveIndex(screenshots.length - 1);
  }, [screenshots.length]);

  const showSlide = (index: number) => {
    if (index < 0) index = 0;
    if (index >= screenshots.length) index = screenshots.length - 1;
    setActiveIndex(index);
  };

  return (
    <div className="my-4 w-full" id={gallery}>
      <div className="border border-gray-700 dark:border-gray-700 rounded-lg overflow-hidden bg-black/5 dark:bg-black/30">
        <div className="relative">
          {screenshots.map((screenshot, index) => (
            <div
              key={index}
              className={`flex flex-col items-center ${
                index === activeIndex ? 'block' : 'hidden'
              }`}
              data-index={index}
            >
              <img
                src={`data:image/png;base64,${screenshot.image}`}
                className="max-w-full h-auto max-h-[600px] object-contain"
                alt="Browser screenshot"
              />
              <div className="text-sm mt-2 text-center p-2 text-gray-200 dark:text-gray-300">
                {screenshot.description}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {screenshots.length > 1 && (
        <>
          <div className="flex justify-center mt-2 gap-2 flex-wrap p-1">
            <button
              className="bg-gray-800 text-white border border-gray-700 rounded px-2 py-1 text-sm disabled:opacity-50"
              onClick={() => showSlide(0)}
              disabled={activeIndex === 0}
            >
              &laquo; First
            </button>
            <button
              className="bg-gray-800 text-white border border-gray-700 rounded px-2 py-1 text-sm disabled:opacity-50"
              onClick={() => showSlide(activeIndex - 1)}
              disabled={activeIndex === 0}
            >
              &lsaquo; Prev
            </button>
            <button
              className="bg-gray-800 text-white border border-gray-700 rounded px-2 py-1 text-sm disabled:opacity-50"
              onClick={() => showSlide(activeIndex + 1)}
              disabled={activeIndex === screenshots.length - 1}
            >
              Next &rsaquo;
            </button>
            <button
              className="bg-gray-800 text-white border border-gray-700 rounded px-2 py-1 text-sm disabled:opacity-50"
              onClick={() => showSlide(screenshots.length - 1)}
              disabled={activeIndex === screenshots.length - 1}
            >
              Last &raquo;
            </button>
          </div>
          
          <div className="flex justify-center gap-1 mt-2">
            {screenshots.map((_, index) => (
              <div
                key={index}
                className={`w-3 h-3 rounded-full cursor-pointer transition-all ${
                  index === activeIndex
                    ? 'bg-blue-500 transform scale-110'
                    : 'bg-gray-300 dark:bg-gray-300 opacity-70'
                }`}
                onClick={() => showSlide(index)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default ScreenshotGallery; 
