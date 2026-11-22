import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import CommandPalette from './components/CommandPalette';
import CreateConceptModal from './components/CreateConceptModal';
import EditConceptModal from './components/EditConceptModal';
import DeleteConfirmationModal from './components/DeleteConfirmationModal';
import ConceptReaderModal from './components/ConceptReaderModal';
import Toast from './components/Toast';

import KnowledgeWorkspace from './pages/KnowledgeWorkspace';
import ForgeLibrary from './pages/ForgeLibrary';
import ForgeCompass from './pages/ForgeCompass';
import RepositoryProgress from './pages/RepositoryProgress';
import AdrTracker from './pages/AdrTracker';

import { fetchConcepts, fetchHealthStatus } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('workspace');
  const [concepts, setConcepts] = useState([]);
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingConcept, setEditingConcept] = useState(null);
  const [deletingConcept, setDeletingConcept] = useState(null);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [conceptsData, healthData] = await Promise.all([
        fetchConcepts(),
        fetchHealthStatus()
      ]);
      setConcepts(Array.isArray(conceptsData) ? conceptsData : []);
      setHealthStatus(healthData);
    } catch (err) {
      console.error("App load error:", err);
      setError("Failed to connect to Forge API backend.");
      showToast("Unable to reach Flask backend server.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleConceptUpdated = (updatedConcept) => {
    loadData();
    // Propagate updated data and slug changes to open reader modal if active
    if (selectedConcept && (selectedConcept.id === updatedConcept.id || selectedConcept.slug === updatedConcept.slug)) {
      setSelectedConcept(updatedConcept);
    }
  };

  const handleConceptDeleted = (deletedConcept) => {
    loadData();
    // If deleted concept was open in reader, close reader modal
    if (selectedConcept && (selectedConcept.id === deletedConcept.id || selectedConcept.slug === deletedConcept.slug)) {
      setSelectedConcept(null);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div style={{ display: 'flex', height: '100vh', maxHeight: '100vh', overflow: 'hidden', backgroundColor: 'var(--bg-main)' }}>
      {/* Primary Fixed Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        conceptCount={concepts.length}
        isMobileOpen={isMobileOpen}
        onCloseMobile={() => setIsMobileOpen(false)}
      />

      {/* Right Content Area Pane */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', minWidth: 0 }}>
        <Header 
          activeTab={activeTab}
          onOpenCreateModal={() => setIsCreateModalOpen(true)}
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          onOpenMobileSidebar={() => setIsMobileOpen(true)}
          healthStatus={healthStatus}
        />

        {/* Independently Scrollable Main Content Pane */}
        <main style={{ flex: 1, overflowY: 'auto' }}>
          {activeTab === 'workspace' && (
            <KnowledgeWorkspace 
              concepts={concepts}
              healthStatus={healthStatus}
              onSelectConcept={setSelectedConcept}
              onOpenCreateModal={() => setIsCreateModalOpen(true)}
              onEditConcept={setEditingConcept}
              onDeleteConcept={setDeletingConcept}
              setActiveTab={setActiveTab}
              loading={loading}
            />
          )}

          {activeTab === 'library' && (
            <ForgeLibrary 
              concepts={concepts}
              onSelectConcept={setSelectedConcept}
              onOpenCreateModal={() => setIsCreateModalOpen(true)}
              onEditConcept={setEditingConcept}
              onDeleteConcept={setDeletingConcept}
              loading={loading}
              error={error}
            />
          )}

          {activeTab === 'compass' && <ForgeCompass />}

          {activeTab === 'progress' && (
            <RepositoryProgress conceptsCount={concepts.length} />
          )}

          {activeTab === 'adrs' && <AdrTracker />}
        </main>
      </div>

      {/* Modals & Overlays */}
      <CreateConceptModal 
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={loadData}
        showToast={showToast}
      />

      <EditConceptModal 
        isOpen={!!editingConcept}
        concept={editingConcept}
        onClose={() => setEditingConcept(null)}
        onUpdated={handleConceptUpdated}
        showToast={showToast}
      />

      <DeleteConfirmationModal 
        isOpen={!!deletingConcept}
        concept={deletingConcept}
        onClose={() => setDeletingConcept(null)}
        onDeleted={handleConceptDeleted}
        showToast={showToast}
      />

      <ConceptReaderModal 
        concept={selectedConcept}
        onClose={() => setSelectedConcept(null)}
        onEdit={setEditingConcept}
        onDelete={setDeletingConcept}
      />

      <CommandPalette 
        isOpen={isCommandPaletteOpen}
        onOpen={() => setIsCommandPaletteOpen(true)}
        onClose={() => setIsCommandPaletteOpen(false)}
        concepts={concepts}
        setActiveTab={setActiveTab}
        onSelectConcept={setSelectedConcept}
      />

      {/* Toast Notification Banner */}
      <Toast 
        message={toast.message} 
        type={toast.type} 
        onClose={() => setToast({ message: '', type: 'success' })} 
      />
    </div>
  );
}
