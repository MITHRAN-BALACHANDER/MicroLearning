import { createContext, useContext, useState, type ReactNode } from 'react'

interface ModalContextType {
  openVideoModal: (video?: any) => void
  openCategoryModal: (category?: any) => void
  openUserModal: (user?: any) => void
  closeModals: () => void
  videoModalOpen: boolean
  categoryModalOpen: boolean
  userModalOpen: boolean
  editingItem: any
}

const ModalContext = createContext<ModalContextType | undefined>(undefined)

export function ModalProvider({ children }: { children: ReactNode }) {
  const [videoModalOpen, setVideoModalOpen] = useState(false)
  const [categoryModalOpen, setCategoryModalOpen] = useState(false)
  const [userModalOpen, setUserModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<any>(null)

  const openVideoModal = (video?: any) => {
    setEditingItem(video || null)
    setVideoModalOpen(true)
  }

  const openCategoryModal = (category?: any) => {
    setEditingItem(category || null)
    setCategoryModalOpen(true)
  }

  const openUserModal = (user?: any) => {
    setEditingItem(user || null)
    setUserModalOpen(true)
  }

  const closeModals = () => {
    setVideoModalOpen(false)
    setCategoryModalOpen(false)
    setUserModalOpen(false)
    setEditingItem(null)
  }

  return (
    <ModalContext.Provider
      value={{
        openVideoModal,
        openCategoryModal,
        openUserModal,
        closeModals,
        videoModalOpen,
        categoryModalOpen,
        userModalOpen,
        editingItem,
      }}
    >
      {children}
    </ModalContext.Provider>
  )
}

export function useModal() {
  const context = useContext(ModalContext)
  if (context === undefined) {
    throw new Error('useModal must be used within a ModalProvider')
  }
  return context
}
