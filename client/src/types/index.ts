export interface ActionItem {
  task: string;
  assignee: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'in_progress' | 'completed';
}

export interface CustomerCommitment {
  promise: string;
  deadline?: string | null;
  made_by: string;
}

export interface ConversationInsight {
  id: string;
  conversation_id: string;
  summary: string;
  customer_intent: string;
  primary_issue: string;
  action_items: ActionItem[];
  commitments: CustomerCommitment[];
  resolution_status: 'resolved' | 'unresolved' | 'escalated' | 'pending_action';
  escalation_level: 'none' | 'low' | 'medium' | 'high' | 'critical';
  escalation_reason?: string | null;
  sentiment_label: 'positive' | 'neutral' | 'negative' | 'frustrated';
  sentiment_score: number;
  frustration_index: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  filename: string;
  file_size_bytes: number;
  content_type: string;
  language_code: string;
  status: 'uploaded' | 'transcribing' | 'completed' | 'failed';
  transcript?: string | null;
  confidence_score?: number | null;
  audio_duration_seconds?: number | null;
  error_message?: string | null;
  customer_id?: string | null;
  order_id?: string | null;
  product_id?: string | null;
  source?: string;
  detected_intent?: string | null;
  created_at: string;
  updated_at: string;
  insight?: ConversationInsight | null;
}

