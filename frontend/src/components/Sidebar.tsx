import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Bot, PhoneCall, Settings, LogOut, Hexagon } from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Agents', path: '/agents', icon: Bot },
    { name: 'Call Logs', path: '/logs', icon: PhoneCall },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="w-[240px] h-full flex flex-col bg-white">
      {/* Top Section */}
      <div className="p-6 pb-8 flex items-center justify-start gap-3">
        <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-primary-light text-primary">
          <Hexagon className="w-5 h-5 fill-current" />
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-[15px] leading-tight text-textPrimary tracking-tight">Voice AI</span>
          <span className="text-[12px] text-textMuted leading-tight">Platform</span>
        </div>
      </div>

      {/* Nav Section */}
      <nav className="flex-1 flex flex-col gap-1 px-3">
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) => `
              flex items-center gap-3 px-3 py-2.5 rounded-lg text-[14px] font-medium transition-all
              ${isActive 
                ? 'bg-primary-light text-primary border-l-[3px] border-primary ml-[-12px] pl-[calc(0.75rem+9px)]' 
                : 'text-textMuted hover:bg-surface hover:text-textPrimary'}
            `}
          >
            <item.icon className="w-[18px] h-[18px]" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      {/* Bottom Section */}
      <div className="p-4 border-t border-border mt-auto">
        <button className="flex items-center gap-3 px-3 py-2.5 w-full text-left rounded-lg text-textMuted hover:bg-surface hover:text-textPrimary transition-all text-[14px] font-medium">
          <LogOut className="w-[18px] h-[18px]" />
          Sign Out
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
