import React, { useState } from 'react';
import { X, FolderPlus } from 'lucide-react';

const FolderInputModal = ({ isOpen, onClose, onSubmit, title }) => {
  const [folderName, setFolderName] = useState('');

  const handleSubmit = () => {
    if (folderName.trim() !== '') {
      onSubmit(folderName);
      setFolderName('');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70">
      <div className="relative bg-gray-900 text-white p-6 rounded-xl w-full max-w-md shadow-lg border border-gray-700">
        <button
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition"
          onClick={onClose}
        >
          <X size={24} />
        </button>

        <div className="mb-6">
          <h2 className="text-2xl font-bold flex items-center">
            <FolderPlus className="mr-2" size={24} />
            {title || 'Enter Folder Name'}
          </h2>
        </div>

        <div className="mb-6">
          <label className="block text-sm text-gray-300 mb-2">Folder Name</label>
          <input
            type="text"
            className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700 focus:border-blue-500 focus:outline-none transition"
            placeholder="Type a folder name..."
            value={folderName}
            onChange={(e) => setFolderName(e.target.value)}
          />
        </div>

        <div className="flex justify-end space-x-4">
          <button
            className="px-4 py-2 rounded-lg text-gray-300 hover:text-white transition"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!folderName.trim()}
            className={`px-6 py-2 rounded-lg font-medium bg-gradient-to-r from-pink-500 to-violet-600 hover:from-pink-600 hover:to-violet-700 transition ${
              !folderName.trim() ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
};

export default FolderInputModal;
