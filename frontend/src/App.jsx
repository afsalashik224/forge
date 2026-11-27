import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import CommandPalette from './components/CommandPalette';
import CreateConceptModal from './components/CreateConceptModal';
import EditConceptModal from './components/EditConceptModal';
import DeleteConfirmationModal from './components/DeleteConfirmationModal';
import ConceptReaderModal from './components/ConceptReaderModal';
import CreateWorkspaceModal from './components/CreateWorkspaceModal';
import EditWorkspaceModal from './components/EditWorkspaceModal';
import CreateRepositoryModal from './components/CreateRepositoryModal';
import EditRepositoryModal from './components/EditRepositoryModal';
import AssociateConceptModal from './components/AssociateConceptModal';
import Toast from './components/Toast';

import KnowledgeWorkspace from './pages/KnowledgeWorkspace';
import ForgeLibrary from './pages/ForgeLibrary';
import WorkspaceManager from './pages/WorkspaceManager';
import ForgeCompass from './pages/ForgeCompass';
import RepositoryProgress from './pages/RepositoryProgress';
import AdrTracker from './pages/AdrTracker';

import { 
  fetchConcepts, 
  fetchHealthStatus, 
  fetchWorkspaces, 
  fetchRepositories,
  deleteWorkspace,
  deleteRepository
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('workspace');
  const [concepts, setConcepts] = useState([]);
  const [workspaces, setWorkspaces] = useState([]);
  const [repositories, setRepositories] = useState([]);
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Concept modal states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingConcept, setEditingConcept] = useState(null);
  const [deletingConcept, setDeletingConcept] = useState(null);
  const [selectedConcept, setSelectedConcept] = useState(null);

  // Workspace & Repository modal states
  const [isCreateWorkspaceOpen, setIsCreateWorkspaceOpen] = useState(false);
  const [editingWorkspace, setEditingWorkspace] = useState(null);
  const [isCreateRepoOpen, setIsCreateRepoOpen] = useState(false);
  const [editingRepo, setEditingRepo] = useState(null);
  const [associatingConceptRepo, setAssociatingConceptRepo] = useState(null);

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
      const [conceptsData, healthData, workspacesData, repositoriesData] = await Promise.all([
        fetchConcepts(),
        fetchHealthStatus(),
        fetchWorkspaces().catch(() => []),
        fetchRepositories().catch(() => []),
      ]);
      setConcepts(Array.isArray(conceptsData) ? conceptsData : []);
      setHealthStatus(healthData);
      setWorkspaces(Array.isArray(workspacesData) ? workspacesData : []);
      setRepositories(Array.isArray(repositoriesData) ? repositoriesData : []);
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
    if (selectedConcept && (selectedConcept.id === updatedConcept.id || selectedConcept.slug === updatedConcept.slug)) {
      setSelectedConcept(updatedConcept);
    }
  };

  const handleConceptDeleted = (deletedConcept) => {
    loadData();
    if (selectedConcept && (selectedConcept.id === deletedConcept.id || selectedConcept.slug === deletedConcept.slug)) {
      setSelectedConcept(null);
    }
  };

  const handleDeleteWorkspace = async (ws) => {
    if (window.confirm(`Are you sure you want to delete workspace '${ws.name}'? Associated repositories will not be deleted.`)) {
      try {
        await deleteWorkspace(ws.slug);
        showToast(`Workspace '${ws.name}' deleted.`, "success");
        loadData();
      } catch (err) {
        showToast(err.message || "Failed to delete workspace.", "error");
      }
    }
  };

  const handleDeleteRepository = async (repo) => {
    if (window.confirm(`Are you sure you want to delete repository '${repo.name}'?`)) {
      try {
        await deleteRepository(repo.slug);
        showToast(`Repository '${repo.name}' deleted.`, "success");
        loadData();
      } catch (err) {
        showToast(err.message || "Failed to delete repository.", "error");
      }
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
              workspaces={workspaces}
              repositories={repositories}
              onSelectConcept={setSelectedConcept}
              onOpenCreateModal={() => setIsCreateModalOpen(true)}
              onEditConcept={setEditingConcept}
              onDeleteConcept={setDeletingConcept}
              loading={loading}
              error={error}
            />
          )}

          {activeTab === 'workspaces' && (
            <WorkspaceManager
              workspaces={workspaces}
              repositories={repositories}
              concepts={concepts}
              onOpenCreateWorkspace={() => setIsCreateWorkspaceOpen(true)}
              onOpenEditWorkspace={setEditingWorkspace}
              onDeleteWorkspace={handleDeleteWorkspace}
              onOpenCreateRepository={() => setIsCreateRepoOpen(true)}
              onOpenEditRepository={setEditingRepo}
              onDeleteRepository={handleDeleteRepository}
              onOpenAssociateConcept={setAssociatingConceptRepo}
              onSelectConcept={setSelectedConcept}
              loading={loading}
            />
          )}

          {activeTab === 'compass' && <ForgeCompass />}

          {activeTab === 'progress' && (
            <RepositoryProgress conceptsCount={concepts.length} />
          )}

          {activeTab === 'adrs' && <AdrTracker />}
        </main>
      </div>

      {/* Concept Modals */}
      <CreateConceptModal 
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={loadData}
        showToast={showToast}
        availableRepositories={repositories}
      />

      <EditConceptModal 
        isOpen={!!editingConcept}
        concept={editingConcept}
        onClose={() => setEditingConcept(null)}
        onUpdated={handleConceptUpdated}
        showToast={showToast}
        availableRepositories={repositories}
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

      {/* Workspace & Repository Modals */}
      <CreateWorkspaceModal
        isOpen={isCreateWorkspaceOpen}
        onClose={() => setIsCreateWorkspaceOpen(false)}
        onWorkspaceCreated={() => {
          showToast("Workspace created successfully.");
          loadData();
        }}
        availableRepositories={repositories}
      />

      <EditWorkspaceModal
        isOpen={!!editingWorkspace}
        workspace={editingWorkspace}
        onClose={() => setEditingWorkspace(null)}
        onWorkspaceUpdated={() => {
          showToast("Workspace updated successfully.");
          loadData();
        }}
        availableRepositories={repositories}
      />

      <CreateRepositoryModal
        isOpen={isCreateRepoOpen}
        onClose={() => setIsCreateRepoOpen(false)}
        onRepositoryCreated={() => {
          showToast("Repository added successfully.");
          loadData();
        }}
        availableWorkspaces={workspaces}
        availableConcepts={concepts}
      />

      <EditRepositoryModal
        isOpen={!!editingRepo}
        repository={editingRepo}
        onClose={() => setEditingRepo(null)}
        onRepositoryUpdated={() => {
          showToast("Repository updated successfully.");
          loadData();
        }}
        availableWorkspaces={workspaces}
        availableConcepts={concepts}
      />

      <AssociateConceptModal
        isOpen={!!associatingConceptRepo}
        repository={associatingConceptRepo}
        availableConcepts={concepts}
        onClose={() => setAssociatingConceptRepo(null)}
        onAssociationChanged={() => {
          showToast("Concept associations updated.");
          loadData();
        }}
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
