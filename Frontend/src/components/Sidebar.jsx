import React, { useState } from 'react';
import {
  Home,
  Users,
  FileText,
  Menu,
  X,
  Bell,
  LogOut,
  Settings,
  PieChart,
  Database,
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';

const Sidebar = ({ isCollapsed, setIsCollapsed }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [showNotificationTooltip, setShowNotificationTooltip] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { icon: Home, label: 'Dashboard', path: '/' },
    { icon: FileText, label: 'Manage Contents', path: '/contentManagement' },
    { icon: PieChart, label: 'Stats and Report', path: '/analytics' },
    { icon: Users, label: 'Manage Users', path: '/users' },
    { icon: MessageCircle, label: 'Feedback', path: '/feedbackDisplay' },
    { icon: Database, label: 'Log', path: '/logs' },
    { icon: Settings, label: 'Settings', path: '/settings'}, // Special handling
  ];

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <div className="bg-gray-50">
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-3 sm:px-4 h-14 sm:h-16">
          <div className="flex items-center space-x-2 sm:space-x-4">
            <button
              onClick={toggleMobileMenu}
              className="lg:hidden p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {isMobileMenuOpen ? (
                <X size={18} className="text-gray-700 sm:w-5 sm:h-5" />
              ) : (
                <Menu size={18} className="text-gray-700 sm:w-5 sm:h-5" />
              )}
            </button>
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className="w-7 h-7 sm:w-8 sm:h-8 bg-[#F29F67] rounded flex items-center justify-center">
                <span className="text-white font-bold text-xs sm:text-sm">S</span>
              </div>
              {!isCollapsed && (
                <span className="font-bold text-gray-800 text-base sm:text-lg hidden sm:block">StarAdmin</span>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-1 sm:space-x-3">
            {/* Notification Icon with Tooltip */}
            <div className="relative">
              <button 
                className="p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 transition-colors relative"
                onMouseEnter={() => setShowNotificationTooltip(true)}
                onMouseLeave={() => setShowNotificationTooltip(false)}
              >
                <Bell size={18} className="text-gray-600 sm:w-5 sm:h-5" />
                <span className="absolute -top-0.5 -right-0.5 sm:-top-1 sm:-right-1 w-2.5 h-2.5 sm:w-3 sm:h-3 bg-red-500 rounded-full" />
              </button>
              
              {/* Tooltip */}
              {showNotificationTooltip && (
                <div className="absolute top-full right-0 mt-2 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg shadow-lg whitespace-nowrap z-50">
                  No newer notifications
                  <div className="absolute -top-1 right-4 w-2 h-2 bg-gray-800 rotate-45"></div>
                </div>
              )}
            </div>

            <button className="p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 transition-colors">
              <LogOut size={18} className="text-gray-600 sm:w-5 sm:h-5" />
            </button>
            <div className="w-7 h-7 sm:w-8 sm:h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <span className="text-gray-600 text-xs sm:text-sm font-medium">JD</span>
            </div>
          </div>
        </div>
      </nav>

      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={toggleMobileMenu}
        />
      )}

      <aside
        className={`
          fixed top-14 sm:top-16 left-0 h-[calc(100vh-3.5rem)] sm:h-[calc(100vh-4rem)] bg-white border-r border-gray-200 z-40 transition-all duration-300 ease-in-out overflow-y-auto
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
          ${isCollapsed ? 'w-16 sm:w-20' : 'w-56 sm:w-64'}
          lg:translate-x-0
        `}
      >
        <div className="p-3 sm:p-4">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="mb-3 sm:mb-4 p-2 sm:p-3 rounded-lg hover:bg-gray-100 transition-colors flex items-center justify-end w-full  lg:flex"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            <Menu size={18} className="text-gray-600 sm:w-5 sm:h-5" />
          </button>

          <nav className="space-y-1">
            {menuItems.map((item, index) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              if (item.isDropdown) {
                return (
                  <div key={index} className="relative">
                    <button
                      onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                      className={`
                        flex items-center px-2 sm:px-3 py-2 sm:py-2.5 rounded-lg transition-all duration-200 group w-full
                        ${isSettingsOpen ? 'bg-[#F29F67]/10 text-[#F29F67]' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'}
                      `}
                      title="Settings"
                    >
                      <Icon
                        size={16}
                        className={`sm:w-[18px] sm:h-[18px] ${
                          isSettingsOpen ? 'text-[#F29F67]' : 'text-gray-500 group-hover:text-gray-700'
                        }`}
                      />
                      {!isCollapsed && (
                        <span className="font-medium text-sm ml-2 sm:ml-3">Settings</span>
                      )}
                    </button>
                  </div>
                );
              }

              return (
                <a
                  key={index}
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(item.path);
                    setIsMobileMenuOpen(false);
                    setIsSettingsOpen(false);
                  }}
                  className={`
                    flex items-center px-2 sm:px-3 py-2 sm:py-2.5 rounded-lg transition-all duration-200 group relative
                    ${isActive
                      ? 'bg-[#F29F67]/10 text-[#F29F67] border-l-2 border-[#F29F67]'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'}
                  `}
                  title={item.label}
                >
                  <Icon
                    size={16}
                    className={`sm:w-[18px] sm:h-[18px] ${
                      isActive ? 'text-[#F29F67]' : 'text-gray-500 group-hover:text-gray-700'
                    }`}
                  />
                  {!isCollapsed && (
                    <span className="font-medium text-sm ml-2 sm:ml-3">{item.label}</span>
                  )}
                </a>
              );
            })}
          </nav>
        </div>
      </aside>
    </div>
  );
};

export default Sidebar;