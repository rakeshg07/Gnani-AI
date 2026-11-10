import {
  Conversation,
  ConversationListResponse,
  DashboardStats,
  TTSResponse,
  SystemHealth,
  ConversationInsight,
  Category,
  Product,
  ProductListResponse,
  Cart,
  Order,
  OrderListResponse,
  ReturnRequest,
  AssistantMessageResponse,
  AdminAnalytics,
  EvonStatusResponse,
  GeminiStatusResponse,
  HuggingFaceStatusResponse,
  AssistantHealthResponse,
  User,
  UserRegisterPayload,
  UserLoginPayload,
  AuthResponse,
} from '@/types';

const API_BASE = '/api';

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem('voiceiq_token');
  } catch {
    return null;
  }
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function registerUser(payload: UserRegisterPayload): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Registration failed');
  }
  const data: AuthResponse = await res.json();
  if (data.token) {
    localStorage.setItem('voiceiq_token', data.token);
    localStorage.setItem('voiceiq_user', JSON.stringify(data.user));
  }
  return data;
}

export async function loginUser(payload: UserLoginPayload): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed. Please check credentials.');
  }
  const data: AuthResponse = await res.json();
  if (data.token) {
    localStorage.setItem('voiceiq_token', data.token);
    localStorage.setItem('voiceiq_user', JSON.stringify(data.user));
  }
  return data;
}

export async function fetchCurrentUser(): Promise<User> {
  const headers = getAuthHeaders();
  const res = await fetch(`${API_BASE}/auth/me`, { headers });
  if (!res.ok) {
    throw new Error('Unauthorized or session expired');
  }
  const user: User = await res.json();
  localStorage.setItem('voiceiq_user', JSON.stringify(user));
  return user;
}

export async function logoutUser(): Promise<void> {
  try {
    const headers = getAuthHeaders();
    await fetch(`${API_BASE}/auth/logout`, { method: 'POST', headers });
  } catch {
    // Ignore network error on logout
  } finally {
    localStorage.removeItem('voiceiq_token');
    localStorage.removeItem('voiceiq_user');
  }
}


export async function fetchAssistantHealth(): Promise<Record<string, any>> {
  const res = await fetch(`${API_BASE}/assistant/health`);
  if (!res.ok) throw new Error('Failed to fetch assistant health');
  return res.json();
}

export async function sendAssistantVoiceAudio(
  audioBlob: Blob,
  params: {
    languageCode?: string;
    currentPage?: string;
    productId?: string;
    orderId?: string;
    synthesizeAudio?: boolean;
    customerId?: string;
  }
): Promise<AssistantMessageResponse> {
  const formData = new FormData();
  formData.append('file', audioBlob, 'customer_query.wav');
  formData.append('language_code', params.languageCode || 'en-IN');
  formData.append('current_page', params.currentPage || 'home');
  if (params.productId) formData.append('product_id', params.productId);
  if (params.orderId) formData.append('order_id', params.orderId);
  formData.append('synthesize_audio', String(params.synthesizeAudio ?? false));

  const custId = params.customerId || 'cust_demo_001';
  const res = await fetch(`${API_BASE}/assistant/voice?customer_id=${custId}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Voice assistant audio processing failed');
  }
  return res.json();
}

export async function fetchEvonStatus(): Promise<EvonStatusResponse> {
  const res = await fetch(`${API_BASE}/assistant/evon/status`);
  if (!res.ok) throw new Error('Failed to fetch Evon status');
  return res.json();
}

export async function fetchHuggingFaceStatus(): Promise<HuggingFaceStatusResponse> {
  const res = await fetch(`${API_BASE}/assistant/huggingface/status`);
  if (!res.ok) throw new Error('Failed to fetch Hugging Face status');
  return res.json();
}

export async function fetchGeminiStatus(): Promise<GeminiStatusResponse> {
  const res = await fetch(`${API_BASE}/assistant/gemini/status`);
  if (!res.ok) throw new Error('Failed to fetch Gemini status');
  return res.json();
}

// --- System & Core Support ---
export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/analytics/dashboard`);
  if (!res.ok) throw new Error('Failed to load dashboard metrics');
  return res.json();
}

export async function fetchConversations(params?: {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string;
  languageCode?: string;
}): Promise<ConversationListResponse> {
  const query = new URLSearchParams();
  if (params?.page) query.set('page', params.page.toString());
  if (params?.pageSize) query.set('page_size', params.pageSize.toString());
  if (params?.search) query.set('search', params.search);
  if (params?.status && params.status !== 'all') query.set('status', params.status);
  if (params?.languageCode && params.languageCode !== 'all') query.set('language_code', params.languageCode);

  const res = await fetch(`${API_BASE}/conversations?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to load conversations');
  return res.json();
}

export async function fetchConversationDetail(id: string): Promise<Conversation> {
  const res = await fetch(`${API_BASE}/conversations/${id}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Conversation not found');
  }
  return res.json();
}