export interface ConversationListResponse {
  items: Conversation[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LanguageStat {
  code: string;
  name: string;
  count: number;
  percentage: number;
}

export interface SentimentDistribution {
  positive: number;
  neutral: number;
  negative: number;
  frustrated: number;
}

export interface EscalationDistribution {
  none: number;
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface DashboardStats {
  total_conversations: number;
  completed_conversations: number;
  processing_conversations: number;
  failed_conversations: number;
  success_rate_percentage: number;
  avg_duration_seconds: number;
  total_insights_generated: number;
  escalated_cases_count: number;
  language_distribution: LanguageStat[];
  sentiment_distribution: SentimentDistribution;
  escalation_distribution: EscalationDistribution;
}

export interface TTSResponse {
  id: string;
  conversation_id?: string | null;
  voice_name: string;
  language_code: string;
  audio_base64: string;
  media_type: string;
  created_at: string;
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  gnani_configured: boolean;
  provider: string;
}

// ==========================================
// E-COMMERCE SPECIFIC TYPES
// ==========================================

export interface Category {
  id: string;
  name: string;
  slug: string;
  icon: string;
  description?: string | null;
}

export interface Product {
  id: string;
  title: string;
  slug: string;
  category_id: string;
  price: number;
  original_price: number;
  rating: number;
  reviews_count: number;
  stock: number;
  image_url: string;
  badge?: string | null;
  description: string;
  specifications: Record<string, any>;
  return_window_days: number;
  is_featured: boolean;
  created_at: string;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CartItem {
  id: string;
  product_id: string;
  product: Product;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Cart {
  id: string;
  customer_id: string;
  items: CartItem[];
  subtotal: number;
  shipping_fee: number;
  tax_amount: number;
  total_amount: number;
  item_count: number;
}

export interface TrackingEvent {
  status: string;
  title: string;
  timestamp: string;
  location: string;
  description: string;
}

export interface OrderItem {
  id: string;
  product_id: string;
  product_title: string;
  product_image: string;
  unit_price: number;
  quantity: number;
  total_price: number;
}

export interface ReturnRequest {
  id: string;
  order_id: string;
  reason: string;
  status: 'requested' | 'approved' | 'rejected' | 'refund_processed';
  refund_amount: number;
  created_at: string;
  resolution_notes?: string | null;
}

export interface Order {
  id: string;
  customer_id: string;
  status: 'processing' | 'shipped' | 'out_for_delivery' | 'delivered' | 'cancelled';
  subtotal: number;
  shipping_fee: number;
  tax_amount: number;
  total_amount: number;
  payment_method: string;
  payment_status: string;
  shipping_address: {
    name: string;
    phone: string;
    address_line: string;
    city: string;
    state: string;
    postal_code: string;
  };
  tracking_number: string;
  carrier: string;
  expected_delivery?: string | null;
  delivered_at?: string | null;
  cancelled_at?: string | null;
  cancellation_reason?: string | null;
  tracking_events: TrackingEvent[];
  created_at: string;
  items: OrderItem[];
  returns: ReturnRequest[];
  can_cancel: boolean;
  can_return: boolean;
}

export interface OrderListResponse {
  items: Order[];
  total: number;
}

export interface AssistantActionProposal {
  action: 'cancel_order' | 'create_return' | 'add_to_cart';
  target_id: string;
  confirmation_prompt: string;
  details: Record<string, any>;
  confirmation_token?: string;
  expires_at?: string;
}

export interface AssistantMessageResponse {
  success: boolean;
  reply_text: string;
  intent: string;
  detected_language: string;
  action_pending_confirmation?: AssistantActionProposal | null;
  products?: Product[] | null;
  order?: Order | null;
  cart?: Cart | null;
  audio_base64?: string | null;
  conversation_id: string;
  llm_provider?: string | null;
  intent_confidence?: number | null;
  reasoning?: string | null;
  consequential_action_required?: boolean;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  transcriptMeta?: {
    confidence?: number;
    request_id?: string;
    duration?: number;
    isRealGnani?: boolean;
  };
  actionProposal?: AssistantActionProposal | null;
  recommendedProducts?: Product[] | null;
  orderCard?: Order | null;
  audioUrl?: string | null;
  isAudioLoading?: boolean;
  llmProvider?: string | null;
  intent?: string | null;
  intentConfidence?: number | null;
  reasoning?: string | null;
  consequentialActionRequired?: boolean;
}

export interface SavedConversation {
  id: string;
  title: string;
  language: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
  contextPage?: string;
}

export interface GeminiStatusResponse {
  provider: string;
  model_id: string;
  configured: boolean;
  enabled: boolean;
  timeout_seconds: number;
  supported_languages: string[];
  health: {
    available: boolean;
    configured: boolean;
    model: string;
    provider: string;
    display_name?: string;
    error?: string;
  };
}

export interface HuggingFaceStatusResponse {
  provider: string;
  model_id: string;
  configured: boolean;
  enabled: boolean;
  base_url: string;
  timeout_seconds: number;
  supported_languages: string[];
  health: {
    available: boolean;
    configured: boolean;
    model: string;
    provider: string;
    base_url?: string;
    error?: string;
  };
}

export interface AssistantHealthResponse {
  status: string;
  service: string;
  ai_provider: string;
  huggingface_llm?: {
    enabled: boolean;
    configured: boolean;
    model_name: string;
    base_url: string;
    health: Record<string, any>;
  };
  gemini_llm?: {
    enabled: boolean;
    configured: boolean;
    model_name: string;
    health: Record<string, any>;
  };
  evon_llm?: {
    enabled: boolean;
    configured: boolean;
    model_name: string;
    hf_repo_id: string;
    health: Record<string, any>;
  };
  gnani_speech?: {
    configured: boolean;
    base_url: string;
    stt_endpoint: string;
    tts_endpoint: string;
  };
}

export interface EvonStatusResponse {
  model_id: string;
  configured: boolean;
  enabled?: boolean;
  endpoint: string;
  architecture: string;
  huggingface_repo: string;
  hf_repo_id?: string;
  supported_languages: string[];
  inference_engine_recommendations: {
    vllm: string;
    sglang: string;
  };
  health: {
    available: boolean;
    endpoint?: string;
    reason?: string;
    model?: string;
  };
}

export interface AdminAnalytics {
  store: {
    total_products: number;
    total_orders: number;
    active_orders: number;
    delivered_orders: number;
    cancelled_orders: number;
    total_returns: number;
    simulated_revenue: number;
    voice_conversations_count: number;
    transcription_success_rate: number;
    intent_distribution: Record<string, number>;
    language_distribution: Record<string, number>;
  };
  support: {
    total_conversations: number;
    completed_conversations: number;
    failed_conversations: number;
    success_rate_percentage: number;
    avg_duration_seconds: number;
    language_distribution: LanguageStat[];
    sentiment_distribution: SentimentDistribution;
    escalation_distribution: EscalationDistribution;
  };
  recent_conversations: Conversation[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string | null;
  address_line?: string | null;
  city?: string | null;
  state?: string | null;
  postal_code?: string | null;
  created_at?: string;
}

export interface UserRegisterPayload {
  name: string;
  email: string;
  password: string;
  phone?: string;
  address_line?: string;
  city?: string;
  state?: string;
  postal_code?: string;
}

export interface UserLoginPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
  message: string;
}

