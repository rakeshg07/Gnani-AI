import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Mic, Headphones, ArrowRight, ShieldCheck, Truck, RotateCcw } from 'lucide-react';
import { Category } from '@/types';

interface HeroBannerProps {
  categories: Category[];
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
  onOpenVoiceAssistant: () => void;
}

export const HeroBanner: React.FC<HeroBannerProps> = ({
  categories,
  selectedCategory,
  onSelectCategory,
  onOpenVoiceAssistant,
}) => {
  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Promotional Hero Banner */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: 'easeOut' }}
        className="relative rounded-2xl sm:rounded-3xl overflow-hidden bg-gradient-to-br from-amber-500/10 via-orange-500/5 to-yellow-500/10 dark:from-[#17120e] dark:via-[#0c0a09] dark:to-[#1b140c] border border-amber-300/60 dark:border-amber-500/20 p-4 sm:p-6 md:p-8 shadow-xl transition-colors duration-200"
      >
        {/* Background glow accents */}
        <div className="absolute top-0 right-0 w-72 sm:w-96 h-72 sm:h-96 bg-orange-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-48 sm:w-64 h-48 sm:h-64 bg-yellow-400/15 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-3 sm:space-y-4">
          <div className="inline-flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1 rounded-full bg-amber-500/15 dark:bg-amber-400/10 border border-amber-500/30 text-orange-700 dark:text-amber-300 backdrop-blur-sm">
            <Sparkles className="h-3 w-3 sm:h-3.5 sm:w-3.5 text-amber-500 dark:text-yellow-400 shrink-0" />
            <span className="typo-label">Gnani AI Challenge 2026 Showcase</span>
          </div>

          <h1 className="font-display text-stone-900 dark:text-white tracking-tight leading-tight" style={{ fontSize: 'var(--text-hero)', lineHeight: 'var(--text-hero-lh)', letterSpacing: 'var(--text-hero-ls)', fontWeight: 'var(--text-hero-weight)' }}>
            Shop Smarter with Sovereign <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-orange-600 via-amber-500 to-yellow-500 dark:from-orange-400 dark:via-amber-300 dark:to-yellow-300 bg-clip-text text-transparent">
              Indian-Language Voice AI
            </span>
          </h1>

          <p className="typo-body text-stone-600 dark:text-stone-300 max-w-2xl">
            Experience next-generation e-commerce with built-in voice shopping and customer care.
            Ask about products, track your orders in real time, or request cancellations and returns in
            English, Hindi, Tamil, Telugu, Kannada, and more.
          </p>

          {/* Value Badges */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3 pt-1 sm:pt-2">
            <div className="flex items-center gap-2 typo-nav text-stone-700 dark:text-stone-300 bg-white/90 dark:bg-[#14100c]/80 border border-amber-200/80 dark:border-stone-800 p-2 sm:p-2.5 rounded-xl shadow-xs">
              <Truck className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-orange-500 shrink-0" />
              <span>Fast 2-3 Day Delivery Across India</span>
            </div>
            <div className="flex items-center gap-2 typo-nav text-stone-700 dark:text-stone-300 bg-white/90 dark:bg-[#14100c]/80 border border-amber-200/80 dark:border-stone-800 p-2 sm:p-2.5 rounded-xl shadow-xs">
              <RotateCcw className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-amber-500 shrink-0" />
              <span>7-Day Easy Replacement &amp; Returns</span>
            </div>
            <div className="flex items-center gap-2 typo-nav text-stone-700 dark:text-stone-300 bg-white/90 dark:bg-[#14100c]/80 border border-amber-200/80 dark:border-stone-800 p-2 sm:p-2.5 rounded-xl shadow-xs">
              <ShieldCheck className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-yellow-500 shrink-0" />
              <span>100% Genuine Certified Brands</span>
            </div>
          </div>

          {/* Action Button */}
          <div className="pt-2 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
            <button
              onClick={onOpenVoiceAssistant}
              className="w-full sm:w-auto px-4 sm:px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-400 hover:from-orange-600 hover:to-amber-500 text-white dark:text-stone-950 typo-button font-bold shadow-lg shadow-orange-500/25 flex items-center justify-center gap-2 transition-all hover:scale-105 active:scale-95 cursor-pointer"
            >
              <Mic className="h-4 w-4 shrink-0" />
              <span>Try Multilingual Voice Assistant</span>
              <ArrowRight className="h-3.5 w-3.5 shrink-0" />
            </button>
            <span className="font-editorial text-sm sm:text-base text-stone-500 dark:text-stone-400 italic">
              Try saying: "Show me wireless earbuds under 2000 rupees"
            </span>
          </div>
        </div>
      </motion.div>

      {/* Category Pills Navigation */}
      <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto pb-2 scrollbar-none touch-pan-x">
        <button
          onClick={() => onSelectCategory('all')}
          className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-xl typo-button font-bold transition-all shrink-0 border cursor-pointer ${
            selectedCategory === 'all'
              ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white border-orange-400 shadow-md shadow-orange-500/30'
              : 'bg-white dark:bg-[#14100c] text-stone-700 dark:text-stone-300 border-amber-200/80 dark:border-stone-800 hover:border-orange-400 hover:text-orange-600 dark:hover:text-white'
          }`}
        >
          All Collections
        </button>

        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => onSelectCategory(cat.id)}
            className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-xl typo-button transition-all shrink-0 border flex items-center gap-1.5 sm:gap-2 cursor-pointer ${
              selectedCategory === cat.id
                ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white border-orange-400 shadow-md shadow-orange-500/30 font-bold'
                : 'bg-white dark:bg-[#14100c] text-stone-700 dark:text-stone-300 border-amber-200/80 dark:border-stone-800 hover:border-orange-400 hover:text-orange-600 dark:hover:text-white'
            }`}
          >
            <span>{cat.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
};
