import React, { useState } from 'react';
import {
  Package,
  Truck,
  RotateCcw,
  XCircle,
  CheckCircle2,
  Clock,
  Mic,
  AlertCircle,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { Order, ReturnRequest } from '@/types';

interface OrdersViewProps {
  orders: Order[];
  onCancelOrder: (orderId: string, reason: string) => Promise<void>;
  onRequestReturn: (orderId: string, reason: string) => Promise<void>;
  onTrackWithVoice: (orderId: string) => void;
  onContinueShopping: () => void;
}

export const OrdersView: React.FC<OrdersViewProps> = ({
  orders,
  onCancelOrder,
  onRequestReturn,
  onTrackWithVoice,
  onContinueShopping,
}) => {
  const [activeTab, setActiveTab] = useState<'all' | 'active' | 'delivered' | 'cancelled'>('all');
  const [cancellationOrderId, setCancellationOrderId] = useState<string | null>(null);
  const [cancellationReason, setCancellationReason] = useState<string>('Found lower price elsewhere');
  const [returnOrderId, setReturnOrderId] = useState<string | null>(null);
  const [returnReason, setReturnReason] = useState<string>('Item defective / does not meet expectation');
  const [isProcessing, setIsProcessing] = useState(false);

  const filteredOrders = orders.filter((o) => {
    if (activeTab === 'active') return ['processing', 'shipped', 'out_for_delivery'].includes(o.status);
    if (activeTab === 'delivered') return o.status === 'delivered';
    if (activeTab === 'cancelled') return o.status === 'cancelled';
    return true;
  });

  const handleConfirmCancel = async () => {
    if (!cancellationOrderId) return;
    setIsProcessing(true);
    try {
      await onCancelOrder(cancellationOrderId, cancellationReason);
      setCancellationOrderId(null);
    } catch (err: any) {
      alert(err.message || 'Failed to cancel order');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmReturn = async () => {
    if (!returnOrderId) return;
    setIsProcessing(true);
    try {
      await onRequestReturn(returnOrderId, returnReason);
      setReturnOrderId(null);
    } catch (err: any) {
      alert(err.message || 'Failed to submit return');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="p-4 sm:p-6 rounded-2xl bg-white dark:bg-[#0c0a09] border border-amber-200/80 dark:border-stone-800 shadow-sm flex flex-wrap items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="font-display text-stone-900 dark:text-white" style={{ fontSize: 'var(--text-promo)', fontWeight: 'var(--text-promo-weight)', lineHeight: 'var(--text-promo-lh)', letterSpacing: 'var(--text-promo-ls)' }}>Your Demo Orders &amp; Tracking</h1>
          <p className="typo-nav text-stone-500 dark:text-stone-400 mt-1">
            Real database records with live tracking timelines, cancellation, and return eligibility.
          </p>
        </div>

        <button
          onClick={onContinueShopping}
          className="px-3.5 sm:px-4 py-2 rounded-xl bg-stone-100 dark:bg-[#14100c] hover:bg-amber-50 dark:hover:bg-[#1c140c] text-stone-800 dark:text-stone-200 border border-amber-200/80 dark:border-stone-800 typo-button font-semibold transition-all cursor-pointer"
        >
          Browse Store Catalog
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 sm:gap-2 border-b border-amber-200/70 dark:border-stone-800 pb-2 overflow-x-auto scrollbar-none">
        {[
          { id: 'all', label: `All Orders (${orders.length})` },
          { id: 'active', label: 'Active Shipments' },
          { id: 'delivered', label: 'Delivered' },
          { id: 'cancelled', label: 'Cancelled' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-xl typo-button font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === tab.id
                ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-sm shadow-orange-500/25'
                : 'text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white hover:bg-amber-50 dark:hover:bg-[#14100c]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Orders List */}
      {filteredOrders.length === 0 ? (
        <div className="p-10 sm:p-12 text-center rounded-2xl border border-amber-200/80 dark:border-stone-800 bg-white dark:bg-[#0c0a09]/60 text-stone-500 dark:text-stone-400 space-y-3">
          <Package className="h-10 w-10 mx-auto text-amber-500/40" />
          <p className="typo-body">No orders found in this category.</p>
        </div>
      ) : (
        <div className="space-y-4 sm:space-y-6">
          {filteredOrders.map((order) => {
            const isDelivered = order.status === 'delivered';
            const isCancelled = order.status === 'cancelled';
            const isShipped = order.status === 'shipped';
            const isProcessingStatus = order.status === 'processing';

            return (
              <div
                key={order.id}
                className="rounded-2xl bg-white dark:bg-[#0c0a09] border border-amber-200/80 dark:border-stone-800 overflow-hidden shadow-sm space-y-3 sm:space-y-4"
              >
                {/* Order Top Bar */}
                <div className="p-3.5 sm:p-4 md:px-6 bg-amber-50/50 dark:bg-[#14100c] border-b border-amber-200/70 dark:border-stone-800 flex flex-wrap items-center justify-between gap-3 typo-nav">
                  <div className="flex flex-wrap items-center gap-3 sm:gap-4">
                    <div>
                      <span className="typo-label text-stone-500 dark:text-stone-400 block">Order Placed</span>
                      <span className="font-semibold text-stone-900 dark:text-white">
                        {new Date(order.created_at).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </span>
                    </div>

                    <div>
                      <span className="typo-label text-stone-500 dark:text-stone-400 block">Total Amount</span>
                      <span className="font-bold text-orange-600 dark:text-amber-400">
                        ₹{order.total_amount.toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div>
                      <span className="typo-label text-stone-500 dark:text-stone-400 block">Ship To</span>
                      <span className="text-stone-800 dark:text-stone-300 font-medium">{order.shipping_address?.name || 'Aarav Sharma'}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 sm:gap-3">
                    <span className="font-mono typo-label normal-case font-bold text-orange-600 dark:text-amber-400 bg-white dark:bg-[#0c0a09] px-2 sm:px-2.5 py-1 rounded-lg border border-amber-200/80 dark:border-stone-800">
                      #{order.id}
                    </span>

                    <button
                      onClick={() => onTrackWithVoice(order.id)}
                      className="px-2.5 sm:px-3 py-1.5 rounded-lg bg-orange-500/15 hover:bg-orange-500/25 text-orange-700 dark:text-orange-300 border border-orange-500/30 typo-button font-bold flex items-center gap-1.5 transition-all shadow-sm shadow-orange-500/20 cursor-pointer"
                    >
                      <Mic className="h-3 w-3" />
                      <span className="hidden sm:inline">Track via Voice</span>
                      <span className="sm:hidden">Voice</span>
                    </button>
                  </div>
                </div>

                {/* Tracking Progress Bar */}
                <div className="px-3.5 sm:px-6 pt-1 sm:pt-2">
                  <div className="p-3 sm:p-4 rounded-xl bg-stone-50 dark:bg-[#14100c] border border-amber-200/70 dark:border-stone-800 space-y-2.5 sm:space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-1 typo-nav">
                      <div className="flex items-center gap-1.5 sm:gap-2">
                        {isDelivered && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                        {isShipped && <Truck className="h-4 w-4 text-orange-500 animate-pulse" />}
                        {isProcessingStatus && <Clock className="h-4 w-4 text-amber-500" />}
                        {isCancelled && <XCircle className="h-4 w-4 text-stone-400" />}
                        <span className="font-bold text-stone-900 dark:text-white uppercase tracking-wide">
                          Status: {order.status.replace(/_/g, ' ')}
                        </span>
                      </div>

                      <span className="typo-nav text-stone-500 dark:text-stone-400">
                        Carrier: <strong className="text-stone-900 dark:text-white">{order.carrier}</strong> ({order.tracking_number})
                      </span>
                    </div>

                    {/* Timeline Milestones */}
                    {!isCancelled && (
                      <div className="grid grid-cols-4 gap-1 sm:gap-2 text-center typo-label font-bold">
                        <div className="space-y-1">
                          <div className="h-1.5 rounded-full bg-emerald-500" />
                          <span className="text-emerald-600 dark:text-emerald-400 normal-case">Ordered</span>
                        </div>
                        <div className="space-y-1">
                          <div
                            className={`h-1.5 rounded-full ${
                              ['shipped', 'out_for_delivery', 'delivered'].includes(order.status)
                                ? 'bg-emerald-500'
                                : 'bg-stone-200 dark:bg-stone-800'
                            }`}
                          />
                          <span className={['shipped', 'out_for_delivery', 'delivered'].includes(order.status) ? 'text-emerald-600 dark:text-emerald-400 normal-case' : 'text-stone-400 dark:text-stone-500 normal-case'}>
                            Dispatched
                          </span>
                        </div>
                        <div className="space-y-1">
                          <div
                            className={`h-1.5 rounded-full ${
                              ['out_for_delivery', 'delivered'].includes(order.status)
                                ? 'bg-emerald-500'
                                : order.status === 'shipped'
                                ? 'bg-orange-500 animate-pulse'
                                : 'bg-stone-200 dark:bg-stone-800'
                            }`}
                          />
                          <span className={['out_for_delivery', 'delivered'].includes(order.status) ? 'text-emerald-600 dark:text-emerald-400 normal-case' : order.status === 'shipped' ? 'text-orange-600 dark:text-amber-400 normal-case' : 'text-stone-400 dark:text-stone-500 normal-case'}>
                            In Transit
                          </span>
                        </div>
                        <div className="space-y-1">
                          <div className={`h-1.5 rounded-full ${isDelivered ? 'bg-emerald-500' : 'bg-stone-200 dark:bg-stone-800'}`} />
                          <span className={isDelivered ? 'text-emerald-600 dark:text-emerald-400 normal-case' : 'text-stone-400 dark:text-stone-500 normal-case'}>
                            Delivered
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Items in Order */}
                <div className="px-3.5 sm:px-6 space-y-3">
                  {order.items.map((item) => (
                    <div key={item.id} className="flex items-center gap-3 sm:gap-4 py-2 border-b border-amber-100 dark:border-stone-800/60 last:border-0">
                      <img
                        src={item.product_image}
                        alt={item.product_title}
                        className="h-12 w-12 sm:h-16 sm:w-16 rounded-xl object-cover border border-amber-200/60 dark:border-stone-800 bg-amber-50 dark:bg-[#070709] shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="typo-product-name font-medium text-stone-900 dark:text-white truncate">
                          {item.product_title}
                        </h4>
                        <p className="typo-label normal-case text-stone-500 dark:text-stone-400 mt-0.5">
                          Qty: {item.quantity} • Unit Price: ₹{item.unit_price.toLocaleString('en-IN')}
                        </p>
                      </div>
                      <span className="typo-product-price font-bold text-stone-900 dark:text-white shrink-0">
                        ₹{item.total_price.toLocaleString('en-IN')}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Order Footer & Consequential Actions */}
                <div className="p-3.5 sm:p-4 md:px-6 bg-amber-50/40 dark:bg-[#14100c] border-t border-amber-200/70 dark:border-stone-800 flex flex-wrap items-center justify-between gap-3 typo-nav">
                  <div className="text-stone-500 dark:text-stone-400">
                    Payment Method: <span className="text-stone-900 dark:text-white font-medium">{order.payment_method}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Cancellation Button */}
                    {order.can_cancel && (
                      <button
                        onClick={() => setCancellationOrderId(order.id)}
                        className="px-3.5 py-1.5 rounded-lg bg-orange-500/15 hover:bg-orange-500/25 text-orange-700 dark:text-orange-400 border border-orange-500/30 typo-button font-bold transition-all cursor-pointer"
                      >
                        Cancel Order
                      </button>
                    )}

                    {/* Return Request Button */}
                    {order.can_return && (
                      <button
                        onClick={() => setReturnOrderId(order.id)}
                        className="px-3.5 py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-800 dark:text-amber-300 border border-amber-500/30 typo-button font-bold transition-all cursor-pointer"
                      >
                        Request Return / Replacement
                      </button>
                    )}

                    {order.returns && order.returns.length > 0 && (
                      <span className="px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30 typo-nav font-semibold">
                        Return {order.returns[0].status.toUpperCase()}
                      </span>
                    )}

                    {isCancelled && (
                      <span className="typo-nav text-stone-500 font-semibold italic">
                        {order.cancellation_reason || 'Order cancelled'}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Cancellation Confirmation Modal */}
      {cancellationOrderId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/60 dark:bg-black/85 backdrop-blur-md">
          <div className="w-full max-w-md p-6 rounded-2xl bg-white dark:bg-[#0c0d14] border border-amber-200/80 dark:border-stone-800 shadow-2xl shadow-orange-950/20 space-y-4">
            <div className="flex items-center gap-3 text-orange-600 dark:text-orange-400">
              <AlertCircle className="h-6 w-6 shrink-0" />
              <h3 className="font-display text-stone-900 dark:text-white" style={{ fontSize: 'clamp(1rem, 1.2vw + 0.5rem, 1.25rem)', fontWeight: 600 }}>Confirm Order Cancellation</h3>
            </div>

            <p className="typo-body text-stone-600 dark:text-stone-300">
              Are you sure you want to cancel Order <strong>#{cancellationOrderId}</strong>?
              A full simulated refund will be credited back to your payment method.
            </p>

            <div className="space-y-1.5">
              <label className="typo-nav text-stone-500 dark:text-stone-400">Reason for cancellation:</label>
              <select
                value={cancellationReason}
                onChange={(e) => setCancellationReason(e.target.value)}
                className="w-full bg-stone-50 dark:bg-[#070709] border border-amber-200/80 dark:border-stone-800 rounded-xl px-3 py-2 typo-nav text-stone-900 dark:text-stone-100 outline-none focus:border-orange-500"
              >
                <option value="Found lower price elsewhere">Found lower price elsewhere</option>
                <option value="Order placed by mistake">Order placed by mistake</option>
                <option value="Delivery time is too long">Delivery time is too long</option>
                <option value="Changed mind">Changed mind</option>
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setCancellationOrderId(null)}
                className="px-4 py-2 rounded-xl bg-stone-100 dark:bg-[#070709] text-stone-700 dark:text-stone-300 hover:text-stone-950 dark:hover:text-white border border-amber-200/80 dark:border-stone-800 typo-button font-semibold cursor-pointer"
              >
                Keep Order
              </button>
              <button
                onClick={handleConfirmCancel}
                disabled={isProcessing}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white typo-button font-bold shadow-md shadow-orange-500/20 transition-all cursor-pointer"
              >
                {isProcessing ? 'Cancelling...' : 'Confirm Cancellation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Return Request Modal */}
      {returnOrderId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/60 dark:bg-black/85 backdrop-blur-md">
          <div className="w-full max-w-md p-6 rounded-2xl bg-white dark:bg-[#0c0d14] border border-amber-200/80 dark:border-stone-800 shadow-2xl shadow-orange-950/20 space-y-4">
            <div className="flex items-center gap-3 text-orange-600 dark:text-amber-400">
              <RotateCcw className="h-6 w-6 shrink-0" />
              <h3 className="font-display text-stone-900 dark:text-white" style={{ fontSize: 'clamp(1rem, 1.2vw + 0.5rem, 1.25rem)', fontWeight: 600 }}>Submit 7-Day Return Request</h3>
            </div>

            <p className="typo-body text-stone-600 dark:text-stone-300">
              You are requesting a return for Order <strong>#{returnOrderId}</strong> within the 7-day policy.
              Free doorstep pickup will be arranged.
            </p>

            <div className="space-y-1.5">
              <label className="typo-nav text-stone-500 dark:text-stone-400">Reason for return:</label>
              <select
                value={returnReason}
                onChange={(e) => setReturnReason(e.target.value)}
                className="w-full bg-stone-50 dark:bg-[#070709] border border-amber-200/80 dark:border-stone-800 rounded-xl px-3 py-2 typo-nav text-stone-900 dark:text-stone-100 outline-none focus:border-orange-500"
              >
                <option value="Item defective / does not meet expectation">Item defective / does not meet expectation</option>
                <option value="Received wrong item or size">Received wrong item or size</option>
                <option value="Product quality not as described">Product quality not as described</option>
                <option value="Package arrived damaged">Package arrived damaged</option>
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setReturnOrderId(null)}
                className="px-4 py-2 rounded-xl bg-stone-100 dark:bg-[#070709] text-stone-700 dark:text-stone-300 hover:text-stone-950 dark:hover:text-white border border-amber-200/80 dark:border-stone-800 typo-button font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReturn}
                disabled={isProcessing}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-400 hover:from-orange-600 hover:to-amber-500 text-white dark:text-stone-950 typo-button font-bold shadow-md shadow-orange-500/25 transition-all cursor-pointer"
              >
                {isProcessing ? 'Submitting...' : 'Submit Return Request'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