export async function uploadAudioConversation(
  file: File,
  languageCode: string = 'en-IN',
  preferredLanguage?: string
): Promise<Conversation> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('language_code', languageCode);
  if (preferredLanguage) formData.append('preferred_language', preferredLanguage);

  const res = await fetch(`${API_BASE}/conversations`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.error?.message || 'Failed to upload audio');
  }
  return res.json();
}

export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 404) {
    throw new Error('Failed to delete conversation');
  }
}

export async function triggerAnalysis(id: string): Promise<ConversationInsight> {
  const res = await fetch(`${API_BASE}/conversations/${id}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force_reanalyze: true }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to generate conversation insights');
  }
  return res.json();
}

export async function synthesizeTTS(payload: {
  text: string;
  voice: string;
  language: string;
  model?: string;
  speed?: number;
  conversationId?: string;
}): Promise<TTSResponse> {
  const res = await fetch(`${API_BASE}/tts/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      conversation_id: payload.conversationId,
      text: payload.text,
      voice: payload.voice,
      language: payload.language,
      model: payload.model || 'timbre-v3.0',
      speed: payload.speed || 1.0,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to synthesize speech');
  }
  return res.json();
}

// ==========================================
// E-COMMERCE API SERVICES
// ==========================================

export async function fetchCategories(): Promise<Category[]> {
  const res = await fetch(`${API_BASE}/categories`);
  if (!res.ok) throw new Error('Failed to load product categories');
  return res.json();
}

export async function fetchProducts(params?: {
  categoryId?: string;
  search?: string;
  minPrice?: number;
  maxPrice?: number;
  sortBy?: string;
  page?: number;
  pageSize?: number;
}): Promise<ProductListResponse> {
  const query = new URLSearchParams();
  if (params?.categoryId && params.categoryId !== 'all') query.set('category_id', params.categoryId);
  if (params?.search) query.set('search', params.search);
  if (params?.minPrice !== undefined) query.set('min_price', params.minPrice.toString());
  if (params?.maxPrice !== undefined) query.set('max_price', params.maxPrice.toString());
  if (params?.sortBy) query.set('sort_by', params.sortBy);
  if (params?.page) query.set('page', params.page.toString());
  if (params?.pageSize) query.set('page_size', params.pageSize.toString());

  const res = await fetch(`${API_BASE}/products?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to load product catalog');
  return res.json();
}

export async function fetchProductDetail(id: string): Promise<Product> {
  const res = await fetch(`${API_BASE}/products/${id}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Product not found');
  }
  return res.json();
}

export async function fetchCart(customerId: string = 'cust_demo_001'): Promise<Cart> {
  const res = await fetch(`${API_BASE}/cart?customer_id=${customerId}`);
  if (!res.ok) throw new Error('Failed to load shopping cart');
  return res.json();
}

export async function addToCart(
  productId: string,
  quantity: number = 1,
  customerId: string = 'cust_demo_001'
): Promise<Cart> {
  const res = await fetch(`${API_BASE}/cart/items?customer_id=${customerId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: productId, quantity }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to add item to cart');
  }
  return res.json();
}

export async function updateCartItem(
  itemId: string,
  quantity: number,
  customerId: string = 'cust_demo_001'
): Promise<Cart> {
  const res = await fetch(`${API_BASE}/cart/items/${itemId}?customer_id=${customerId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quantity }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update quantity');
  }
  return res.json();
}

export async function removeCartItem(
  itemId: string,
  customerId: string = 'cust_demo_001'
): Promise<Cart> {
  const res = await fetch(`${API_BASE}/cart/items/${itemId}?customer_id=${customerId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to remove item from cart');
  return res.json();
}

export async function simulateCheckout(payload: {
  customerId?: string;
  shippingAddress?: {
    name: string;
    phone: string;
    address_line: string;
    city: string;
    state: string;
    postal_code: string;
  };
  paymentMethod?: string;
}): Promise<Order> {
  const res = await fetch(`${API_BASE}/checkout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      customer_id: payload.customerId || 'cust_demo_001',
      shipping_address: payload.shippingAddress,
      payment_method: payload.paymentMethod || 'UPI (Simulated)',
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Checkout simulation failed');
  }
  return res.json();
}

export async function fetchOrders(customerId: string = 'cust_demo_001'): Promise<OrderListResponse> {
  const res = await fetch(`${API_BASE}/orders?customer_id=${customerId}`);
  if (!res.ok) throw new Error('Failed to load orders');
  return res.json();
}

