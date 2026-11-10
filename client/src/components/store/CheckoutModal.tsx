import React, { useState } from 'react';
import {
  X,
  CheckCircle2,
  MapPin,
  CreditCard,
  Truck,
  ShieldCheck,
  ArrowRight,
  Mic,
  PackageCheck,
} from 'lucide-react';
import { Cart, Order } from '@/types';

interface CheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  cart: Cart | null;
  onConfirmOrder: (address: any, paymentMethod: string) => Promise<Order>;
  onTrackWithVoice: (orderId: string) => void;
  onViewOrders: () => void;
}

export const CheckoutModal: React.FC<CheckoutModalProps> = ({
  isOpen,
  onClose,
  cart,
  onConfirmOrder,
  onTrackWithVoice,
  onViewOrders,
}) => {
  const [name, setName] = useState('Aarav Sharma');
  const [phone, setPhone] = useState('+91 98450 12345');
  const [addressLine, setAddressLine] = useState('Flat 402, Skyline Residency, 12th Main, Indiranagar');
  const [city, setCity] = useState('Bengaluru');
  const [state, setState] = useState('Karnataka');
  const [postalCode, setPostalCode] = useState('560038');
  const [paymentMethod, setPaymentMethod] = useState('UPI (Google Pay / PhonePe)');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [placedOrder, setPlacedOrder] = useState<Order | null>(null);

  if (!isOpen) return null;

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const order = await onConfirmOrder(
        {
          name,
          phone,
          address_line: addressLine,
          city,
          state,
          postal_code: postalCode,
        },
        paymentMethod
      );
      setPlacedOrder(order);
    } catch (err: any) {
      alert(err.message || 'Checkout failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setPlacedOrder(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-stone-900/60 dark:bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-white dark:bg-[#0c0a09] border border-amber-200/80 dark:border-stone-800 rounded-2xl sm:rounded-3xl shadow-2xl shadow-orange-950/20 dark:shadow-black/70 overflow-hidden my-2 sm:my-8">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-amber-200/70 dark:border-stone-800 flex items-center justify-between bg-amber-50/70 dark:bg-[#14100c]">
          <div className="flex items-center gap-2">
            <PackageCheck className="h-5 w-5 text-orange-500" />
            <h2 className="font-display text-stone-900 dark:text-white" style={{ fontSize: 'clamp(1rem, 1.5vw + 0.5rem, 1.25rem)', fontWeight: 600 }}>
              {placedOrder ? 'Order Confirmed!' : 'Simulated Checkout'}
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 sm:p-2 rounded-xl text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white hover:bg-amber-100/60 dark:hover:bg-[#1c140c] transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {placedOrder ? (
          /* Success Screen */
          <div className="p-5 sm:p-8 text-center space-y-4 sm:space-y-6">
            <div className="h-16 w-16 sm:h-20 sm:w-20 rounded-full bg-amber-500/20 text-orange-600 dark:text-amber-400 border border-amber-500/40 flex items-center justify-center mx-auto shadow-lg shadow-orange-500/20">
              <CheckCircle2 className="h-8 w-8 sm:h-10 sm:w-10 animate-bounce" />
            </div>

            <div className="space-y-1.5 sm:space-y-2">
              <h3 className="font-display text-stone-900 dark:text-white" style={{ fontSize: 'clamp(1.125rem, 2vw + 0.25rem, 1.5rem)', fontWeight: 700 }}>
                Thank you for your order, {placedOrder.shipping_address?.name || 'Customer'}!
              </h3>
              <p className="typo-nav text-stone-500 dark:text-stone-400">
                A confirmation has been sent to your registered demo profile.
              </p>
            </div>

            <div className="p-4 sm:p-5 rounded-2xl bg-stone-50 dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 text-left space-y-2.5 sm:space-y-3 max-w-md mx-auto">
              <div className="flex justify-between items-center typo-nav">
                <span className="text-stone-500 dark:text-stone-400">Order ID:</span>
                <span className="font-mono font-bold text-orange-600 dark:text-amber-400" style={{ fontSize: 'var(--text-body)' }}>
                  {placedOrder.id}
                </span>
              </div>
              <div className="flex justify-between items-center typo-nav">
                <span className="text-stone-500 dark:text-stone-400">Logistics Carrier:</span>
                <span className="font-semibold text-stone-900 dark:text-white">{placedOrder.carrier}</span>
              </div>
              <div className="flex justify-between items-center typo-nav">
                <span className="text-stone-500 dark:text-stone-400">Tracking Number:</span>
                <span className="font-mono text-stone-700 dark:text-stone-300">{placedOrder.tracking_number}</span>
              </div>
              <div className="flex justify-between items-center typo-nav">
                <span className="text-stone-500 dark:text-stone-400">Total Paid:</span>
                <span className="font-bold text-orange-600 dark:text-amber-400" style={{ fontSize: 'var(--text-body)' }}>
                  ₹{placedOrder.total_amount.toLocaleString('en-IN')}
                </span>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-col sm:flex-row gap-2.5 sm:gap-3 justify-center pt-2">
              <button
                onClick={() => {
                  handleClose();
                  onTrackWithVoice(placedOrder.id);
                }}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white typo-button font-bold flex items-center justify-center gap-2 shadow-md shadow-orange-500/25 transition-all cursor-pointer"
              >
                <Mic className="h-4 w-4" />
                <span>Track via Voice Assistant</span>
              </button>

              <button
                onClick={() => {
                  handleClose();
                  onViewOrders();
                }}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-white dark:bg-[#14100c] hover:bg-amber-50 dark:hover:bg-[#1c140c] text-stone-800 dark:text-stone-200 border border-amber-200/80 dark:border-stone-800 typo-button font-semibold transition-all cursor-pointer"
              >
                View My Orders
              </button>
            </div>
          </div>
        ) : (
          /* Checkout Form */
          <form onSubmit={handlePlaceOrder} className="p-4 sm:p-6 md:p-8 space-y-4 sm:space-y-6">
            {/* Step 1: Shipping Address */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 typo-label text-orange-600 dark:text-amber-400 font-bold">
                <MapPin className="h-4 w-4 text-orange-500" />
                <span>1. Shipping &amp; Delivery Address (Demo Customer)</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Full Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="bg-stone-50 dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 rounded-xl px-3.5 py-2 typo-nav text-stone-900 dark:text-white placeholder-stone-400 dark:placeholder-stone-500 outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/30"
                />
                <input
                  type="text"
                  placeholder="Phone Number"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  required
                  className="bg-stone-50 dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 rounded-xl px-3.5 py-2 typo-nav text-stone-900 dark:text-white placeholder-stone-400 dark:placeholder-stone-500 outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/30"
                />
                <input
                  type="text"
                  placeholder="Address Line / Flat / Building"
                  value={addressLine}
                  onChange={(e) => setAddressLine(e.target.value)}
                  required
                  className="sm:col-span-2 bg-stone-50 dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 rounded-xl px-3.5 py-2 typo-nav text-stone-900 dark:text-white placeholder-stone-400 dark:placeholder-stone-500 outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/30"
                />
                <input
                  type="text"
                  placeholder="City"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  required
                  className="bg-stone-50 dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 rounded-xl px-3.5 py-2 typo-nav text-stone-900 dark:text-white placeholder-stone-400 dark:placeholder-stone-500 outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/30"
                />
                <input
                  type="text"
                  placeholder="Postal Code (PIN)"
                  value={postalCode}
                  onChange={(e) => setPostalCode(e.target.value)}
                  required
                  className="bg-stone-50 dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 rounded-xl px-3.5 py-2 typo-nav text-stone-900 dark:text-white placeholder-stone-400 dark:placeholder-stone-500 outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/30"
                />
              </div>
            </div>

            {/* Step 2: Simulated Payment Selection */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 typo-label text-orange-600 dark:text-amber-400 font-bold">
                <CreditCard className="h-4 w-4 text-orange-500" />
                <span>2. Simulated Payment Method</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {[
                  'UPI (Google Pay / PhonePe)',
                  'Credit / Debit Card (Simulated)',
                  'Net Banking (HDFC / SBI / ICICI)',
                  'Cash on Delivery (Simulated)',
                ].map((method) => (
                  <label
                    key={method}
                    className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all typo-nav ${
                      paymentMethod === method
                        ? 'bg-orange-500/10 border-orange-500 text-stone-900 dark:text-white font-semibold shadow-sm shadow-orange-500/20'
                        : 'bg-stone-50 dark:bg-[#14100c] border-amber-200/80 dark:border-stone-800 text-stone-700 dark:text-stone-300 hover:border-orange-400'
                    }`}
                  >
                    <input
                      type="radio"
                      name="payment_method"
                      value={method}
                      checked={paymentMethod === method}
                      onChange={() => setPaymentMethod(method)}
                      className="accent-orange-500"
                    />
                    <span>{method}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Step 3: Order Summary */}
            <div className="p-4 rounded-2xl bg-stone-50 dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 space-y-2">
              <div className="flex justify-between typo-nav text-stone-500 dark:text-stone-400">
                <span>Items ({cart?.item_count || 0})</span>
                <span className="text-stone-900 dark:text-white font-medium">₹{cart?.subtotal.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between typo-nav text-stone-500 dark:text-stone-400">
                <span>Delivery</span>
                <span className={cart?.shipping_fee === 0 ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-stone-900 dark:text-white'}>
                  {cart?.shipping_fee === 0 ? 'FREE' : `₹${cart?.shipping_fee}`}
                </span>
              </div>
              <div className="flex justify-between typo-nav text-stone-500 dark:text-stone-400">
                <span>Taxes (5% GST)</span>
                <span className="text-stone-900 dark:text-white">₹{cart?.tax_amount.toLocaleString('en-IN')}</span>
              </div>
              <div className="pt-2 border-t border-amber-200/80 dark:border-stone-800 flex justify-between font-bold text-stone-900 dark:text-white" style={{ fontSize: 'var(--text-body)' }}>
                <span>Order Total</span>
                <span className="typo-product-price font-bold text-orange-600 dark:text-amber-400" style={{ fontSize: 'clamp(1rem, 1.2vw + 0.5rem, 1.25rem)' }}>
                  ₹{cart?.total_amount.toLocaleString('en-IN')}
                </span>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || !cart?.items.length}
              className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-400 hover:from-orange-600 hover:to-amber-500 disabled:opacity-50 text-white dark:text-stone-950 typo-button font-bold flex items-center justify-center gap-2 shadow-lg shadow-orange-500/25 transition-all active:scale-95 cursor-pointer"
            >
              <span>{isSubmitting ? 'Processing Order...' : 'Place Simulated Order'}</span>
              <ArrowRight className="h-4 w-4" />
            </button>

            <p className="typo-label normal-case text-center text-stone-400 dark:text-stone-500">
              This is an independent demo store. No real financial transaction is conducted.
            </p>
          </form>
        )}
      </div>
    </div>
  );
};
