import React from 'react';
import { motion } from 'framer-motion';
import { Star, ShoppingCart, Mic, Eye, Check } from 'lucide-react';
import { Product } from '@/types';

interface ProductCardProps {
  product: Product;
  onSelect: (product: Product) => void;
  onAddToCart: (product: Product) => void;
  onAskVoice: (product: Product) => void;
  isAddingToCart?: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onSelect,
  onAddToCart,
  onAskVoice,
  isAddingToCart = false,
}) => {
  const discountPct = Math.round(
    ((product.original_price - product.price) / product.original_price) * 100
  );

  return (
    <motion.div
      whileHover={{ y: -5 }}
      transition={{ type: 'spring', stiffness: 350, damping: 25 }}
      className="group rounded-2xl bg-white dark:bg-[#16120e] border border-amber-200/70 dark:border-stone-800 hover:border-orange-500/60 dark:hover:border-orange-500/60 transition-colors duration-200 flex flex-col overflow-hidden shadow-xs hover:shadow-xl hover:shadow-orange-500/10 dark:hover:shadow-orange-950/30"
    >
      {/* Product Image Area */}
      <div
        onClick={() => onSelect(product)}
        className="relative aspect-square w-full bg-stone-50 dark:bg-[#0c0a09] overflow-hidden cursor-pointer"
      >
        <img
          src={product.image_url}
          alt={product.title}
          loading="lazy"
          className="h-full w-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
        />

        {/* Badges */}
        <div className="absolute top-2.5 left-2.5 flex flex-col gap-1 z-10">
          {product.badge && (
            <span className="px-2 py-0.5 rounded-md typo-label font-extrabold bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md">
              {product.badge}
            </span>
          )}
          {discountPct > 0 && (
            <span className="px-2 py-0.5 rounded-md typo-label font-black bg-amber-400 dark:bg-yellow-400 text-stone-950 shadow-md">
              {discountPct}% OFF
            </span>
          )}
        </div>

        {/* Quick View Overlay Button */}
        <div className="absolute inset-0 bg-stone-900/40 dark:bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelect(product);
            }}
            className="p-2.5 rounded-xl bg-white/95 dark:bg-[#16120e]/95 hover:bg-white dark:hover:bg-[#1f1914] text-stone-900 dark:text-white shadow-md typo-nav font-semibold flex items-center gap-1.5 backdrop-blur-sm border border-amber-200 dark:border-stone-700 transition-colors"
          >
            <Eye className="h-4 w-4 text-orange-500" />
            <span>Quick Specs</span>
          </button>
        </div>
      </div>

      {/* Product Content Details */}
      <div className="p-3 sm:p-4 flex-1 flex flex-col justify-between space-y-2.5 sm:space-y-3">
        <div className="space-y-1 sm:space-y-1.5">
          {/* Star Ratings & Reviews */}
          <div className="flex items-center gap-1 sm:gap-1.5">
            <div className="flex items-center gap-0.5 sm:gap-1 px-1 sm:px-1.5 py-0.2 sm:py-0.5 rounded bg-amber-500/15 border border-amber-400/40 text-amber-800 dark:text-yellow-300 font-bold typo-label">
              <span>{product.rating}</span>
              <Star className="h-2.5 w-2.5 sm:h-3 sm:w-3 fill-amber-400 text-amber-400 dark:fill-yellow-400 dark:text-yellow-400" />
            </div>
            <span className="typo-label text-stone-500 dark:text-stone-400 truncate normal-case">
              ({product.reviews_count.toLocaleString('en-IN')})
            </span>
          </div>

          {/* Title */}
          <h3
            onClick={() => onSelect(product)}
            className="typo-product-name font-medium text-stone-900 dark:text-white line-clamp-2 hover:text-orange-600 dark:hover:text-orange-400 cursor-pointer transition-colors leading-snug"
            title={product.title}
          >
            {product.title}
          </h3>

          {/* Price & Savings */}
          <div className="pt-0.5 sm:pt-1 flex flex-wrap items-baseline gap-1.5 sm:gap-2">
            <span className="typo-product-price font-bold text-stone-900 dark:text-white">
              ₹{product.price.toLocaleString('en-IN')}
            </span>
            {product.original_price > product.price && (
              <span className="typo-label text-stone-400 dark:text-stone-500 line-through normal-case">
                ₹{product.original_price.toLocaleString('en-IN')}
              </span>
            )}
          </div>

          {/* Stock / Delivery Guarantee */}
          <p className="typo-label normal-case text-stone-500 dark:text-stone-400">
            {product.stock > 0 ? (
              <span className="text-orange-600 dark:text-amber-400 font-medium">In Stock • Fast Delivery</span>
            ) : (
              <span className="text-rose-500 font-medium">Out of Stock</span>
            )}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 grid grid-cols-2 gap-1.5 sm:gap-2 border-t border-amber-200/60 dark:border-stone-800">
          <button
            onClick={() => onAddToCart(product)}
            disabled={product.stock <= 0 || isAddingToCart}
            className="w-full py-1.5 sm:py-2 px-2 sm:px-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 disabled:bg-stone-200 dark:disabled:bg-stone-800 disabled:text-stone-400 text-white typo-button font-bold flex items-center justify-center gap-1 sm:gap-1.5 transition-all shadow-md shadow-orange-500/20 active:scale-95 cursor-pointer"
          >
            <ShoppingCart className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
            <span>Add</span>
          </button>

          <button
            onClick={() => onAskVoice(product)}
            className="w-full py-1.5 sm:py-2 px-2 sm:px-2.5 rounded-xl bg-stone-50 dark:bg-[#1e1914] hover:bg-amber-50 dark:hover:bg-[#28211a] text-stone-700 dark:text-amber-300 border border-amber-200/80 dark:border-stone-700 hover:border-orange-400 typo-button font-semibold flex items-center justify-center gap-1 sm:gap-1.5 transition-all active:scale-95 cursor-pointer"
            title="Ask VoiceIQ about this product"
          >
            <Mic className="h-3 w-3 sm:h-3.5 sm:w-3.5 text-orange-500 dark:text-amber-400" />
            <span>Ask AI</span>
          </button>
        </div>
      </div>
    </motion.div>
  );
};
