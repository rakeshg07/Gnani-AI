import React from 'react';
import { X, Trash2, ShoppingBag, ArrowRight, Sparkles, Plus, Minus } from 'lucide-react';
import { Cart } from '@/types';

interface CartDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  cart: Cart | null;
  onUpdateQuantity: (itemId: string, newQty: number) => void;
  onRemoveItem: (itemId: string) => void;
  onProceedToCheckout: () => void;
}

export const CartDrawer: React.FC<CartDrawerProps> = ({
  isOpen,
  onClose,
  cart,
  onUpdateQuantity,
  onRemoveItem,
  onProceedToCheckout,
}) => {
  if (!isOpen) return null;

  const items = cart?.items || [];
  const subtotal = cart?.subtotal || 0;
  const freeDeliveryThreshold = 999;
  const neededForFreeDelivery = Math.max(0, freeDeliveryThreshold - subtotal);
  const freeDeliveryProgress = Math.min(100, Math.round((subtotal / freeDeliveryThreshold) * 100));

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-stone-900/60 dark:bg-black/80 backdrop-blur-md">
      <div className="absolute inset-y-0 right-0 max-w-full flex sm:pl-10 w-full sm:w-auto">
        <div className="w-full sm:w-screen sm:max-w-md bg-white dark:bg-[#0c0a09] border-l border-amber-200/80 dark:border-stone-800 shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-4 sm:p-5 border-b border-amber-200/70 dark:border-stone-800 bg-amber-50/70 dark:bg-[#14100c] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingBag className="h-5 w-5 text-orange-500" />
              <h2 className="font-display text-stone-900 dark:text-white" style={{ fontSize: 'clamp(1rem, 1.5vw + 0.5rem, 1.25rem)', fontWeight: 600 }}>Your Shopping Cart</h2>
              <span className="px-2 py-0.5 rounded-full typo-label normal-case font-bold bg-amber-500/20 text-amber-800 dark:text-amber-300 border border-amber-500/30">
                {cart?.item_count || 0}
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white hover:bg-amber-100/60 dark:hover:bg-[#1c140c] transition-colors cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Free Delivery Progress */}
          <div className="bg-amber-50/40 dark:bg-[#080706] px-5 py-3 border-b border-amber-200/60 dark:border-stone-800 space-y-1.5">
            <div className="flex items-center justify-between typo-nav">
              {neededForFreeDelivery > 0 ? (
                <span className="text-stone-600 dark:text-stone-300">
                  Add <strong className="text-orange-600 dark:text-amber-400">₹{neededForFreeDelivery.toFixed(0)}</strong> more for <strong>FREE Delivery</strong>
                </span>
              ) : (
                <span className="text-orange-600 dark:text-amber-400 font-bold flex items-center gap-1">
                  <Sparkles className="h-3.5 w-3.5 text-amber-500" /> FREE Express Delivery unlocked!
                </span>
              )}
              <span className="text-stone-500 font-mono typo-label normal-case">{freeDeliveryProgress}%</span>
            </div>
            <div className="h-1.5 w-full bg-stone-200 dark:bg-[#1e1710] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-orange-500 via-amber-400 to-yellow-400 transition-all duration-500 rounded-full"
                style={{ width: `${freeDeliveryProgress}%` }}
              />
            </div>
          </div>

          {/* Items List */}
          <div className="flex-1 p-5 overflow-y-auto space-y-4">
            {items.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="h-16 w-16 rounded-full bg-amber-50 dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 flex items-center justify-center text-orange-500 shadow-lg shadow-orange-950/10">
                  <ShoppingBag className="h-8 w-8" />
                </div>
                <div>
                  <h3 className="font-display text-stone-900 dark:text-white" style={{ fontSize: '1rem', fontWeight: 600 }}>Your cart is empty</h3>
                  <p className="typo-body text-stone-500 dark:text-stone-400 mt-1">
                    Explore our top-selling electronics, home appliances, and fashion collections.
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white typo-button font-bold transition-all shadow-md shadow-orange-500/20 cursor-pointer"
                >
                  Start Shopping
                </button>
              </div>
            ) : (
              items.map((item) => (
                <div
                  key={item.id}
                  className="p-3.5 rounded-2xl bg-stone-50 dark:bg-[#14100c] border border-amber-200/70 dark:border-stone-800 flex items-center gap-3.5 hover:border-orange-500/40 transition-all"
                >
                  <img
                    src={item.product.image_url}
                    alt={item.product.title}
                    className="h-16 w-16 rounded-xl object-cover border border-amber-200/60 dark:border-stone-800 shrink-0 bg-white dark:bg-[#070709]"
                  />

                  <div className="flex-1 min-w-0 space-y-1">
                    <h4 className="typo-product-name font-medium text-stone-900 dark:text-white truncate" title={item.product.title}>
                      {item.product.title}
                    </h4>
                    <div className="flex items-center gap-2">
                      <span className="typo-product-price font-bold text-orange-600 dark:text-amber-400">
                        ₹{item.unit_price.toLocaleString('en-IN')}
                      </span>
                      {item.product.original_price > item.unit_price && (
                        <span className="typo-label normal-case text-stone-400 dark:text-stone-500 line-through">
                          ₹{item.product.original_price.toLocaleString('en-IN')}
                        </span>
                      )}
                    </div>

                    {/* Quantity Controls */}
                    <div className="flex items-center justify-between pt-1">
                      <div className="flex items-center border border-amber-200/80 dark:border-stone-800 rounded-lg overflow-hidden bg-white dark:bg-[#0c0a09]">
                        <button
                          onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}
                          className="p-1 text-stone-500 hover:text-orange-600 dark:hover:text-amber-300 hover:bg-amber-50 dark:hover:bg-[#1e1710] cursor-pointer"
                        >
                          <Minus className="h-3 w-3" />
                        </button>
                        <span className="px-2.5 typo-nav font-bold text-stone-800 dark:text-stone-200">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
                          disabled={item.quantity >= item.product.stock}
                          className="p-1 text-stone-500 hover:text-orange-600 dark:hover:text-amber-300 hover:bg-amber-50 dark:hover:bg-[#1e1710] disabled:opacity-40 cursor-pointer"
                        >
                          <Plus className="h-3 w-3" />
                        </button>
                      </div>

                      <button
                        onClick={() => onRemoveItem(item.id)}
                        className="text-stone-400 hover:text-orange-600 dark:hover:text-orange-400 p-1 transition-colors cursor-pointer"
                        title="Remove item"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Cart Footer */}
          {items.length > 0 && (
            <div className="p-5 bg-amber-50/60 dark:bg-[#14100c] border-t border-amber-200/70 dark:border-stone-800 space-y-4">
              <div className="space-y-1.5 typo-nav">
                <div className="flex justify-between text-stone-600 dark:text-stone-400">
                  <span>Subtotal</span>
                  <span className="font-semibold text-stone-900 dark:text-white">
                    ₹{cart?.subtotal.toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="flex justify-between text-stone-600 dark:text-stone-400">
                  <span>Estimated Delivery Fee</span>
                  <span className={cart?.shipping_fee === 0 ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-stone-900 dark:text-white'}>
                    {cart?.shipping_fee === 0 ? 'FREE' : `₹${cart?.shipping_fee}`}
                  </span>
                </div>
                <div className="flex justify-between text-stone-600 dark:text-stone-400">
                  <span>GST / Tax (5%)</span>
                  <span className="text-stone-900 dark:text-white">₹{cart?.tax_amount.toLocaleString('en-IN')}</span>
                </div>
                <div className="pt-2 border-t border-amber-200/80 dark:border-stone-800 flex justify-between font-bold text-stone-900 dark:text-white" style={{ fontSize: 'var(--text-body)' }}>
                  <span>Total Amount</span>
                  <span className="typo-product-price font-bold text-orange-600 dark:text-amber-400" style={{ fontSize: 'clamp(1rem, 1.2vw + 0.5rem, 1.25rem)' }}>
                    ₹{cart?.total_amount.toLocaleString('en-IN')}
                  </span>
                </div>
              </div>

              <button
                onClick={onProceedToCheckout}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-400 hover:from-orange-600 hover:to-amber-500 text-white dark:text-stone-950 typo-button font-bold flex items-center justify-center gap-2 shadow-lg shadow-orange-500/25 transition-all active:scale-95 cursor-pointer"
              >
                <span>Proceed to Simulated Checkout</span>
                <ArrowRight className="h-4 w-4" />
              </button>

              <p className="typo-label normal-case text-center text-stone-400 dark:text-stone-500">
                🔒 Safe &amp; Secure Simulated Demo Checkout • No actual card charged
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
