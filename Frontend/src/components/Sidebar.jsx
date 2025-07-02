import React, { useState } from 'react';
import { 
  Home, 
  Users, 
  BarChart3, 
  Settings, 
  Mail, 
  Calendar, 
  FileText, 
  Menu,
  X,
  Bell,
  Search,
  ChevronDown,
  Target,
  Database,
  PieChart,
  Activity,
  UserCheck,
  Layers,
  Shield,
  UserPlus,
  LogOut
} from 'lucide-react';

const StarAdminLayout = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeMenuItem, setActiveMenuItem] = useState('Dashboard');

  const menuItems = [
    { icon: Home, label: 'Dashboard' },
    { icon: FileText, label: 'Manage Contents' },
    { icon: PieChart, label: 'Stats and Report'},
    { icon: Users, label: 'Manage Users' },
    { icon: Settings, label: 'Settings' },
    { icon: Database, label: 'Log' },
   
   /*
    { 
      label: 'CONTENT MANAGEMENT',
      isHeader: true
    },
    { icon: Target, label: 'Target settings'},
    { icon: Database, label: 'Data reporting' },
    { icon: PieChart, label: 'Reports/Analytics' },
    { icon: Activity, label: 'Manage activities' },
    { 
      label: 'USERS MANAGEMENT',
      isHeader: true
    },
    { icon: Layers, label: 'Departments & Activities' },
    { icon: Settings, label: 'States' },
    { icon: Calendar, label: 'Term and period' },
    { 
      label: 'ANALYTICS & REPORTS',
      isHeader: true
    },
    { icon: Users, label: 'Manage users' },
    { icon: UserCheck, label: 'Manage roles' },
    { icon: Shield, label: 'Manage hierarchy' },
    { icon: UserPlus, label: 'Manage leaders' },
    { icon: FileText, label: 'Member types' }, */
  ]; 

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-4 h-16">
          {/* Left side - Logo and menu toggle */}
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleMobileMenu}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {isMobileMenuOpen ? <X size={20} className='text-gray-700'/> : <Menu size={20} className='text-gray-700'/>}
            </button>

            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-[#F29F67] rounded flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <span className="font-bold text-gray-800 text-lg">StarAdmin</span>
            </div>
          </div>

          {/* Right side - Actions and profile */}
          <div className="flex items-center space-x-3">
            <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors relative">
              <Bell size={20} className="text-gray-600" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
            </button>

            <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
              <LogOut size={20} className="text-gray-600" />
            </button>

            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
              <span className="text-gray-600 text-sm font-medium">JD</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Sidebar Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={toggleMobileMenu}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-16 left-0 h-[calc(100vh-4rem)] bg-white border-r border-gray-200 z-40 transition-all duration-300 ease-in-out overflow-y-auto w-64
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
        <div className="p-4">
          <nav className="space-y-1">
            {menuItems.map((item, index) => {
              if (item.isHeader) {
                return (
                  <div 
                    key={index} 
                    className="mt-6 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider"
                  >
                    {item.label}
                  </div>
                );
              }

              const Icon = item.icon;
              const isActive = activeMenuItem === item.label;
              
              return (
                <a
                  key={index}
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setActiveMenuItem(item.label);
                    setIsMobileMenuOpen(false);
                  }}
                  className={`
                    flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 group relative
                    ${isActive 
                      ? 'bg-[#F29F67]/20 text-[#F29F67] border-l-2 border-[#F29F67]' 
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                    }
                  `}
                  title={item.label}
                >
                  <Icon 
                    size={18} 
                    className={`
                      ${isActive ? 'text-[#F29F67]' : 'text-gray-500 group-hover:text-gray-700'}
                    `} 
                  />
                  <span className="font-medium text-sm ml-3">{item.label}</span>
                </a>
              );
            })}
          </nav>
        </div>
      </aside>
    </div>
  );
};

export default StarAdminLayout;