import React, { useState, useEffect } from 'react';
import SplitText from "./SplitText";
import BlurText from "./BlurText";
import { CButton } from '@coreui/react';
import { Link } from "react-router-dom";
import FolderInputModal from './FolderInputModal';

const HomePage = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [accessToken, setAccessToken] = useState(localStorage.getItem('googleAccessToken') || '');
  const [isCategorizing, setIsCategorizing] = useState(false);
  const [isDuplicating, setIsDuplicating] = useState(false);

  const [modalVisible, setModalVisible] = useState(false);
  const [modalPurpose, setModalPurpose] = useState('');
  const [onModalSubmit, setOnModalSubmit] = useState(() => () => {});

  const openFolderModal = (purpose, onSubmit) => {
    setModalPurpose(purpose);
    setOnModalSubmit(() => onSubmit);
    setModalVisible(true);
  };

  const handleShowGalleryClick = async (folderName) => {
    try {
      const response = await fetch('http://localhost:5000/list-folders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ accessToken, folderName }),
      });

      const result = await response.json();

      if (response.ok && result.folderId) {
        window.open(`https://drive.google.com/drive/folders/${result.folderId}`, '_blank');
      } else {
        alert('Folder not found or an error occurred.');
      }
    } catch (err) {
      console.error('Fetch failed:', err.message);
      alert('Failed to open the folder. Try again.');
    }
    
  };

  const handleDeduplicationClick = async (folderName) => {
    try {
      setIsDuplicating(true);
      const response = await fetch('http://localhost:5000/run_duplication', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ accessToken, folderName }),
      });

      const result = await response.json();

      if (response.ok) {
        alert('Duplication Completed');
      } else {
        alert('Duplication failed: ' + result.error);
      }
    } catch (err) {
      console.error('Duplication failed:', err.message);
      alert('Failed to duplicate images.');
    } finally {
      setIsDuplicating(false);
    }
  };

  const handleCategorizeClick = async (folderName) => {
    try {
      setIsCategorizing(true);
      const response = await fetch('http://localhost:5000/categorize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ accessToken, folderName }),
      });

      const result = await response.json();

      if (response.ok) {
        alert('Categorization Completed');
      } else {
        alert('Categorization failed: ' + result.error);
      }
    } catch (err) {
      console.error('Categorization failed:', err.message);
      alert('Failed to categorize images.');
    }finally {
      setIsCategorizing(false);
    }
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100,
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useEffect(() => {
    const storedToken = localStorage.getItem('googleAccessToken');
    if (storedToken !== accessToken) {
      setAccessToken(storedToken || '');
    }
  }, [accessToken]);

  return (
    <div className="relative h-screen w-full overflow-hidden">
      <div 
        className="absolute inset-0 transition-all duration-1000 ease-in-out"
        style={{
          background: `
            radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(0, 128, 128, 0.4) 0%, transparent 40%),
            radial-gradient(circle at ${100 - mousePosition.x}% ${mousePosition.y}%, rgba(255, 0, 255, 0.4) 0%, transparent 40%),
            radial-gradient(circle at ${mousePosition.y}% ${mousePosition.x}%, rgba(255, 215, 0, 0.4) 0%, transparent 40%),
            linear-gradient(180deg, rgba(10, 10, 30, 0.95) 0%, rgba(10, 10, 30, 1) 100%)
          `,
          filter: 'blur(8px)',
        }}
      />

      <div className="h-screen w-full relative flex flex-col items-center justify-center">
        <div className="relative z-10 mt-8">
          <div className="px-12 py-4 rounded-full shadow-lg flex items-center justify-center space-x-12"
            style={{
              background: 'rgba(0, 0, 0, 0.3)',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)'
            }}
          >
            <Link to="/home" className="text-white text-lg font-medium">Home</Link>
            <Link to="/about-us" className="text-white text-lg font-medium">About Us</Link>
            <Link to="/contact-us" className="text-white text-lg font-medium">Contact Us</Link>
          </div>
        </div>

        <div className="flex-1 flex -mt-40 flex-col items-center justify-center space-y-4">
          <SplitText
            text="DUPFREE"
            className="text-8xl md:text-9xl lg:text-[12rem] xl:text-[15rem] font-bold text-white font-doodle"
            delay={200}
            animationFrom={{ opacity: 0, transform: 'translate3d(0,50px,0)' }}
            animationTo={{ opacity: 1, transform: 'translate3d(0,0,0)' }}
            easing="easeOutCubic"
          />
          <BlurText
            text="Because Every Memory Deserves Space"
            delay={150}
            animateBy="words"
            direction="top"
            className="text-5xl mb-8 text-white"
          />

          {!accessToken && (
            <div className="text-white text-xl mb-6">
              <p>Please log in with Google to use duplicate detection</p>
            </div>
          )}

          <div className="absolute bottom-20 flex gap-10 items-center justify-center z-30">
            <CButton
              onClick={() => openFolderModal("Find duplicates in folder", handleDeduplicationClick)}
              disabled={isDuplicating}
              className="text-xl px-8 py-3 text-white rounded-full bg-gradient-to-r from-pink-400 via-rose-500 to-fuchsia-500 hover:from-pink-500 hover:via-rose-600 hover:to-fuchsia-600 transition-all duration-300 disabled:opacity-50"
            >
              {isDuplicating ? 'Processing...' : 'Find Duplicates'}
            </CButton>

            <CButton
              onClick={() => openFolderModal("Open folder in Drive", handleShowGalleryClick)}
              className="text-xl px-8 py-3 text-white rounded-full bg-gradient-to-r from-pink-400 to-orange-500 hover:from-pink-500 hover:to-orange-600 transition-all duration-300"
            >
              Show Gallery
            </CButton>

            <CButton
              onClick={() => openFolderModal("Categorize folder images", handleCategorizeClick)}
              disabled={isCategorizing}
              className="text-xl px-8 py-3 text-white rounded-full bg-gradient-to-r from-violet-400 via-purple-500 to-indigo-600 hover:from-violet-500 hover:via-purple-600 hover:to-indigo-700 transition-all duration-300"
            >
              
            {isCategorizing ? 'Processing...' : 'Categorise'}
            </CButton>
          </div>
        </div>
      </div>

      <FolderInputModal
        isOpen={modalVisible}
        onClose={() => setModalVisible(false)}
        onSubmit={(folderName) => {
          setModalVisible(false);
          onModalSubmit(folderName);
        }}
        title={modalPurpose}
      />
    </div>
  );
};

export default HomePage;
