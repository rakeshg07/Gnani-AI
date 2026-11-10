import React, { useState } from 'react';
import {
  X,
  Star,
  ShoppingCart,
  Mic,
  ShieldCheck,
  Truck,
  RotateCcw,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import { Product } from '@/types';

interface ProductDetailModalProps {
  product: Product | null;
  onClose: () => void;
  onAddToCart: (product: Product, quantity: number) => void;
  onBuyNow: (product: Product, quantity: number) => void;
  onAskVoice: (product: Product) => void;
  isAddingToCart?: boolean;
}

export const ProductDetailModal: React.FC<ProductDetailModalProps> = ({
  product,
  onClose,
  onAddToCart,
  onBuyNow,
  onAskVoice,
  isAddingToCart = false,
}) => {
  const [quantity, setQuantity] = useState<number>(1);

  if (!product) return null;

  const discountPct = Math.round(
    ((product.original_price - product.price) / product.original_price) * 100
  );
  const savings = product.original_price - product.price;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-stone-900/60 dark:bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-white dark:bg-[#0c0a09] border border-amber-200/80 dark:border-stone-800 rounded-2xl sm:rounded-3xl shadow-2xl shadow-orange-950/20 dark:shadow-black/70 overflow-hidden my-2 sm:my-8">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 sm:top-4 sm:right-4 z-20 p-2 rounded-full bg-stone-100 dark:bg-[#14100c] hover:bg-amber-100 dark:hover:bg-[#1c140c] text-stone-600 dark:text-stone-300 hover:text-stone-900 dark:hover:text-white border border-amber-200/80 dark:border-stone-800 transition-colors cursor-pointer"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="grid grid-cols-1 md:grid-cols-2">
          {/* Left: Product Image */}
          <div className="p-4 sm:p-6 md:p-8 bg-amber-50/30 dark:bg-[#070709] flex flex-col items-center justify-center border-b md:border-b-0 md:border-r border-amber-200/70 dark:border-stone-800">
            <div className="relative aspect-square w-full max-w-sm md:max-w-md rounded-2xl overflow-hidden shadow-lg border border-amber-200/80 dark:border-stone-800 bg-white dark:bg-[#0c0a09]">
              <img
                src={product.image_url}
                alt={product.title}
                className="h-full w-full object-cover object-center"
              />
              {product.badge && (
                <span className="absolute top-3 left-3 px-2.5 py-1 rounded-md typo-label font-bold bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md shadow-orange-500/30">
                  {product.badge}
                </span>
              )}
            </div>

            {/* Guarantees */}
            <div className="grid grid-cols-3 gap-2 w-full mt-4 sm:mt-6 text-center">
              <div className="p-2 sm:p-2.5 rounded-xl bg-white dark:bg-[#14100c] border border-amber-200/70 dark:border-stone-800 flex flex-col items-center gap-1 shadow-sm">
                <Truck className="h-4 w-4 text-emerald-500" />
                <span className="typo-label normal-case text-stone-700 dark:text-stone-300">Free Delivery</span>
              </div>
              <div className="p-2 sm:p-2.5 rounded-xl bg-white dark:bg-[#14100c] border border-amber-200/70 dark:border-stone-800 flex flex-col items-center gap-1 shadow-sm">
                <RotateCcw className="h-4 w-4 text-orange-500" />
                <span className="typo-label normal-case text-stone-700 dark:text-stone-300">{product.return_window_days}-Day Returns</span>
              </div>
              <div className="p-2 sm:p-2.5 rounded-xl bg-white dark:bg-[#14100c] border border-amber-200/70 dark:border-stone-800 flex flex-col items-center gap-1 shadow-sm">
                <ShieldCheck className="h-4 w-4 text-amber-500" />
                <span className="typo-label normal-case text-stone-700 dark:text-stone-300">Brand Warranty</span>
              </div>
            </div>
          </div>

          {/* Right: Product Details & Controls */}
          <div className="p-4 sm:p-6 md:p-8 flex flex-col justify-between space-y-4 sm:space-y-6 max-h-[85vh] overflow-y-auto">
            <div className="space-y-4">
              {/* Category & Rating */}
              <div className="flex items-center justify-between">
                <span className="typo-label text-orange-600 dark:text-amber-400 font-bold">
                  {product.category_id}
                </span>
                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-500/15 text-stone-800 dark:text-amber-300 font-bold typo-label border border-amber-500/30">
                  <span className="normal-case">{product.rating}</span>
                  <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                  <span className="text-stone-500 dark:text-stone-400 font-normal normal-case">
                    ({product.reviews_count.toLocaleString('en-IN')})
                  </span>
                </div>
              </div>

              {/* Title — Uses Playfair Display for premium section heading feel */}
              <h2 className="font-display text-stone-900 dark:text-white leading-snug" style={{ fontSize: 'clamp(1.25rem, 2vw + 0.5rem, 1.5rem)', fontWeight: 600, letterSpacing: '-0.01em' }}>
                {product.title}
              </h2>

              {/* Price Breakdown */}
              <div className="p-4 rounded-2xl bg-amber-50/50 dark:bg-[#14100c] border border-amber-200/70 dark:border-stone-800 space-y-1">
                <div className="flex items-baseline gap-3">
                  <span className="font-body text-stone-900 dark:text-white" style={{ fontSize: 'clamp(1.5rem, 2.5vw, 2rem)', fontWeight: 700 }}>
                    ₹{product.price.toLocaleString('en-IN')}
                  </span>
                  {product.original_price > product.price && (
                    <>
                      <span className="typo-body text-stone-400 dark:text-stone-500 line-through">
                        ₹{product.original_price.toLocaleString('en-IN')}
                      </span>
                      <span className="typo-label font-bold px-2 py-0.5 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-sm normal-case">
                        {discountPct}% OFF
                      </span>
                    </>
                  )}
                </div>
                {savings > 0 && (
                  <p className="typo-nav text-emerald-600 dark:text-emerald-400 font-semibold">
                    You save ₹{savings.toLocaleString('en-IN')} on this order
                  </p>
                )}
                <p className="typo-label normal-case text-stone-500 dark:text-stone-400">
                  Inclusive of all taxes • Eligible for simulated cash on delivery
                </p>
              </div>

              {/* Description */}
              <div className="space-y-1.5">
                <h3 className="typo-label text-stone-900 dark:text-stone-200 font-bold">
                  Product Overview
                </h3>
                <p className="typo-body text-stone-600 dark:text-stone-300">
                  {product.description}
                </p>
              </div>

              {/* Specifications Table */}
              {product.specifications && Object.keys(product.specifications).length > 0 && (
                <div className="space-y-2">
                  <h3 className="typo-label text-stone-900 dark:text-stone-200 font-bold">
                    Key Specifications
                  </h3>
                  <div className="rounded-xl border border-amber-200/80 dark:border-stone-800 overflow-hidden divide-y divide-amber-200/60 dark:divide-stone-800 shadow-sm">
                    {Object.entries(product.specifications).map(([key, value]) => (
                      <div key={key} className="grid grid-cols-2 p-2.5 bg-stone-50 dark:bg-[#14100c]">
                        <span className="typo-nav text-stone-500 dark:text-stone-400 font-medium">{key}</span>
                        <span className="typo-nav text-stone-800 dark:text-stone-200 font-semibold">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            <div className="space-y-4 pt-4 border-t border-amber-200/80 dark:border-stone-800">
              {/* Quantity selector */}
              <div className="flex items-center justify-between">
                <span className="typo-nav font-semibold text-stone-700 dark:text-stone-300">Quantity:</span>
                <div className="flex items-center border border-amber-200/80 dark:border-stone-800 rounded-xl overflow-hidden bg-white dark:bg-[#0c0a09]">
                  <button
                    onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                    disabled={quantity <= 1}
                    className="px-3 py-1 text-stone-600 dark:text-stone-300 hover:text-orange-600 dark:hover:text-amber-300 hover:bg-amber-50 dark:hover:bg-[#1c140c] disabled:opacity-40 cursor-pointer"
                  >
                    -
                  </button>
                  <span className="px-4 py-1 typo-nav font-bold text-stone-900 dark:text-white">{quantity}</span>
                  <button
                    onClick={() => setQuantity((q) => Math.min(product.stock, q + 1))}
                    disabled={quantity >= product.stock}
                    className="px-3 py-1 text-stone-600 dark:text-stone-300 hover:text-orange-600 dark:hover:text-amber-300 hover:bg-amber-50 dark:hover:bg-[#1c140c] disabled:opacity-40 cursor-pointer"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={() => onAddToCart(product, quantity)}
                  disabled={product.stock <= 0 || isAddingToCart}
                  className="py-3 px-4 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 disabled:opacity-50 text-white typo-button font-bold flex items-center justify-center gap-2 shadow-md shadow-orange-500/20 transition-all active:scale-95 cursor-pointer"
                >
                  <ShoppingCart className="h-4 w-4" />
                  <span>Add to Cart</span>
                </button>

                <button
                  onClick={() => onBuyNow(product, quantity)}
                  disabled={product.stock <= 0}
                  className="py-3 px-4 rounded-xl bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-400 hover:from-orange-600 hover:to-amber-500 text-white dark:text-stone-950 typo-button font-black flex items-center justify-center gap-2 shadow-md shadow-orange-500/25 transition-all active:scale-95 cursor-pointer"
                >
                  <Zap className="h-4 w-4 fill-white dark:fill-stone-950" />
                  <span>Buy Now (Simulated)</span>
                </button>
              </div>

              {/* Voice Query Shortcut */}
              <button
                onClick={() => {
                  onClose();
                  onAskVoice(product);
                }}
                className="w-full py-2.5 px-4 rounded-xl bg-amber-50/60 dark:bg-[#14100c] hover:bg-amber-100/60 dark:hover:bg-[#1c140c] text-orange-700 dark:text-amber-300 border border-amber-200/80 dark:border-stone-800 typo-nav font-semibold flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer"
              >
                <Mic className="h-4 w-4 text-orange-500 shrink-0" />
                <span className="sm:hidden">Ask VoiceIQ Assistant about this item</span>
                <span className="hidden sm:inline">Ask VoiceIQ Assistant: "What is the warranty and battery life?"</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