export async function fetchOrderDetail(orderId: string, customerId: string = 'cust_demo_001'): Promise<Order> {
  const res = await fetch(`${API_BASE}/orders/${orderId}?customer_id=${customerId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Order not found');
  }
  return res.json();
}

export async function cancelOrder(
  orderId: string,
  reason?: string,
  customerId: string = 'cust_demo_001'
): Promise<Order> {
  const res = await fetch(`${API_BASE}/orders/${orderId}/cancel?customer_id=${customerId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to cancel order');
  }
  return res.json();
}

export async function requestOrderReturn(
  orderId: string,
  reason: string,
  customerId: string = 'cust_demo_001'
): Promise<ReturnRequest> {
  const res = await fetch(`${API_BASE}/orders/${orderId}/returns?customer_id=${customerId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to request return');
  }
  return res.json();
}

// ==========================================
// VOICE ASSISTANT & GNANI SPEECH SERVICES
// ==========================================

export async function transcribeWithGnani(
  audioBlob: Blob,
  filename: string = 'voice_query.wav',
  languageCode: string = 'en-IN'
): Promise<{
  success: boolean;
  transcript: string;
  confidence: number;
  duration?: number;
  request_id?: string;
  language_code: string;
}> {
  const formData = new FormData();
  formData.append('file', audioBlob, filename);
  formData.append('language_code', languageCode);

  const res = await fetch(`${API_BASE}/voice/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gnani voice transcription failed');
  }
  return res.json();
}

export async function sendAssistantMessage(payload: {
  message: string;
  currentPage: string;
  productId?: string;
  orderId?: string;
  languageCode?: string;
  synthesizeAudio?: boolean;
  conversationId?: string;
}): Promise<AssistantMessageResponse> {
  const res = await fetch(`${API_BASE}/assistant/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: payload.message,
      current_page: payload.currentPage,
      product_id: payload.productId,
      order_id: payload.orderId,
      language_code: payload.languageCode || 'en-IN',
      synthesize_audio: payload.synthesizeAudio ?? false,
      conversation_id: payload.conversationId,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Voice assistant failed to respond');
  }
  return res.json();
}

export async function confirmAssistantAction(payload: {
  conversationId: string;
  action: string;
  targetId: string;
  confirmed: boolean;
  reason?: string;
  confirmationToken?: string;
}): Promise<{
  success: boolean;
  action: string;
  target_id: string;
  confirmed: boolean;
  message: string;
  order?: Order;
  return_request?: ReturnRequest;
}> {
  const res = await fetch(`${API_BASE}/assistant/confirm-action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      conversation_id: payload.conversationId,
      action: payload.action,
      target_id: payload.targetId,
      confirmed: payload.confirmed,
      reason: payload.reason,
      confirmation_token: payload.confirmationToken,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Action confirmation failed');
  }
  return res.json();
}

export async function fetchAdminAnalytics(): Promise<AdminAnalytics> {
  const res = await fetch(`${API_BASE}/admin/analytics`);
  if (!res.ok) throw new Error('Failed to load store and support analytics');
  return res.json();
}

// --- Languages & Voices ---
export const SUPPORTED_LANGUAGES = [
  { code: 'en-IN', name: 'English (India)', native: 'English', region: 'Pan-India' },
  { code: 'hi-IN', name: 'Hindi', native: 'हिंदी', region: 'North / Central India' },
  { code: 'ta-IN', name: 'Tamil', native: 'தமிழ்', region: 'Tamil Nadu' },
  { code: 'te-IN', name: 'Telugu', native: 'తెలుగు', region: 'Andhra / Telangana' },
  { code: 'kn-IN', name: 'Kannada', native: 'ಕನ್ನಡ', region: 'Karnataka' },
  { code: 'ml-IN', name: 'Malayalam', native: 'മലയാളം', region: 'Kerala' },
  { code: 'mr-IN', name: 'Marathi', native: 'मराठी', region: 'Maharashtra' },
  { code: 'bn-IN', name: 'Bengali', native: 'বাংলা', region: 'West Bengal' },
  { code: 'gu-IN', name: 'Gujarati', native: 'ગુજરાતી', region: 'Gujarat' },
  { code: 'pa-IN', name: 'Punjabi', native: 'ਪੰਜਾਬੀ', region: 'Punjab' },
  { code: 'or-IN', name: 'Odia', native: 'ଓଡ଼ିଆ', region: 'Odisha' },
];

export const TIMBRE_VOICES = [
  { name: 'Nalini', gender: 'Female', description: 'Empathetic & Warm (Customer Care)' },
  { name: 'Shivani', gender: 'Female', description: 'Professional & Expressive' },
  { name: 'Yashvi', gender: 'Female', description: 'Clear & Energetic' },
  { name: 'Avinash', gender: 'Male', description: 'Authoritative & Calm (Support Lead)' },
];
