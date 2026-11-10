import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchCategories,
  fetchProducts,
  fetchCart,
  addToCart,
  updateCartItem,
  removeCartItem,
  simulateCheckout,
  fetchOrders,
  cancelOrder,
  requestOrderReturn,
  fetchAdminAnalytics,
  SUPPORTED_LANGUAGES,
} from '@/lib/api';
import { Product, Order, Category } from '@/types';

import { StoreHeader } from '@/components/store/StoreHeader';
import { HeroBanner } from '@/components/store/HeroBanner';
import { ProductCard } from '@/components/store/ProductCard';
import { ProductDetailModal } from '@/components/store/ProductDetailModal';
import { CartDrawer } from '@/components/store/CartDrawer';
import { CheckoutModal } from '@/components/store/CheckoutModal';
import { OrdersView } from '@/components/store/OrdersView';
import { VoiceAssistantModal } from '@/components/voice/VoiceAssistantModal';
import { AuthModal } from '@/components/auth/AuthModal';
import { Mic, ArrowUpDown, Filter, Sparkles, RefreshCw, Quote } from 'lucide-react';

export default function Home() {
  const queryClient = useQueryClient();

  // Navigation & View States
  const [isOrdersViewOpen, setIsOrdersViewOpen] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [isVoiceAssistantOpen, setIsVoiceAssistantOpen] = useState(false);

  // Filter & Search States
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [submittedSearch, setSubmittedSearch] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('featured');
  const [selectedLanguage, setSelectedLanguage] = useState<string>(() => {
    try {
      return localStorage.getItem('voiceiq_preferred_language') || 'en-IN';
    } catch {
      return 'en-IN';
    }
  });

  const handleSelectLanguage = (lang: string) => {
    setSelectedLanguage(lang);
    try {
      localStorage.setItem('voiceiq_preferred_language', lang);
    } catch {}
  };

  // Context & Modals
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [activeVoiceOrderId, setActiveVoiceOrderId] = useState<string | undefined>(undefined);
  const [activeVoiceProductId, setActiveVoiceProductId] = useState<string | undefined>(undefined);

  // Queries
  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: fetchCategories,
  });

  const { data: productsData, isLoading: isLoadingProducts } = useQuery({
    queryKey: ['products', selectedCategory, submittedSearch, sortBy],
    queryFn: () =>
      fetchProducts({
        categoryId: selectedCategory,
        search: submittedSearch,
        sortBy,
      }),
  });

  const { data: cart = null, refetch: refetchCart } = useQuery({
    queryKey: ['cart'],
    queryFn: () => fetchCart('cust_demo_001'),
  });

  const { data: ordersData, refetch: refetchOrders } = useQuery({
    queryKey: ['orders'],
    queryFn: () => fetchOrders('cust_demo_001'),
  });


  // Handlers
  const handleAddToCart = async (product: Product, quantity: number = 1) => {
    try {
      await addToCart(product.id, quantity, 'cust_demo_001');
      await refetchCart();
      setIsCartOpen(true);
    } catch (err: any) {
      alert(err.message || 'Failed to add item to cart');
    }
  };

  const handleBuyNow = async (product: Product, quantity: number = 1) => {
    try {
      await addToCart(product.id, quantity, 'cust_demo_001');
      await refetchCart();
      setSelectedProduct(null);
      setIsCheckoutOpen(true);
    } catch (err: any) {
      alert(err.message || 'Failed to initiate purchase');
    }
  };

  const handleUpdateCartQuantity = async (itemId: string, newQty: number) => {
    try {
      await updateCartItem(itemId, newQty, 'cust_demo_001');
      await refetchCart();
    } catch (err: any) {
      alert(err.message || 'Failed to update quantity');
    }
  };

  const handleRemoveCartItem = async (itemId: string) => {
    try {
      await removeCartItem(itemId, 'cust_demo_001');
      await refetchCart();
    } catch (err: any) {
      alert(err.message || 'Failed to remove item');
    }
  };

  const handleConfirmOrder = async (address: any, paymentMethod: string): Promise<Order> => {
    const order = await simulateCheckout({
      customerId: 'cust_demo_001',
      shippingAddress: address,
      paymentMethod,
    });
    await refetchCart();
    await refetchOrders();
    return order;
  };

  const handleCancelOrder = async (orderId: string, reason: string) => {
    await cancelOrder(orderId, reason, 'cust_demo_001');
    await refetchOrders();
  };

  const handleRequestReturn = async (orderId: string, reason: string) => {
    await requestOrderReturn(orderId, reason, 'cust_demo_001');
    await refetchOrders();
  };

  const handleAskVoiceAboutProduct = (product: Product) => {
    setActiveVoiceProductId(product.id);
    setActiveVoiceOrderId(undefined);
    setIsVoiceAssistantOpen(true);
  };

  const handleTrackWithVoice = (orderId: string) => {
    setActiveVoiceOrderId(orderId);
    setActiveVoiceProductId(undefined);
    setIsVoiceAssistantOpen(true);
  };

  const currentPageContext = isOrdersViewOpen
    ? 'orders'
    : selectedProduct
      ? 'product_detail'
      : isCheckoutOpen
        ? 'checkout'
        : isCartOpen
          ? 'cart'
          : 'home';

  const products = productsData?.items || [];

  return (
    <div className="min-h-screen bg-[#faf8f5] dark:bg-[#0c0a09] text-stone-900 dark:text-stone-100 flex flex-col font-sans selection:bg-orange-500/25 selection:text-orange-950 dark:selection:text-orange-200 transition-colors duration-200">
      {/* Global Store Header */}
      <StoreHeader
        categories={categories}
        selectedCategory={selectedCategory}
        onSelectCategory={(cat) => {
          setSelectedCategory(cat);
          setIsOrdersViewOpen(false);
        }}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSearchSubmit={() => {
          setSubmittedSearch(searchQuery);
          setIsOrdersViewOpen(false);
        }}
        cart={cart}
        onOpenCart={() => setIsCartOpen(true)}
        onOpenOrders={() => {
          setIsOrdersViewOpen(true);
        }}
        onOpenVoiceAssistant={() => {
          setActiveVoiceProductId(undefined);
          setActiveVoiceOrderId(undefined);
          setIsVoiceAssistantOpen(true);
        }}
        selectedLanguage={selectedLanguage}
        onSelectLanguage={handleSelectLanguage}
        supportedLanguages={SUPPORTED_LANGUAGES}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-4 md:p-6 lg:p-8">
        {isOrdersViewOpen ? (
          /* Orders & Live Tracking View */
          <OrdersView
            orders={ordersData?.items || []}
            onCancelOrder={handleCancelOrder}
            onRequestReturn={handleRequestReturn}
            onTrackWithVoice={handleTrackWithVoice}
            onContinueShopping={() => setIsOrdersViewOpen(false)}
          />
        ) : (
          /* Storefront View */
          <div className="space-y-4 sm:space-y-6 md:space-y-8">
            {/* Hero Promo Banner */}
            <HeroBanner
              categories={categories}
              selectedCategory={selectedCategory}
              onSelectCategory={setSelectedCategory}
              onOpenVoiceAssistant={() => {
                setActiveVoiceProductId(undefined);
                setActiveVoiceOrderId(undefined);
                setIsVoiceAssistantOpen(true);
              }}
            />

            {/* Editorial Collection Highlights Callout */}
            <div className="relative rounded-2xl overflow-hidden bg-gradient-to-r from-amber-50 via-orange-50/40 to-amber-50 dark:from-[#17120e] dark:via-[#130f0a] dark:to-[#17120e] border border-amber-200/60 dark:border-amber-900/30 px-6 py-5 sm:px-8 sm:py-6 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4 text-center md:text-left">
              <div className="space-y-1 max-w-2xl">
                <div className="inline-flex items-center gap-1.5 typo-label text-orange-600 dark:text-amber-400 font-semibold">
                  <Sparkles className="h-3 w-3" />
                  <span>Curated Collection Showcase</span>
                </div>
                <p className="font-editorial text-lg sm:text-xl md:text-2xl text-stone-800 dark:text-stone-200 italic leading-snug">
                  "Crafted for the modern Indian home — where timeless heritage meets sovereign Indic Voice AI."
                </p>
              </div>
              <div className="shrink-0 flex items-center gap-2">
                <span className="typo-label text-stone-500 dark:text-stone-400 bg-white dark:bg-[#0c0a09] px-3 py-1.5 rounded-full border border-amber-200/80 dark:border-stone-800 shadow-xs">
                  12 Verified Categories
                </span>
              </div>
            </div>

            {/* Catalog Controls / Filters Bar */}
            <div className="p-3 sm:p-4 rounded-2xl bg-white dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 flex flex-wrap items-center justify-between gap-2 sm:gap-4 shadow-xs">
              <div className="flex items-center gap-1.5 sm:gap-2 typo-nav text-stone-600 dark:text-stone-300">
                <span className="typo-product-price font-bold text-stone-900 dark:text-white tabular-nums">
                  {productsData?.total || products.length}
                </span>{' '}
                <span>Products in Catalog</span>
                {submittedSearch && (
                  <span className="text-orange-600 dark:text-amber-400 font-semibold truncate max-w-[140px] sm:max-w-none">
                    for "{submittedSearch}"
                  </span>
                )}
              </div>

              {/* Sorting */}
              <div className="flex items-center gap-1.5 sm:gap-2">
                <span className="typo-label text-stone-500 dark:text-stone-400 flex items-center gap-1">
                  <ArrowUpDown className="h-3.5 w-3.5 text-orange-500" />
                  <span className="hidden sm:inline">Sort By:</span>
                </span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="typo-nav bg-stone-50 dark:bg-[#0c0a09] text-stone-700 dark:text-stone-200 px-2.5 sm:px-3 py-1.5 rounded-xl border border-amber-200/80 dark:border-stone-800 outline-none cursor-pointer hover:border-orange-500/50 focus:border-orange-500 transition-colors"
                >
                  <option value="featured">Featured Deals</option>
                  <option value="price_asc">Price: Low to High</option>
                  <option value="price_desc">Price: High to Low</option>
                  <option value="rating">Customer Rating</option>
                  <option value="newest">Newest Arrivals</option>
                </select>
              </div>
            </div>

            {/* Products Grid */}
            {isLoadingProducts ? (
              <div className="p-16 text-center text-stone-500 typo-body space-y-3">
                <RefreshCw className="h-8 w-8 mx-auto animate-spin text-orange-500" />
                <p>Loading VoiceIQ Indian catalog...</p>
              </div>
            ) : products.length === 0 ? (
              <div className="p-12 sm:p-16 text-center rounded-2xl border border-amber-200/80 dark:border-stone-800 bg-white dark:bg-[#14100c] text-stone-600 dark:text-stone-400 typo-body space-y-3 shadow-md">
                <p className="font-display text-lg font-bold text-stone-900 dark:text-white">
                  No products matched your search.
                </p>
                <p className="typo-body">Try searching for "earbuds", "mixer grinder", "kurti", "smartwatch", or "backpack".</p>
                <button
                  onClick={() => {
                    setSubmittedSearch('');
                    setSearchQuery('');
                    setSelectedCategory('all');
                  }}
                  className="typo-button px-4 py-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold shadow-md shadow-orange-500/25 transition-all"
                >
                  Reset Filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
                {products.map((product) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    onSelect={setSelectedProduct}
                    onAddToCart={(p) => handleAddToCart(p, 1)}
                    onAskVoice={handleAskVoiceAboutProduct}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Floating Push-to-Talk Mic Trigger */}
      <button
        id="floating-voice-trigger"
        onClick={() => {
          setActiveVoiceProductId(undefined);
          setActiveVoiceOrderId(undefined);
          setIsVoiceAssistantOpen(!isVoiceAssistantOpen);
        }}
        className="fixed bottom-10 right-4 sm:bottom-8 sm:right-8 z-40 h-12 w-12 sm:h-14 sm:w-14 rounded-full bg-gradient-to-tr from-orange-500 via-amber-500 to-yellow-400 hover:from-orange-600 hover:to-amber-500 text-white dark:text-stone-950 shadow-2xl shadow-orange-500/35 flex items-center justify-center transition-all hover:scale-110 active:scale-95 border-2 border-amber-300/40 cursor-pointer"
        title="Open VoiceIQ Multilingual Assistant"
      >
        <span className="absolute -top-1 -right-1 flex h-4 w-4">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-500 opacity-75" />
          <span className="relative inline-flex rounded-full h-4 w-4 bg-gradient-to-r from-orange-600 to-amber-500 text-[9px] font-black items-center justify-center text-white shadow-sm typo-label">
            AI
          </span>
        </span>
        <Mic className="h-5 w-5 sm:h-6 sm:w-6" />
      </button>

      {/* Modals & Drawers */}
      <ProductDetailModal
        product={selectedProduct}
        onClose={() => setSelectedProduct(null)}
        onAddToCart={handleAddToCart}
        onBuyNow={handleBuyNow}
        onAskVoice={handleAskVoiceAboutProduct}
      />

      <CartDrawer
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        cart={cart}
        onUpdateQuantity={handleUpdateCartQuantity}
        onRemoveItem={handleRemoveCartItem}
        onProceedToCheckout={() => {
          setIsCartOpen(false);
          setIsCheckoutOpen(true);
        }}
      />

      <CheckoutModal
        isOpen={isCheckoutOpen}
        onClose={() => setIsCheckoutOpen(false)}
        cart={cart}
        onConfirmOrder={handleConfirmOrder}
        onTrackWithVoice={handleTrackWithVoice}
        onViewOrders={() => {
          setIsOrdersViewOpen(true);
        }}
      />

      <VoiceAssistantModal
        isOpen={isVoiceAssistantOpen}
        onClose={() => setIsVoiceAssistantOpen(false)}
        currentPage={currentPageContext}
        activeProductId={activeVoiceProductId}
        activeOrderId={activeVoiceOrderId}
        onAddToCart={(p) => handleAddToCart(p, 1)}
        onOrderUpdated={refetchOrders}
        selectedLanguage={selectedLanguage}
        onSelectLanguage={handleSelectLanguage}
      />

      <AuthModal />

      {/* Footer */}
      <footer className="mt-12 bg-white dark:bg-[#0c0a09] border-t border-amber-200/60 dark:border-stone-800 py-8 px-4 text-xs text-stone-600 dark:text-stone-400 transition-colors">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <p className="font-display text-base font-bold text-stone-900 dark:text-white">
              VoiceIQ India — Gnani AI Challenge 2026
            </p>
            <p className="typo-body text-xs text-stone-600 dark:text-stone-400">
              Independent demonstration e-commerce store with genuine Gnani.ai Prisma STT &amp; Timbre TTS integration.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
