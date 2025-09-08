import { useState, useEffect, useCallback } from 'react';

export function useGlobalSearch() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const openModal = useCallback(() => {
    setIsModalOpen(true);
  }, []);
  
  const closeModal = useCallback(() => {
    setIsModalOpen(false);
  }, []);
  
  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Cmd+K (Mac) or Ctrl+K (Windows/Linux)
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        openModal();
      }
      
      // Close modal on Escape
      if (event.key === 'Escape' && isModalOpen) {
        event.preventDefault();
        closeModal();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isModalOpen, openModal, closeModal]);
  
  return {
    isModalOpen,
    openModal,
    closeModal
  };
}
