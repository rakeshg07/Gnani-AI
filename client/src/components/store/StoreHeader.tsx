import React, { useState } from 'react';
import {
  ShoppingBag,
  Search,
  ShoppingCart,
  Mic,
  MapPin,
  ChevronDown,
  Sparkles,
  Sun,
  Moon,
  Menu,
  X,
  Package,
  Languages,
  Check,
  ChevronRight,
  User as UserIcon,
  LogOut,
  LogIn,
} from 'lucide-react';
import { Category, Cart } from '@/types';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';

interface StoreHeaderProps {
  categories: Category[];
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSearchSubmit: () => void;
  cart: Cart | null;
  onOpenCart: () => void;
  onOpenOrders: () => void;
  onOpenVoiceAssistant: () => void;
  selectedLanguage: string;
  onSelectLanguage: (lang: string) => void;
  supportedLanguages: Array<{ code: string; name: string; native: string }>;
}

export const StoreHeader: React.FC<StoreHeaderProps> = ({
  categories,
  selectedCategory,
  onSelectCategory,
  searchQuery,
  onSearchChange,
  onSearchSubmit,
  cart,
  onOpenCart,
  onOpenOrders,
  onOpenVoiceAssistant,
  selectedLanguage,
  onSelectLanguage,
  supportedLanguages,
}) => {
  const { theme, toggleTheme } = useTheme();
  const { user, logout, openAuthModal } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const cartItemCount = cart?.item_count || 0;

  return (
    <>
      <header className="sticky top-0 z-40 bg-white/95 dark:bg-[#0c0a09]/95 backdrop-blur-md border-b border-amber-200/60 dark:border-stone-800 shadow-sm transition-colors duration-200">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 dark:from-[#0c0a09] dark:via-[#14100c] dark:to-[#0c0a09] py-1.5 px-3 sm:px-4 typo-label normal-case font-medium text-stone-700 dark:text-stone-300 border-b border-amber-200/50 dark:border-stone-800/80 transition-colors">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 sm:gap-2 truncate">
            <span className="flex h-2 w-2 rounded-full bg-orange-500 animate-pulse shrink-0" />
            <span className="font-bold text-stone-900 dark:text-white shrink-0">VoiceIQ India</span>
            <span className="text-stone-400 hidden md:inline">|</span>
            <span className="text-stone-600 dark:text-stone-400 hidden md:inline truncate">
              Multilingual Voice Customer Support powered by Sovereign Gnani AI (Prisma STT &amp; Timbre TTS)
            </span>
          </div>

          <div className="flex items-center gap-2 sm:gap-4 shrink-0">
            <span className="text-orange-600 dark:text-amber-400 font-bold flex items-center gap-1 typo-label normal-case">
              <Sparkles className="h-3 w-3 sm:h-3.5 sm:w-3.5 text-amber-500 dark:text-yellow-400 shrink-0" />
              <span>FREE Delivery &gt; ₹999</span>
            </span>
            <div className="hidden sm:flex items-center gap-1 text-stone-600 dark:text-stone-400 typo-label normal-case">
              <MapPin className="h-3 w-3 text-orange-500 shrink-0" />
              <span>
                Deliver to{' '}
                <strong>
                  {user
                    ? `${user.name.split(' ')[0]}, ${user.postal_code || user.city || '560001'}`
                    : 'India • Sovereign Store'}
                </strong>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Navbar */}
      <div className="max-w-7xl mx-auto px-3 sm:px-4 py-2 sm:py-3">
        <div className="flex items-center justify-between gap-2 sm:gap-4">
          {/* Mobile Menu Button + Logo */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            {/* Hamburger Menu Button for Phone */}
            <button
              id="mobile-menu-trigger"
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-xl text-stone-700 dark:text-stone-300 hover:text-orange-600 dark:hover:text-amber-400 hover:bg-amber-100/60 dark:hover:bg-[#1c140c] border border-amber-200/80 dark:border-stone-800 transition-colors cursor-pointer flex items-center justify-center shrink-0"
              title="Open Navigation Menu"
              aria-label="Open Navigation Menu"
            >
              <Menu className="h-5 w-5 text-orange-500" />
            </button>

            {/* Logo */}
            <div className="flex items-center gap-2 sm:gap-3 cursor-pointer" onClick={() => onSelectCategory('all')}>
              <div className="h-8 w-8 sm:h-10 sm:w-10 rounded-xl bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-400 flex items-center justify-center text-white shadow-md sm:shadow-lg shadow-orange-500/25 border border-amber-300/40">
                <ShoppingBag className="h-4 w-4 sm:h-5 sm:w-5" />
              </div>
              <div>
                <div className="flex items-center gap-1 sm:gap-1.5">
                  <span className="font-display text-base sm:text-lg font-bold tracking-tight text-stone-900 dark:text-white">VoiceIQ</span>
                  <span className="typo-label px-1 sm:px-1.5 py-0.2 sm:py-0.5 rounded font-bold bg-amber-400/25 text-orange-700 dark:text-amber-300 border border-amber-400/40 normal-case">
                    INDIA
                  </span>
                </div>
                <p className="typo-label normal-case text-stone-500 dark:text-stone-400 tracking-wide -mt-0.5 hidden xs:block sm:block" style={{ fontSize: '9px' }}>
                  Gnani AI Sovereign Store
                </p>
              </div>
            </div>
          </div>

          {/* Search Bar with Category Dropdown (Laptop / Desktop) */}
          <div className="flex-1 max-w-2xl hidden md:flex items-center">
            <div className="flex w-full rounded-xl overflow-hidden border border-amber-200/80 dark:border-stone-800 bg-white dark:bg-[#0c0a09] focus-within:border-orange-500 focus-within:ring-2 focus-within:ring-orange-500/20 transition-all shadow-inner">
              <select
                value={selectedCategory}
                onChange={(e) => onSelectCategory(e.target.value)}
                className="bg-stone-50 dark:bg-[#14100c] text-stone-700 dark:text-stone-200 typo-nav px-3 py-2 border-r border-amber-200/80 dark:border-stone-800 outline-none cursor-pointer hover:bg-stone-100 dark:hover:bg-[#1c1813] transition-colors"
              >
                <option value="all">All Categories</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>

              <div className="relative flex-1 flex items-center">
                <input
                  type="text"
                  placeholder="Search phones, earbuds, mixer grinders, kurtis, watches..."
                  value={searchQuery}
                  onChange={(e) => onSearchChange(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && onSearchSubmit()}
                  className="w-full bg-transparent px-4 py-2 typo-body text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-500 outline-none"
                />
              </div>

              <button
                onClick={onSearchSubmit}
                className="bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 px-4 py-2 text-white transition-all flex items-center justify-center shadow-sm cursor-pointer"
                title="Search Products"
              >
                <Search className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Action Items */}
          <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
            {/* Aesthetic Theme Mode Toggle Button */}
            <button
              onClick={toggleTheme}
              className="relative flex items-center p-0.5 sm:p-1 rounded-full bg-amber-500/10 dark:bg-stone-900 border border-amber-300/40 dark:border-stone-700 backdrop-blur-md transition-all hover:scale-105 active:scale-95 shadow-sm cursor-pointer"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              aria-label="Toggle Light and Dark Mode"
            >
              <div
                className={`flex items-center justify-center w-5 h-5 sm:w-6 sm:h-6 rounded-full transition-all duration-300 ${
                  theme === 'light'
                    ? 'bg-gradient-to-tr from-amber-400 to-orange-500 text-white shadow-md shadow-orange-500/30 scale-105'
                    : 'text-stone-400 opacity-60'
                }`}
              >
                <Sun className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
              </div>
              <div
                className={`flex items-center justify-center w-5 h-5 sm:w-6 sm:h-6 rounded-full transition-all duration-300 ${
                  theme === 'dark'
                    ? 'bg-gradient-to-tr from-amber-400 to-yellow-300 text-stone-950 shadow-md shadow-yellow-400/30 scale-105'
                    : 'text-stone-400 opacity-60'
                }`}
              >
                <Moon className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
              </div>
            </button>

            {/* Language Selector (Desktop / Laptop) */}
            <div className="relative hidden md:block">
              <select
                value={selectedLanguage}
                onChange={(e) => onSelectLanguage(e.target.value)}
                className="bg-white dark:bg-[#14100c] text-stone-700 dark:text-stone-200 typo-nav px-2.5 py-1.5 rounded-lg border border-amber-200/80 dark:border-stone-800 outline-none cursor-pointer hover:border-orange-500/50 transition-colors font-medium"
                title="Select Voice & Interface Language"
              >
                {supportedLanguages.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.native} ({l.code.split('-')[0].toUpperCase()})
                  </option>
                ))}
              </select>
            </div>


            {/* User Account / Sign In */}
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-white dark:bg-[#14100c] text-stone-800 dark:text-stone-200 border border-amber-200/80 dark:border-stone-800 hover:border-orange-500/50 transition-all shadow-sm cursor-pointer"
                  title="My Account"
                >
                  <div className="relative h-6 w-6 rounded-full bg-gradient-to-tr from-orange-500 to-amber-400 text-white font-bold text-[11px] flex items-center justify-center shrink-0">
                    {user.name.slice(0, 2).toUpperCase()}
                    <span className="absolute -bottom-0.5 -right-0.5 flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                    </span>
                  </div>
                  <span className="typo-nav font-bold hidden lg:inline max-w-[80px] truncate">{user.name.split(' ')[0]}</span>
                  <ChevronDown className="h-3 w-3 text-stone-400" />
                </button>

                {isUserMenuOpen && (
                  <div className="absolute right-0 top-full mt-1.5 w-48 py-1.5 bg-white dark:bg-[#120e0b] border border-amber-200/80 dark:border-stone-800 rounded-xl shadow-xl z-50 animate-in fade-in slide-in-from-top-1 duration-150">
                    <div className="px-3 py-2 border-b border-amber-100 dark:border-stone-800">
                      <p className="text-xs font-bold text-stone-900 dark:text-white truncate">{user.name}</p>
                      <p className="text-[10px] text-stone-500 dark:text-stone-400 truncate">{user.email}</p>
                    </div>
                    <button
                      onClick={() => {
                        setIsUserMenuOpen(false);
                        onOpenOrders();
                      }}
                      className="w-full px-3 py-2 text-left text-xs text-stone-700 dark:text-stone-300 hover:bg-amber-50 dark:hover:bg-stone-800/80 flex items-center gap-2 cursor-pointer transition-colors"
                    >
                      <Package className="h-3.5 w-3.5 text-amber-500" />
                      <span>My Orders & Returns</span>
                    </button>
                    <button
                      onClick={() => {
                        setIsUserMenuOpen(false);
                        logout();
                      }}
                      className="w-full px-3 py-2 text-left text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 flex items-center gap-2 cursor-pointer transition-colors"
                    >
                      <LogOut className="h-3.5 w-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => openAuthModal('login')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-orange-700 dark:text-amber-400 border border-amber-300/60 dark:border-amber-900/40 transition-all shadow-sm cursor-pointer"
                title="Sign In / Register"
              >
                <LogIn className="h-3.5 w-3.5" />
                <span className="typo-nav font-bold hidden sm:inline">Sign In</span>
              </button>
            )}

            {/* Orders shortcut (visible on desktop/tablet) */}
            <button
              onClick={onOpenOrders}
              className="typo-nav text-stone-700 dark:text-stone-300 hover:text-orange-600 dark:hover:text-white px-2 py-1 rounded-lg hover:bg-stone-100 dark:hover:bg-[#14100c] transition-colors hidden sm:flex flex-col text-left cursor-pointer"
            >
              <span className="typo-label normal-case text-stone-500 dark:text-stone-400 leading-tight" style={{ fontSize: '10px' }}>Returns</span>
              <span className="font-semibold leading-tight">&amp; Orders</span>
            </button>

            {/* Shopping Cart Button */}
            <button
              onClick={onOpenCart}
              className="relative flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1.5 rounded-xl bg-white dark:bg-[#14100c] text-stone-800 dark:text-stone-200 border border-amber-200/80 dark:border-stone-800 hover:border-orange-500/50 transition-all shadow-sm cursor-pointer"
              title="Shopping Cart"
            >
              <ShoppingCart className="h-4 w-4 text-orange-500" />
              <span className="typo-nav font-bold hidden md:inline">Cart</span>
              {cartItemCount > 0 && (
                <span className="h-4 sm:h-5 min-w-[16px] sm:min-w-[20px] px-1 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 text-white typo-label normal-case font-bold flex items-center justify-center animate-pulse shadow-sm shadow-orange-500/40" style={{ fontSize: '10px' }}>
                  {cartItemCount}
                </span>
              )}
            </button>

            {/* Voice Assistant Launcher */}
            <button
              onClick={onOpenVoiceAssistant}
              className="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-400 hover:from-orange-600 hover:to-amber-500 text-white dark:text-stone-950 typo-button font-bold shadow-md shadow-orange-500/25 border border-amber-300/30 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
              title="Open VoiceIQ Assistant"
            >
              <Mic className="h-3.5 w-3.5 animate-bounce shrink-0" />
              <span className="hidden sm:inline">Voice Support</span>
              <span className="sm:hidden">Voice</span>
            </button>
          </div>
        </div>

        {/* Mobile Search Input (Phone only) with Quick Tap-to-Speak Mic */}
        <div className="mt-2 md:hidden">
          <div className="flex w-full items-center rounded-xl overflow-hidden border border-amber-200/80 dark:border-stone-800 bg-white dark:bg-[#0c0a09] shadow-inner">
            <input
              type="text"
              placeholder="Search products with voice or text..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onSearchSubmit()}
              className="flex-1 bg-transparent px-3 py-2 typo-nav text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-500 outline-none"
            />
            {/* Quick Voice Mic inside mobile search bar */}
            <button
              onClick={onOpenVoiceAssistant}
              className="p-2 text-orange-600 dark:text-amber-400 hover:text-orange-500 transition-colors"
              title="Speak query"
            >
              <Mic className="h-4 w-4 animate-pulse" />
            </button>
            <button
              onClick={onSearchSubmit}
              className="bg-gradient-to-r from-orange-500 to-amber-500 px-3.5 py-2.5 text-white flex items-center justify-center cursor-pointer"
              title="Search"
            >
              <Search className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </header>

    {/* Mobile Slide-Out Navigation Drawer */}
    {isMobileMenuOpen && (
      <div id="mobile-menu-drawer" className="fixed inset-0 z-[100] md:hidden">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-stone-950/70 backdrop-blur-sm transition-opacity"
          onClick={() => setIsMobileMenuOpen(false)}
        />

        {/* Drawer Panel */}
        <div className="fixed inset-y-0 left-0 w-[84%] max-w-xs h-full bg-white dark:bg-[#0c0a09] border-r border-amber-200/80 dark:border-stone-800 shadow-2xl flex flex-col z-10 overflow-hidden animate-in slide-in-from-left duration-200">
            {/* Drawer Header */}
            <div className="p-4 bg-amber-50/70 dark:bg-[#14100c] border-b border-amber-200/70 dark:border-stone-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-400 flex items-center justify-center text-white shadow-md shadow-orange-500/25">
                  <ShoppingBag className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center gap-1">
                    <span className="font-display text-base font-bold text-stone-900 dark:text-white">VoiceIQ</span>
                    <span className="typo-label px-1 py-0.2 rounded font-bold bg-amber-400/25 text-orange-700 dark:text-amber-300 border border-amber-400/40 normal-case" style={{ fontSize: '10px' }}>
                      INDIA
                    </span>
                  </div>
                  <p className="typo-label normal-case text-stone-500 dark:text-stone-400" style={{ fontSize: '9px' }}>Menu & Navigation</p>
                </div>
              </div>

              <button
                id="close-mobile-menu"
                onClick={() => setIsMobileMenuOpen(false)}
                className="p-1.5 rounded-xl text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white hover:bg-amber-100/60 dark:hover:bg-[#1c140c] transition-colors cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* User Greeting Card */}
            {user ? (
              <div className="p-3.5 bg-gradient-to-r from-orange-500/10 via-amber-500/10 to-transparent border-b border-amber-200/50 dark:border-stone-800/80 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-orange-500 to-amber-400 text-white font-bold flex items-center justify-center typo-nav shrink-0 shadow-sm text-xs">
                    {user.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="typo-nav font-bold text-stone-900 dark:text-white truncate">
                      Namaste, {user.name}
                    </p>
                    <p className="typo-label normal-case text-stone-500 dark:text-stone-400 flex items-center gap-1 truncate" style={{ fontSize: '10px' }}>
                      <MapPin className="h-3 w-3 text-orange-500 shrink-0" />
                      <span>{user.city || 'India'} {user.postal_code || ''}</span>
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    logout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="p-1.5 rounded-lg text-stone-400 hover:text-red-500 transition-colors cursor-pointer"
                  title="Sign Out"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div className="p-3 bg-amber-50/50 dark:bg-[#14100c] border-b border-amber-200/50 dark:border-stone-800/80">
                <button
                  onClick={() => {
                    setIsMobileMenuOpen(false);
                    openAuthModal('login');
                  }}
                  className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold text-xs shadow-md shadow-orange-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
                >
                  <LogIn className="h-4 w-4" />
                  <span>Sign In / Create Account</span>
                </button>
              </div>
            )}

            {/* Drawer Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Main Navigation Section */}
              <div className="space-y-1">
                <p className="typo-label text-stone-400 dark:text-stone-500 px-2 pb-1">
                  Menu Navigation
                </p>

                {/* Storefront Catalog */}
                <button
                  onClick={() => {
                    onSelectCategory('all');
                    setIsMobileMenuOpen(false);
                  }}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl typo-nav font-semibold text-stone-700 dark:text-stone-300 hover:bg-amber-50 dark:hover:bg-[#14100c] transition-all cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <ShoppingBag className="h-4 w-4 text-orange-500" />
                    <span>Storefront Catalog</span>
                  </div>
                  <ChevronRight className="h-3.5 w-3.5 text-stone-400" />
                </button>

                {/* My Orders & Tracking */}
                <button
                  onClick={() => {
                    onOpenOrders();
                    setIsMobileMenuOpen(false);
                  }}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl typo-nav font-semibold text-stone-700 dark:text-stone-300 hover:bg-amber-50 dark:hover:bg-[#14100c] transition-all cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <Package className="h-4 w-4 text-amber-500" />
                    <span>My Orders &amp; Live Tracking</span>
                  </div>
                  <ChevronRight className="h-3.5 w-3.5 text-stone-400" />
                </button>

                {/* Voice Assistant */}
                <button
                  onClick={() => {
                    onOpenVoiceAssistant();
                    setIsMobileMenuOpen(false);
                  }}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl typo-nav font-semibold bg-gradient-to-r from-orange-500/10 to-amber-500/10 text-orange-700 dark:text-amber-400 border border-orange-500/30 transition-all cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <Mic className="h-4 w-4 text-orange-500 animate-pulse" />
                    <span>Voice Customer Assistant</span>
                  </div>
                  <span className="typo-label normal-case font-bold px-1.5 py-0.5 rounded-full bg-orange-500 text-white" style={{ fontSize: '10px' }}>AI</span>
                </button>


                {/* Cart */}
                <button
                  onClick={() => {
                    onOpenCart();
                    setIsMobileMenuOpen(false);
                  }}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl typo-nav font-semibold text-stone-700 dark:text-stone-300 hover:bg-amber-50 dark:hover:bg-[#14100c] transition-all cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <ShoppingCart className="h-4 w-4 text-orange-500" />
                    <span>Cart &amp; Checkout</span>
                  </div>
                  {cartItemCount > 0 && (
                    <span className="h-4 min-w-[16px] px-1.5 rounded-full bg-orange-500 text-white typo-label normal-case font-bold flex items-center justify-center" style={{ fontSize: '10px' }}>
                      {cartItemCount}
                    </span>
                  )}
                </button>
              </div>

              {/* Categories Section */}
              <div className="space-y-1.5 pt-2 border-t border-amber-200/60 dark:border-stone-800">
                <p className="typo-label text-stone-400 dark:text-stone-500 px-2 pb-1">
                  Shop by Category
                </p>
                <div className="flex flex-wrap gap-1.5 px-1">
                  <button
                    onClick={() => {
                      onSelectCategory('all');
                      setIsMobileMenuOpen(false);
                    }}
                    className={`px-3 py-1.5 rounded-lg typo-nav font-medium transition-all cursor-pointer ${
                      selectedCategory === 'all'
                        ? 'bg-orange-500 text-white font-bold shadow-sm shadow-orange-500/30'
                        : 'bg-stone-100 dark:bg-[#14100c] text-stone-700 dark:text-stone-300 hover:bg-amber-50 dark:hover:bg-[#1c140c]'
                    }`}
                  >
                    All
                  </button>
                  {categories.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => {
                        onSelectCategory(c.id);
                        setIsMobileMenuOpen(false);
                      }}
                      className={`px-3 py-1.5 rounded-lg typo-nav font-medium transition-all cursor-pointer ${
                        selectedCategory === c.id
                          ? 'bg-orange-500 text-white font-bold shadow-sm shadow-orange-500/30'
                          : 'bg-stone-100 dark:bg-[#14100c] text-stone-700 dark:text-stone-300 hover:bg-amber-50 dark:hover:bg-[#1c140c]'
                      }`}
                    >
                      {c.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Indian Languages Selection */}
              <div className="space-y-2 pt-2 border-t border-amber-200/60 dark:border-stone-800">
                <div className="flex items-center justify-between px-2">
                  <p className="typo-label text-stone-400 dark:text-stone-500 flex items-center gap-1.5">
                    <Languages className="h-3.5 w-3.5 text-orange-500" />
                    <span>Voice Language</span>
                  </p>
                  <span className="typo-label font-bold text-orange-600 dark:text-amber-400 normal-case" style={{ fontFamily: 'var(--font-mono)' }}>
                    {selectedLanguage.split('-')[0]}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-1.5">
                  {supportedLanguages.map((l) => {
                    const isSelected = selectedLanguage === l.code;
                    return (
                      <button
                        key={l.code}
                        onClick={() => {
                          onSelectLanguage(l.code);
                          setIsMobileMenuOpen(false);
                        }}
                        className={`p-2 rounded-xl text-left border typo-nav transition-all flex items-center justify-between cursor-pointer ${
                          isSelected
                            ? 'bg-orange-500/15 border-orange-500 text-stone-900 dark:text-white font-bold shadow-sm shadow-orange-500/20'
                            : 'bg-stone-50 dark:bg-[#14100c] border-amber-200/70 dark:border-stone-800 text-stone-700 dark:text-stone-300 hover:border-orange-400'
                        }`}
                      >
                        <span className="truncate">{l.native}</span>
                        {isSelected && <Check className="h-3.5 w-3.5 text-orange-500 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Theme Mode Selection */}
              <div className="space-y-2 pt-2 border-t border-amber-200/60 dark:border-stone-800">
                <p className="typo-label text-stone-400 dark:text-stone-500 px-2">
                  Appearance
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => {
                      if (theme !== 'light') toggleTheme();
                    }}
                    className={`p-2.5 rounded-xl border flex items-center justify-center gap-2 typo-nav font-bold transition-all cursor-pointer ${
                      theme === 'light'
                        ? 'bg-amber-100/80 border-amber-400 text-orange-800 shadow-sm shadow-orange-500/20'
                        : 'bg-stone-50 dark:bg-[#14100c] border-amber-200/70 dark:border-stone-800 text-stone-600 dark:text-stone-400'
                    }`}
                  >
                    <Sun className="h-4 w-4 text-orange-500" />
                    <span>Light Mode</span>
                  </button>

                  <button
                    onClick={() => {
                      if (theme !== 'dark') toggleTheme();
                    }}
                    className={`p-2.5 rounded-xl border flex items-center justify-center gap-2 typo-nav font-bold transition-all cursor-pointer ${
                      theme === 'dark'
                        ? 'bg-[#1c1813] border-amber-500/40 text-amber-300 shadow-sm shadow-amber-500/20'
                        : 'bg-stone-50 dark:bg-[#14100c] border-amber-200/70 dark:border-stone-800 text-stone-600 dark:text-stone-400'
                    }`}
                  >
                    <Moon className="h-4 w-4 text-yellow-400" />
                    <span>Dark Mode</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Drawer Footer */}
            <div className="p-3 bg-amber-50/70 dark:bg-[#14100c] border-t border-amber-200/70 dark:border-stone-800 text-center text-stone-500 dark:text-stone-400 space-y-0.5">
              <p className="typo-nav font-semibold text-stone-800 dark:text-stone-300">
                VoiceIQ India • Sovereign AI Platform
              </p>
              <p className="typo-label normal-case" style={{ fontSize: '9px' }}>Gnani.ai Prisma STT &amp; Timbre TTS</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
