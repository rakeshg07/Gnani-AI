import React, { useState, useRef, useEffect } from 'react';
import {
  Mic,
  MicOff,
  Upload,
  Send,
  X,
  Volume2,
  VolumeX,
  RefreshCw,
  ShoppingBag,
  Package,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ArrowDown,
  RotateCcw,
  Play,
  Pause,
  History,
  Plus,
  Trash2,
  Search,
  MessageSquare,
} from 'lucide-react';
import {
  transcribeWithGnani,
  sendAssistantMessage,
  confirmAssistantAction,
  fetchEvonStatus,
  fetchAssistantHealth,
  SUPPORTED_LANGUAGES,
} from '@/lib/api';
import {
  ChatMessage,
  AssistantActionProposal,
  Product,
  Order,
  EvonStatusResponse,
  AssistantHealthResponse,
  SavedConversation,
} from '@/types';
import { WavRecorder } from '@/lib/wavRecorder';
import { RealtimeVoiceConversation, RealtimeVoiceState } from '@/lib/realtimeVoice';

const STORAGE_KEY = 'voiceiq_chat_history_v1';

function getStoredConversations(): SavedConversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveStoredConversations(convs: SavedConversation[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(convs));
  } catch (e) {
    console.warn('Failed to save conversations to localStorage', e);
  }
}

function formatConversationDate(timestampMs: number): string {
  const d = new Date(timestampMs);
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  const yesterday = new Date();
  yesterday.setDate(now.getDate() - 1);
  const isYesterday = d.toDateString() === yesterday.toDateString();

  if (isToday) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  if (isYesterday) {
    return 'Yesterday';
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

const WELCOME_MESSAGES: Record<string, string> = {
  'en-IN': 'Welcome to VoiceIQ India! , How can i assist you?',
  'hi-IN': 'वॉइसआईक्यू इंडिया में आपका स्वागत है! मैं आपकी क्या सहायता कर सकता हूँ?',
  'ta-IN': 'VoiceIQ இந்தியாவிற்கு வருக! நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?',
  'te-IN': 'VoiceIQ ఇండియాకు స్వాగతం! నేను మీకు ఎలా సహాయపడగలను?',
  'kn-IN': 'VoiceIQ ಇಂಡಿಯಾಗೆ ಸ್ವಾಗತ! ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?',
  'ml-IN': 'VoiceIQ ഇന്ത്യയിലേക്ക് സ്വാഗതം! ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കണം?',
  'mr-IN': 'VoiceIQ इंडियामध्ये आपले स्वागत आहे! मी आपली काय मदत करू शकतो?',
  'bn-IN': 'VoiceIQ ইন্ডিয়াতে স্বাগতম! আমি কীভাবে আপনাকে সাহায্য করতে পারি?',
  'gu-IN': 'VoiceIQ ઇન્ડિયામાં તમારું સ્વાગત છે! હું તમને કેવી રીતે મદદ કરી શકું?',
  'pa-IN': 'VoiceIQ ਇੰਡੀਆ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ! ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?',
  'or-IN': 'VoiceIQ ଇଣ୍ଡିଆକୁ ସ୍ୱାଗତ! ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?',
};

const QUICK_SUGGESTIONS: Record<string, string[]> = {
  'en-IN': ['Track my order', 'Earbuds under ₹2000', 'View my cart', 'Cancel my order'],
  'hi-IN': ['मेरा ऑर्डर कहाँ है?', '₹2000 के अंदर ईयरबड्स', 'मेरा कार्ट दिखाएं', 'ऑर्डर कैंसिल करें'],
  'ta-IN': ['என் ஆர்டர் எங்கே?', '₹2000-க்குள் இயர்பட்ஸ்', 'என் கார்ட்டைக் காட்டு', 'ஆர்டரை ரத்து செய்'],
  'te-IN': ['నా ఆర్డర్ ఎక్కడ ఉంది?', '₹2000 లోపు ఇయర్‌बడ్స్', 'నా కార్ట్ చూపించు', 'ఆర్డర్ రద్దు చేయండి'],
  'kn-IN': ['ನನ್ನ ಆರ್ಡರ್ ಎಲ್ಲಿದೆ?', '₹2000 ಒಳಗೆ ಇಯರ್‌ಬಡ್ಸ್', 'ನನ್ನ ಕಾರ್ಟ್ ತೋರಿಸಿ', 'ಆರ್ಡರ್ ರದ್ದು ಮಾಡಿ'],
  'ml-IN': ['എന്റെ ഓർഡർ എവിടെയാണ്?', '₹2000-ൽ താഴെയുള്ള ഇയർബഡുകൾ', 'എന്റെ കാർട്ട് കാണിക്കുക', 'ഓർഡർ റദ്ദാക്കുക'],
  'mr-IN': ['माझी ऑर्डर कुठे आहे?', '₹2000 च्या आत इयरबड्स', 'माझी कार्ट दाखवा', 'ऑर्डर रद्द करा'],
  'bn-IN': ['আমার অর্ডার কোথায়?', '₹2000 এর মধ্যে ইয়ারবাডস', 'আমার কার্ট দেখান', 'অর্ডার বাতিল করুন'],
  'gu-IN': ['મારો ઓર્ડર ક્યાં છે?', '₹2000 ની અંદર ઇયરબડ્સ', 'મારું કાર્ਟ બતાવો', 'ઓર્ડર રદ કરો'],
  'pa-IN': ['ਮੇਰਾ ਆਰਡਰ ਕਿੱਥੇ ਹੈ?', '₹2000 ਦੇ ਅੰਦਰ ਈਅਰਬਡਸ', 'ਮੇਰਾ ਕਾਰਟ ਦਿਖਾਓ', 'ਆਰਡਰ ਰੱਦ ਕਰੋ'],
  'or-IN': ['ମୋ ଅର୍ଡର କେଉଁଠି?', '₹୨୦୦୦ ଭିତରେ ଇୟରବଡ୍ସ', 'ମୋ କାର୍ଟ ଦେଖାନ୍ତୁ', 'ଅର୍ଡର ବାତିଲ କରନ୍ତୁ'],
};

const INPUT_PLACEHOLDERS: Record<string, string> = {
  'en-IN': 'Ask in English (e.g. Track order VIQ-89214)...',
  'hi-IN': 'हिंदी में पूछें (उदा: मेरा ऑर्डर कहाँ है?)...',
  'ta-IN': 'தமிழில் கேளுங்கள் (उदा: என் ஆர்டர் எங்கே?)...',
  'te-IN': 'తెలుగులో అడగండి (उदा: నా ఆర్డర్ ఎక్కడ ఉంది?)...',
  'kn-IN': 'ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ (ಉದಾ: ನನ್ನ ಆರ್ಡರ್ ಎಲ್ಲಿದೆ?)...',
  'ml-IN': 'മലയാളത്തിൽ ചോദിക്കൂ (उदा: എന്റെ ഓർഡർ എവിടെയാണ്?)...',
  'mr-IN': 'मराठीत विचारा (उदा: माझी ऑर्डर कुठे आहे?)...',
  'bn-IN': 'বাংলায় জিজ্ঞাসা করুন (उदा: আমার অর্ডার কোথায়?)...',
  'gu-IN': 'ગુજરાતીમાં પૂછો (उदा: મારો ઓર્ડર ક્યાં છે?)...',
  'pa-IN': 'ਪੰਜਾਬੀ ਵਿੱਚ ਪੁੱਛੋ (उदा: ਮੇਰਾ ਆਰਡਰ ਕਿੱਥੇ ਹੈ?)...',
  'or-IN': 'ଓଡ଼ିଆରେ ପଚାରନ୍ତୁ (ଉଦା: ମୋ ଅର୍ଡର କେଉଁଠି ଅଛି?)...',
};

interface VoiceAssistantModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPage: string;
  activeProductId?: string;
  activeOrderId?: string;
  onSelectProduct?: (product: Product) => void;
  onAddToCart?: (product: Product) => void;
  onOrderUpdated?: () => void;
  selectedLanguage?: string;
  onSelectLanguage?: (lang: string) => void;
}

export const VoiceAssistantModal: React.FC<VoiceAssistantModalProps> = ({
  isOpen,
  onClose,
  currentPage,
  activeProductId,
  activeOrderId,
  onSelectProduct,
  onAddToCart,
  onOrderUpdated,
  selectedLanguage: propSelectedLanguage,
  onSelectLanguage,
}) => {
  const [internalLanguage, setInternalLanguage] = useState(() => {
    try {
      const saved = localStorage.getItem('voiceiq_preferred_language');
      return propSelectedLanguage || (saved && saved !== 'undefined' && saved !== 'null' ? saved : 'en-IN');
    } catch {
      return propSelectedLanguage || 'en-IN';
    }
  });
  const activeLanguage = propSelectedLanguage || internalLanguage || 'en-IN';

  // ChatGPT-style conversation persistence & history
  const [conversations, setConversations] = useState<SavedConversation[]>(() => getStoredConversations());
  const [activeConvId, setActiveConvId] = useState<string>(() => {
    const stored = getStoredConversations();
    return stored.length > 0 ? stored[0].id : `conv_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
  });
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [historySearch, setHistorySearch] = useState('');

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const stored = getStoredConversations();
    if (stored.length > 0 && stored[0].messages && stored[0].messages.length > 0) {
      return stored[0].messages;
    }
    return [
      {
        id: 'welcome',
        sender: 'assistant',
        text: WELCOME_MESSAGES[propSelectedLanguage || 'en-IN'] || WELCOME_MESSAGES['en-IN'],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ];
  });

  const [inputQuery, setInputQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState<'idle' | 'stt' | 'llm'>('idle');
  const [aiProvider, setAiProvider] = useState<'huggingface' | 'gemini' | 'evon' | 'local'>('huggingface');
  const [evonStatus, setEvonStatus] = useState<EvonStatusResponse | null>(null);
  const [synthesizeAudio, setSynthesizeAudio] = useState(false);
  const [activeAudioUrl, setActiveAudioUrl] = useState<string | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const [currentConversationId, setCurrentConversationId] = useState<string>(() => {
    const stored = getStoredConversations();
    return stored.length > 0 ? stored[0].id : '';
  });

  // ChatGPT-style history methods
  const persistConversation = (newMessages: ChatMessage[], lang?: string, forcedConvId?: string) => {
    const targetId = forcedConvId || activeConvId || currentConversationId || `conv_${Date.now()}`;
    const userMsgs = newMessages.filter((m) => m.sender === 'user');
    if (userMsgs.length === 0) return;

    const firstUserText = userMsgs[0].text.trim();
    const title = firstUserText.length > 36 ? `${firstUserText.slice(0, 36)}...` : firstUserText;

    setConversations((prev) => {
      const idx = prev.findIndex((c) => c.id === targetId);
      let updatedList: SavedConversation[];
      if (idx >= 0) {
        const existing = prev[idx];
        const updatedConv: SavedConversation = {
          ...existing,
          title: existing.title && existing.title !== 'New Conversation' ? existing.title : title,
          language: lang || existing.language || activeLanguage,
          updatedAt: Date.now(),
          messages: newMessages,
        };
        updatedList = [updatedConv, ...prev.filter((_, i) => i !== idx)];
      } else {
        const newConv: SavedConversation = {
          id: targetId,
          title: title || 'New Conversation',
          language: lang || activeLanguage,
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages: newMessages,
          contextPage: currentPage,
        };
        updatedList = [newConv, ...prev];
      }
      saveStoredConversations(updatedList);
      return updatedList;
    });
  };

  const startNewChat = () => {
    const newId = `conv_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
    const initialWelcome: ChatMessage = {
      id: `welcome_${Date.now()}`,
      sender: 'assistant',
      text: WELCOME_MESSAGES[activeLanguage] || WELCOME_MESSAGES['en-IN'],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setActiveConvId(newId);
    setCurrentConversationId(newId);
    setMessages([initialWelcome]);
    setIsHistoryOpen(false);
  };

  const loadConversation = (conv: SavedConversation) => {
    setActiveConvId(conv.id);
    setCurrentConversationId(conv.id);
    setMessages(conv.messages);
    setIsHistoryOpen(false);
  };

  const handleDeleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = conversations.filter((c) => c.id !== id);
    setConversations(updated);
    saveStoredConversations(updated);
    if (activeConvId === id) {
      if (updated.length > 0) {
        loadConversation(updated[0]);
      } else {
        startNewChat();
      }
    }
  };

  const clearAllConversations = () => {
    if (confirm('Clear all conversation history?')) {
      setConversations([]);
      saveStoredConversations([]);
      startNewChat();
    }
  };

  const filteredConversations = conversations.filter((c) => {
    if (!historySearch.trim()) return true;
    const q = historySearch.toLowerCase();
    return (
      c.title.toLowerCase().includes(q) ||
      c.messages.some((m) => m.text.toLowerCase().includes(q))
    );
  });

  // Continuous real-time voice call state & controller
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [liveState, setLiveState] = useState<RealtimeVoiceState>('IDLE');
  const [liveVolume, setLiveVolume] = useState<number>(0);
  const [livePartialTranscript, setLivePartialTranscript] = useState<string>('');
  const realtimeConvRef = useRef<RealtimeVoiceConversation | null>(null);

  const startLiveCall = async () => {
    try {
      // Synchronously unlock browser audio context on user interaction
      try {
        const unlockAudio = new Audio('data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=');
        unlockAudio.volume = 0.01;
        unlockAudio.play().then(() => {
          unlockAudio.pause();
        }).catch(() => {});
      } catch {}

      if (realtimeConvRef.current) {
        realtimeConvRef.current.stop();
      }

      const conv = new RealtimeVoiceConversation(
        activeLanguage,
        currentPage,
        activeConvId,
        {
          onStateChange: (state) => {
            setLiveState(state);
            if (state === 'SPEAKING' || state === 'LISTENING') {
              setLivePartialTranscript('');
            }
          },
          onPartialTranscript: (text) => {
            if (text && text !== 'listening') {
              setLivePartialTranscript(text);
            }
          },
          onFinalTranscript: (transcript) => {
            setLivePartialTranscript('');
            const userMsg: ChatMessage = {
              id: `user_live_${Date.now()}`,
              sender: 'user',
              text: transcript,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            };
            setMessages((prev) => {
              const updated = [...prev, userMsg];
              persistConversation(updated, activeLanguage, activeConvId);
              return updated;
            });
          },
          onAiThinking: () => {
            setLiveState('THINKING');
          },
          onAiTextDelta: () => {},
          onAiTextFinal: (text, products) => {
            // Check if incoming text is a welcome greeting (from session.start)
            const isGreeting = Object.values(WELCOME_MESSAGES).some(
              (w) => w.trim().toLowerCase() === text.trim().toLowerCase()
            );

            setMessages((prev) => {
              if (isGreeting) {
                // If only welcome greeting exists, update it cleanly to matching language
                if (prev.length <= 1 && prev[0]?.id.startsWith('welcome')) {
                  return [{ ...prev[0], text }];
                }
                return prev;
              }

              // Normal assistant response to user query (Route 2: Gemini Live Voice)
              const aiMsg: ChatMessage = {
                id: `ai_live_${Date.now()}`,
                sender: 'assistant',
                text: text,
                llmProvider: 'Gemini 2.5 Flash',
                recommendedProducts: products,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              };
              const updated = [...prev, aiMsg];
              persistConversation(updated, activeLanguage, activeConvId);
              return updated;
            });
          },
          onInterrupted: () => {
            setLiveState('INTERRUPTED');
            setLivePartialTranscript('');
          },
          onError: (err) => {
            console.warn('Real-time voice error:', err);
            setIsLiveMode(false);
          },
          onVolumeChange: (vol) => {
            setLiveVolume(vol);
          },
        }
      );

      realtimeConvRef.current = conv;
      setIsLiveMode(true);
      await conv.start();
    } catch (e: any) {
      alert(`Could not start Live Voice Call: ${e.message || e}`);
      setIsLiveMode(false);
    }
  };

  const stopLiveCall = () => {
    if (realtimeConvRef.current) {
      realtimeConvRef.current.stop();
      realtimeConvRef.current = null;
    }
    setIsLiveMode(false);
    setLiveState('IDLE');
    setLivePartialTranscript('');
  };

  const handleBargeIn = () => {
    if (realtimeConvRef.current) {
      realtimeConvRef.current.interrupt();
    }
  };

  // Clean up live call when modal closes
  useEffect(() => {
    if (!isOpen && isLiveMode) {
      stopLiveCall();
    }
  }, [isOpen, isLiveMode]);

  // Sync internal language if prop changes
  useEffect(() => {
    if (propSelectedLanguage && propSelectedLanguage !== internalLanguage) {
      setInternalLanguage(propSelectedLanguage);
    }
  }, [propSelectedLanguage]);

  // Update welcome greeting if fresh conversation
  useEffect(() => {
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].id === 'welcome') {
        return [
          {
            ...prev[0],
            text: WELCOME_MESSAGES[activeLanguage] || WELCOME_MESSAGES['en-IN'],
          },
        ];
      }
      return prev;
    });
  }, [activeLanguage]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const wavRecorderRef = useRef<WavRecorder | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);

  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const scrolledUp = scrollHeight - scrollTop - clientHeight > 75;
    setIsUserScrolledUp(scrolledUp);
  };

  // Smart auto-scroll to latest message, voice transcription or state change
  useEffect(() => {
    if (!isUserScrolledUp) {
      scrollToBottom('smooth');
    }
  }, [messages, isProcessing, isLiveMode, liveState, livePartialTranscript]);

  // Fetch assistant health and AI provider status whenever modal is opened
  useEffect(() => {
    if (isOpen) {
      fetchAssistantHealth()
        .then((data: any) => {
          if (data?.ai_provider) {
            setAiProvider(data.ai_provider.toLowerCase());
          }
        })
        .catch((err) => console.log('Assistant health fetch error:', err));

      fetchEvonStatus()
        .then((data) => setEvonStatus(data))
        .catch((err) => console.log('Evon status fetch error:', err));
    }
  }, [isOpen]);

  // Clean up audio on unmount
  useEffect(() => {
    return () => {
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current = null;
      }
    };
  }, []);

  const toggleAudioPlayback = (audioUrl: string) => {
    if (isPlayingAudio && activeAudioUrl === audioUrl) {
      audioElementRef.current?.pause();
      setIsPlayingAudio(false);
      return;
    }

    if (audioElementRef.current) {
      audioElementRef.current.pause();
    }

    const audio = new Audio(audioUrl);
    audioElementRef.current = audio;
    setActiveAudioUrl(audioUrl);
    setIsPlayingAudio(true);

    audio.onended = () => {
      setIsPlayingAudio(false);
    };

    audio.onerror = () => {
      setIsPlayingAudio(false);
      alert('Failed to play synthesized audio response.');
    };

    audio.play().catch((err) => {
      console.error('Audio play error:', err);
      setIsPlayingAudio(false);
    });
  };

  const handleSendMessage = async (
    textToSend: string,
    transcriptMeta?: { confidence?: number; request_id?: string; duration?: number; isRealGnani?: boolean }
  ) => {
    if (!textToSend.trim()) return;

    const userMessage: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      transcriptMeta,
    };

    setMessages((prev) => {
      const nextWithUser = [...prev, userMessage];
      persistConversation(nextWithUser, activeLanguage, activeConvId);
      return nextWithUser;
    });
    setInputQuery('');
    setIsUserScrolledUp(false);
    scrollToBottom('smooth');
    setIsProcessing(true);
    setProcessingStage('llm');

    try {
      const response = await sendAssistantMessage({
        message: textToSend,
        languageCode: activeLanguage,
        currentPage: currentPage,
        productId: activeProductId,
        orderId: activeOrderId,
        synthesizeAudio: synthesizeAudio,
        conversationId: activeConvId || currentConversationId || undefined,
      });

      if (response.conversation_id) {
        setCurrentConversationId(response.conversation_id);
      }

      const audioUrl = response.audio_base64
        ? `data:audio/wav;base64,${response.audio_base64}`
        : null;

      const assistantMsg: ChatMessage = {
        id: `asst_${Date.now()}`,
        sender: 'assistant',
        text: response.reply_text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: response.intent,
        intentConfidence: response.intent_confidence,
        actionProposal: response.action_pending_confirmation,
        recommendedProducts: response.products,
        orderCard: response.order,
        audioUrl: audioUrl,
        llmProvider: response.llm_provider,
      };

      setMessages((prev) => {
        const nextWithAssistant = [...prev, assistantMsg];
        persistConversation(nextWithAssistant, activeLanguage, response.conversation_id || activeConvId);
        return nextWithAssistant;
      });

      // If audio synthesized, play automatically if user had toggle enabled
      if (audioUrl && synthesizeAudio) {
        toggleAudioPlayback(audioUrl);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          text: `Error contacting Indic reasoning assistant: ${err.message || 'Unknown network error'}. Please try again.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsProcessing(false);
      setProcessingStage('idle');
    }
  };

  const handleConfirmAction = async (proposal: AssistantActionProposal, confirmed: boolean) => {
    setIsProcessing(true);
    setProcessingStage('llm');

    try {
      const result = await confirmAssistantAction({
        conversationId: currentConversationId || `conv_${Date.now()}`,
        action: proposal.action,
        targetId: proposal.target_id,
        confirmed,
        confirmationToken: proposal.confirmation_token || proposal.details?.confirmation_token,
      });

      const confMsg: ChatMessage = {
        id: `asst_conf_${Date.now()}`,
        sender: 'assistant',
        text: result.message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => {
        const next = [...prev, confMsg];
        persistConversation(next, activeLanguage, activeConvId);
        return next;
      });

      if (confirmed && onOrderUpdated) {
        onOrderUpdated();
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_conf_${Date.now()}`,
          sender: 'assistant',
          text: `Action execution error: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsProcessing(false);
      setProcessingStage('idle');
    }
  };

  // Audio Recording with real PCM 16kHz WAV Recorder
  const startRecording = async () => {
    try {
      const recorder = new WavRecorder();
      await recorder.start();
      wavRecorderRef.current = recorder;
      setIsRecording(true);
      setRecordingSeconds(0);

      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      alert(`Microphone access error: ${err.message || 'Unable to open audio device'}`);
    }
  };

  const cancelRecording = async () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (wavRecorderRef.current) {
      await wavRecorderRef.current.cancel();
      wavRecorderRef.current = null;
    }
    setIsRecording(false);
    setRecordingSeconds(0);
  };

  const stopRecording = async () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (!wavRecorderRef.current) return;

    setIsRecording(false);
    setIsProcessing(true);
    setProcessingStage('stt');

    try {
      const wavBlob = await wavRecorderRef.current.stop();
      wavRecorderRef.current = null;

      // Send to server for Gnani Prisma STT
      const sttRes = await transcribeWithGnani(wavBlob, 'speech_recording.wav', activeLanguage);

      if (sttRes.success && sttRes.transcript.trim()) {
        await handleSendMessage(sttRes.transcript, {
          confidence: sttRes.confidence,
          request_id: sttRes.request_id,
          duration: sttRes.duration,
          isRealGnani: true,
        });
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `empty_trans_${Date.now()}`,
            sender: 'assistant',
            text: 'I could not detect any speech in the recording. Please try speaking clearly or type your question below.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ]);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_gnani_${Date.now()}`,
          sender: 'assistant',
          text: `Gnani Prisma STT error: ${err.message}. You can continue typing your question below.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsProcessing(false);
      setProcessingStage('idle');
    }
  };

  // Audio File Upload Fallback
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    setProcessingStage('stt');
    try {
      const sttRes = await transcribeWithGnani(file, file.name, activeLanguage);
      if (sttRes.success && sttRes.transcript.trim()) {
        await handleSendMessage(sttRes.transcript, {
          confidence: sttRes.confidence,
          request_id: sttRes.request_id,
          duration: sttRes.duration,
          isRealGnani: true,
        });
      } else {
        alert('Gnani transcription returned empty transcript.');
      }
    } catch (err: any) {
      alert(`Audio file transcription failed: ${err.message}`);
    } finally {
      setIsProcessing(false);
      setProcessingStage('idle');
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop Scrim to isolate assistant, prevent accidental page clicks, and close on backdrop tap */}
      <div
        className="fixed inset-0 z-50 bg-black/45 dark:bg-black/70 backdrop-blur-sm transition-opacity animate-in fade-in duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Main Assistant Container */}
      <div className="fixed inset-x-0 bottom-0 sm:inset-x-auto sm:bottom-6 sm:right-6 z-50 w-full sm:w-[450px] sm:max-w-[460px] h-[88vh] sm:h-[660px] max-h-[92vh] sm:max-h-[85vh] bg-white/95 dark:bg-[#0c0a09]/95 border-t sm:border border-amber-300/40 dark:border-stone-800 rounded-t-3xl sm:rounded-3xl shadow-2xl shadow-orange-950/25 dark:shadow-black/80 flex flex-col overflow-hidden backdrop-blur-2xl animate-in fade-in slide-in-from-bottom duration-300">
        {/* Mobile Top Drag Indicator */}
        <div className="sm:hidden w-12 h-1 rounded-full bg-stone-300 dark:bg-stone-700 mx-auto my-2 shrink-0" />

        {/* ChatGPT-style Conversation History Slide-Over Drawer */}
        {isHistoryOpen && (
          <div className="absolute inset-0 z-40 bg-white/95 dark:bg-[#0c0a09]/95 backdrop-blur-md flex flex-col animate-in fade-in slide-in-from-left duration-200">
            {/* Drawer Header */}
            <div className="p-3 sm:p-3.5 border-b border-amber-200/70 dark:border-stone-800 flex items-center justify-between bg-amber-50/60 dark:bg-[#14100c]/60">
              <div className="flex items-center gap-2">
                <div className="h-7 w-7 rounded-lg bg-orange-500/15 flex items-center justify-center text-orange-600 dark:text-orange-400">
                  <MessageSquare className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="font-bold text-xs sm:text-sm text-stone-900 dark:text-stone-100">Saved Conversations</h4>
                  <p className="text-[10px] text-stone-500 dark:text-stone-400">{conversations.length} chats stored</p>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={startNewChat}
                  className="px-2.5 py-1 rounded-lg bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white text-xs font-bold flex items-center gap-1 shadow-sm shadow-orange-500/25 transition-all cursor-pointer"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>New Chat</span>
                </button>
                <button
                  onClick={() => setIsHistoryOpen(false)}
                  className="p-1.5 rounded-lg text-stone-400 hover:text-stone-900 dark:hover:text-white hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors cursor-pointer"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Search History Filter */}
            <div className="p-2.5 border-b border-amber-200/50 dark:border-stone-800/80">
              <div className="relative flex items-center">
                <Search className="absolute left-3 h-3.5 w-3.5 text-stone-400 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search conversations..."
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                  className="w-full bg-stone-100 dark:bg-[#14100c] text-xs pl-8 pr-3 py-1.5 rounded-xl border border-stone-200 dark:border-stone-800 outline-none focus:border-orange-500 text-stone-900 dark:text-stone-100"
                />
              </div>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto p-2 space-y-1.5 chat-scrollbar">
              {filteredConversations.length === 0 ? (
                <div className="p-8 text-center text-stone-400 dark:text-stone-500 space-y-2">
                  <MessageSquare className="h-8 w-8 mx-auto opacity-40 text-orange-500" />
                  <p className="text-xs font-medium">
                    {historySearch ? 'No matching conversations.' : 'No conversations recorded yet.'}
                  </p>
                  <p className="text-[11px] text-stone-400">
                    Every voice query and chat is stored here like ChatGPT.
                  </p>
                </div>
              ) : (
                filteredConversations.map((conv) => {
                  const isActive = conv.id === activeConvId;
                  const lastMsg = conv.messages[conv.messages.length - 1];
                  return (
                    <div
                      key={conv.id}
                      onClick={() => loadConversation(conv)}
                      className={`group relative p-2.5 rounded-xl transition-all cursor-pointer flex items-start gap-2.5 ${
                        isActive
                          ? 'bg-orange-500/10 dark:bg-orange-500/15 border border-orange-500/40 text-stone-900 dark:text-stone-100 shadow-sm'
                          : 'hover:bg-amber-50/70 dark:hover:bg-[#14100c] border border-transparent hover:border-amber-200/60 dark:hover:border-stone-800 text-stone-700 dark:text-stone-300'
                      }`}
                    >
                      <MessageSquare className={`h-4 w-4 mt-0.5 shrink-0 ${isActive ? 'text-orange-600 dark:text-amber-400' : 'text-stone-400 group-hover:text-orange-500'}`} />
                      <div className="flex-1 min-w-0 pr-6">
                        <div className="flex items-center justify-between gap-1 mb-0.5">
                          <h5 className="text-xs font-semibold truncate leading-tight">
                            {conv.title || 'Conversation'}
                          </h5>
                        </div>
                        {lastMsg && (
                          <p className="text-[11px] text-stone-500 dark:text-stone-400 truncate leading-snug">
                            {lastMsg.text}
                          </p>
                        )}
                        <div className="flex items-center gap-2 mt-1 text-[10px] text-stone-400">
                          <span>{formatConversationDate(conv.updatedAt || conv.createdAt)}</span>
                          <span>•</span>
                          <span>{conv.messages.filter((m) => m.sender === 'user').length} queries</span>
                        </div>
                      </div>

                      {/* Delete chat button on hover */}
                      <button
                        onClick={(e) => handleDeleteConversation(conv.id, e)}
                        className="absolute right-2 top-2 p-1 rounded-md text-stone-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 opacity-70 group-hover:opacity-100 transition-all cursor-pointer"
                        title="Delete conversation"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  );
                })
              )}
            </div>

            {/* Drawer Footer */}
            {conversations.length > 0 && (
              <div className="p-2.5 border-t border-amber-200/70 dark:border-stone-800 flex items-center justify-between text-xs bg-amber-50/30 dark:bg-[#14100c]/30">
                <span className="text-stone-400 text-[11px]">{conversations.length} saved chats</span>
                <button
                  onClick={clearAllConversations}
                  className="text-stone-400 hover:text-red-500 text-[11px] flex items-center gap-1 transition-colors cursor-pointer"
                >
                  <Trash2 className="h-3 w-3" />
                  <span>Clear All</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Clean, Non-wrapping Header */}
        <div className="px-3.5 sm:px-4 py-2.5 sm:py-3 bg-gradient-to-r from-amber-50/90 via-white/90 to-orange-50/90 dark:from-[#14100c] dark:via-[#0c0a09] dark:to-[#1a120c] border-b border-amber-200/70 dark:border-stone-800 flex items-center justify-between shrink-0 gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="relative h-9 w-9 rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center text-white shadow-md shadow-orange-500/25 border border-amber-300/40 shrink-0">
              <Mic className="h-4 w-4" />
              <span className="absolute -bottom-0.5 -right-0.5 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 border border-white dark:border-[#0c0a09] bg-emerald-500" />
              </span>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <h3 className="font-display text-sm sm:text-base font-bold text-stone-900 dark:text-white truncate">VoiceIQ Assistant</h3>
              </div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
                </span>
                <span className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                  Online
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 sm:gap-1.5 shrink-0">
            {/* Active Live Voice Badge if in call */}
            {isLiveMode && (
              <button
                onClick={stopLiveCall}
                className="px-2 py-1 rounded-full bg-emerald-500/15 hover:bg-red-500/15 text-emerald-700 dark:text-emerald-300 hover:text-red-600 border border-emerald-500/30 text-[10px] font-bold flex items-center gap-1 transition-colors cursor-pointer"
                title="Click to End Voice Call"
              >
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
                </span>
                <span className="hidden xs:inline">Live</span>
                <span className="text-red-500 font-bold ml-0.5">✕</span>
              </button>
            )}

            {/* ChatGPT-style Conversation History Toggle */}
            <button
              onClick={() => setIsHistoryOpen(!isHistoryOpen)}
              className={`h-8 px-2 rounded-lg border text-[11px] font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                isHistoryOpen
                  ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white border-orange-400 shadow-sm'
                  : 'bg-stone-100 dark:bg-[#14100c] text-stone-600 dark:text-stone-300 border-amber-200/80 dark:border-stone-800 hover:text-stone-900 dark:hover:text-white'
              }`}
              title="Conversation History (ChatGPT style)"
            >
              <History className="h-3.5 w-3.5 text-orange-500" />
              <span className="hidden sm:inline">Chats</span>
              {conversations.length > 0 && (
                <span className={`text-[10px] px-1 rounded-full font-mono ${isHistoryOpen ? 'bg-white/30 text-white' : 'bg-orange-500/15 text-orange-700 dark:text-orange-400'}`}>
                  {conversations.length}
                </span>
              )}
            </button>

            {/* New Chat Button */}
            <button
              onClick={startNewChat}
              className="h-8 w-8 sm:w-auto sm:px-2 rounded-lg border border-amber-200/80 dark:border-stone-800 bg-stone-100 dark:bg-[#14100c] text-stone-700 dark:text-stone-300 hover:bg-orange-500 hover:text-white hover:border-orange-500 text-[11px] font-semibold transition-all flex items-center justify-center gap-1 cursor-pointer"
              title="Start New Conversation"
            >
              <Plus className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">New</span>
            </button>

            {/* TTS Spoken Audio Toggle */}
            <button
              onClick={() => setSynthesizeAudio(!synthesizeAudio)}
              className={`h-8 w-8 rounded-lg border text-xs flex items-center justify-center transition-colors cursor-pointer ${
                synthesizeAudio
                  ? 'bg-orange-500 text-white border-orange-400 shadow-sm shadow-orange-500/30'
                  : 'bg-stone-100 dark:bg-[#14100c] text-stone-600 dark:text-stone-400 border-amber-200/80 dark:border-stone-800 hover:text-stone-900 dark:hover:text-white'
              }`}
              title={synthesizeAudio ? 'Spoken Voice Output ON' : 'Spoken Voice Output OFF'}
            >
              {synthesizeAudio ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
            </button>

            {/* Close */}
            <button
              onClick={onClose}
              className="h-8 w-8 rounded-lg text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white hover:bg-amber-100/60 dark:hover:bg-[#14100c] flex items-center justify-center transition-colors cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Language Selector Bar */}
        <div className="bg-amber-50/50 dark:bg-[#080706] px-3.5 sm:px-4 py-1.5 sm:py-2 border-b border-amber-200/60 dark:border-stone-800 flex items-center justify-between text-xs shrink-0">
          <span className="typo-label text-stone-500 dark:text-stone-400">Speech Language:</span>
          <select
            value={activeLanguage}
            onChange={(e) => {
              const next = e.target.value;
              setInternalLanguage(next);
              try {
                localStorage.setItem('voiceiq_preferred_language', next);
              } catch {}
              if (onSelectLanguage) {
                onSelectLanguage(next);
              }
              if (realtimeConvRef.current) {
                realtimeConvRef.current.setLanguage(next);
              }
            }}
            className="typo-nav bg-white dark:bg-[#14100c] text-stone-800 dark:text-stone-200 px-2 sm:px-2.5 py-1 rounded-lg border border-amber-200/80 dark:border-stone-800 outline-none cursor-pointer hover:border-orange-500/50 focus:border-orange-500 font-medium text-xs"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.native} ({lang.name})
              </option>
            ))}
          </select>
        </div>

        {/* Chat Messages Feed with Atmospheric Background & Scroll Container */}
        <div
          ref={chatContainerRef}
          onScroll={handleScroll}
          className="relative flex-1 p-3.5 sm:p-4 overflow-y-auto space-y-3.5 bg-[#faf8f5] dark:bg-[#080706] chat-scrollbar overscroll-contain transition-colors"
        >
          {/* Ambient atmospheric aura lights */}
          <div className="absolute -top-12 -right-12 w-64 h-64 bg-orange-500/10 dark:bg-orange-500/15 rounded-full blur-3xl pointer-events-none animate-aura-slow" />
          <div className="absolute -bottom-16 -left-16 w-60 h-60 bg-amber-400/10 dark:bg-amber-400/12 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute inset-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] dark:bg-[radial-gradient(#262626_1px,transparent_1px)] [background-size:16px_16px] opacity-40 pointer-events-none" />

          {/* Dynamic voice state atmospheric glow when in Live Call */}
          {isLiveMode && (
            <div
              className={`absolute inset-0 pointer-events-none transition-all duration-700 ${
                liveState === 'SPEAKING'
                  ? 'bg-gradient-to-b from-emerald-500/10 via-transparent to-transparent'
                  : liveState === 'THINKING'
                  ? 'bg-gradient-to-b from-amber-500/12 via-transparent to-transparent'
                  : 'bg-gradient-to-b from-orange-500/10 via-transparent to-transparent'
              }`}
            />
          )}

          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                className={`relative z-10 flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1`}
              >
                <div
                  className={`max-w-[85%] sm:max-w-[82%] p-3.5 rounded-2xl typo-body leading-relaxed ${
                    isUser
                      ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-br-none shadow-md shadow-orange-500/20'
                      : 'bg-white dark:bg-[#14100c] border border-amber-200/70 dark:border-stone-800 text-stone-900 dark:text-stone-100 rounded-bl-none shadow-sm'
                  }`}
                >
                  {/* Real Gnani STT Badge if applicable */}
                  {isUser && msg.transcriptMeta?.isRealGnani && (
                    <div className="mb-1.5 pb-1 border-b border-amber-300/30 flex items-center gap-1.5 typo-label text-amber-100">
                      <Sparkles className="h-3 w-3 text-yellow-300" />
                      <span>
                        Gnani Prisma STT • Confidence:{' '}
                        {msg.transcriptMeta.confidence !== undefined
                          ? `${(msg.transcriptMeta.confidence * 100).toFixed(0)}%`
                          : '95%'}
                      </span>
                    </div>
                  )}

                  {/* Model Provider & Intent Badge */}
                  {!isUser && (msg.llmProvider || msg.intent) && (
                    <div className="mb-2 pb-1.5 border-b border-amber-100 dark:border-stone-800 flex flex-wrap items-center justify-between gap-1 typo-label">
                      <span className="flex items-center gap-1 text-orange-600 dark:text-amber-400 font-semibold">
                        <Sparkles className="h-3 w-3 text-amber-500" />
                        <span>{msg.llmProvider || (aiProvider === 'gemini' ? 'Gemini 2.5 Flash' : 'Qwen 4B (Ollama)')}</span>
                      </span>
                      {msg.intent && (
                        <span className="px-1.5 py-0.5 rounded bg-amber-50 dark:bg-[#1c140c] text-stone-700 dark:text-stone-300 border border-amber-200/60 dark:border-stone-700">
                          intent: <span className="text-orange-600 dark:text-amber-400 font-bold">{msg.intent}</span>
                          {msg.intentConfidence !== undefined && msg.intentConfidence !== null
                            ? ` • ${(msg.intentConfidence * 100).toFixed(0)}%`
                            : ''}
                        </span>
                      )}
                    </div>
                  )}

                  <p className="whitespace-pre-line">{msg.text}</p>

                  {/* Spoken audio player button */}
                  {msg.audioUrl && (
                    <div className="mt-2.5 pt-2 border-t border-amber-100 dark:border-stone-800 flex items-center gap-2">
                      <button
                        onClick={() => toggleAudioPlayback(msg.audioUrl!)}
                        className="typo-button px-2.5 py-1 rounded-lg bg-orange-500/15 hover:bg-orange-500/25 text-orange-700 dark:text-orange-300 border border-orange-500/30 flex items-center gap-1.5 transition-colors cursor-pointer"
                      >
                        {isPlayingAudio && activeAudioUrl === msg.audioUrl ? (
                          <>
                            <Pause className="h-3 w-3" />
                            <span>Pause Audio</span>
                          </>
                        ) : (
                          <>
                            <Play className="h-3 w-3" />
                            <span>Listen (Gnani Timbre TTS)</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>

                {/* Embedded Consequential Action Card */}
                {msg.actionProposal && (
                  <div className="relative z-10 w-full max-w-[90%] sm:max-w-[85%] p-3.5 rounded-2xl bg-amber-500/10 dark:bg-amber-950/20 border border-amber-500/40 space-y-2.5 typo-body text-stone-900 dark:text-amber-200 shadow-sm">
                    <div className="flex items-center gap-2 font-bold text-orange-600 dark:text-amber-400 typo-label">
                      <AlertTriangle className="h-4 w-4" />
                      <span>Confirmation Required</span>
                    </div>
                    <p>{msg.actionProposal.confirmation_prompt}</p>

                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={() => handleConfirmAction(msg.actionProposal!, true)}
                        className="typo-button px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold shadow-sm transition-all cursor-pointer"
                      >
                        Yes, Confirm
                      </button>
                      <button
                        onClick={() => handleConfirmAction(msg.actionProposal!, false)}
                        className="typo-button px-3.5 py-1.5 rounded-xl bg-stone-200 dark:bg-stone-800 text-stone-800 dark:text-stone-300 hover:text-stone-950 dark:hover:text-white transition-all cursor-pointer"
                      >
                        No, Keep Order
                      </button>
                    </div>
                  </div>
                )}

                {/* Embedded Product Recommendations */}
                {msg.recommendedProducts && msg.recommendedProducts.length > 0 && (
                  <div className="relative z-10 w-full max-w-[92%] sm:max-w-[88%] space-y-2 pt-1">
                    {msg.recommendedProducts.map((p) => (
                      <div
                        key={p.id}
                        className="p-2.5 rounded-xl bg-white dark:bg-[#16120e] border border-amber-200/80 dark:border-stone-800 flex items-center gap-3 shadow-sm hover:border-orange-500/40 transition-colors"
                      >
                        <img
                          src={p.image_url}
                          alt={p.title}
                          className="h-12 w-12 rounded-lg object-cover bg-amber-50 dark:bg-stone-900 shrink-0 border border-amber-100 dark:border-stone-800"
                        />
                        <div className="flex-1 min-w-0">
                          <h5 className="typo-product-name text-stone-900 dark:text-white truncate">{p.title}</h5>
                          <span className="typo-product-price text-orange-600 dark:text-amber-400 tabular-nums">
                            ₹{p.price.toLocaleString('en-IN')}
                          </span>
                        </div>
                        <button
                          onClick={() => {
                            if (onAddToCart) onAddToCart(p);
                          }}
                          className="typo-button px-2.5 py-1 rounded-lg bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white shrink-0 shadow-sm shadow-orange-500/20 transition-all active:scale-95 cursor-pointer font-bold"
                        >
                          Add
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Embedded Order Tracking Card */}
                {msg.orderCard && (
                  <div className="relative z-10 w-full max-w-[90%] sm:max-w-[85%] p-3.5 rounded-2xl bg-white dark:bg-[#16120e] border border-amber-200/80 dark:border-stone-800 space-y-2 typo-body shadow-md shadow-orange-950/10">
                    <div className="flex justify-between items-center">
                      <span className="font-display font-bold text-stone-900 dark:text-white">Order #{msg.orderCard.id}</span>
                      <span className="typo-label px-2 py-0.5 rounded bg-amber-500/20 text-orange-800 dark:text-amber-300 border border-amber-500/30">
                        {msg.orderCard.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-stone-600 dark:text-stone-400">
                      Carrier: <strong className="text-stone-900 dark:text-white font-medium">{msg.orderCard.carrier}</strong> ({msg.orderCard.tracking_number})
                    </p>
                    <div className="text-stone-700 dark:text-stone-300 font-bold">
                      Total: <span className="typo-product-price text-orange-600 dark:text-amber-400 tabular-nums">₹{msg.orderCard.total_amount.toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                )}

                <span className="typo-label text-[10px] text-stone-400 dark:text-stone-500 px-1">{msg.timestamp}</span>
              </div>
            );
          })}

          {isProcessing && (
            <div className="relative z-10 overflow-hidden flex items-center justify-center px-4 py-3 rounded-2xl bg-gradient-to-r from-orange-500/10 via-amber-500/10 to-orange-500/5 dark:from-[#1c140c] dark:to-[#17110c] border border-orange-500/25 dark:border-amber-500/20 w-fit shadow-md shadow-orange-500/5">
              {/* Ambient Background Aura Glow */}
              <div className="absolute -top-6 -left-6 w-20 h-20 bg-orange-500/20 rounded-full blur-xl animate-aura-slow pointer-events-none" />
              <div className="absolute -bottom-6 -right-6 w-20 h-20 bg-amber-400/20 rounded-full blur-xl animate-pulse pointer-events-none" />

              <div className="relative z-10 flex items-center gap-2.5">
                {processingStage === 'stt' ? (
                  /* STT: Animated Audio Waveform Bars */
                  <div className="flex items-center gap-1 h-6 px-1">
                    <span className="w-1 bg-orange-500 rounded-full animate-bounce h-2.5" style={{ animationDelay: '0.05s' }} />
                    <span className="w-1 bg-amber-500 rounded-full animate-bounce h-4.5" style={{ animationDelay: '0.15s' }} />
                    <span className="w-1 bg-orange-600 rounded-full animate-bounce h-6" style={{ animationDelay: '0.25s' }} />
                    <span className="w-1 bg-amber-400 rounded-full animate-bounce h-4" style={{ animationDelay: '0.35s' }} />
                    <span className="w-1 bg-orange-500 rounded-full animate-bounce h-2" style={{ animationDelay: '0.12s' }} />
                  </div>
                ) : (
                  /* LLM / Intent: Rotating Neural Orb & Pulsing Dots */
                  <div className="flex items-center gap-2">
                    <div className="relative w-6 h-6 flex items-center justify-center shrink-0">
                      <div className="absolute inset-0 rounded-full border-2 border-orange-500/30 border-t-orange-500 animate-spin" style={{ animationDuration: '1.5s' }} />
                      <div className="absolute inset-1 rounded-full border border-amber-400/40 border-b-amber-400 animate-spin" style={{ animationDuration: '2.5s', animationDirection: 'reverse' }} />
                      <div className="w-2.5 h-2.5 rounded-full bg-gradient-to-tr from-orange-500 to-amber-400 animate-pulse shadow-sm shadow-orange-500/50" />
                    </div>
                    <div className="flex items-center gap-1.5 ml-0.5">
                      <span className="w-2 h-2 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Real-Time Continuous Voice Assistant Animation in Active Chat Feed */}
          {isLiveMode && (
            <div className="relative z-10 my-2 p-3.5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-yellow-500/10 dark:from-[#1c120a] dark:via-[#24160c] dark:to-[#1c120a] border border-amber-400/40 dark:border-amber-500/30 shadow-md shadow-orange-500/10 transition-all duration-300 animate-in fade-in">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  {/* Pulsing Glowing AI Brain / Voice Orb */}
                  <div className="relative flex items-center justify-center shrink-0">
                    <span className={`absolute inline-flex h-9 w-9 rounded-full opacity-60 animate-ping ${
                      liveState === 'SPEAKING' ? 'bg-emerald-400' : liveState === 'THINKING' ? 'bg-amber-400' : 'bg-orange-400'
                    }`} />
                    <div className={`relative h-9 w-9 rounded-full flex items-center justify-center text-white shadow-md ${
                      liveState === 'SPEAKING'
                        ? 'bg-gradient-to-tr from-emerald-500 to-teal-500 shadow-emerald-500/40'
                        : liveState === 'THINKING'
                        ? 'bg-gradient-to-tr from-amber-500 to-yellow-500 shadow-yellow-500/40'
                        : 'bg-gradient-to-tr from-orange-500 via-amber-500 to-yellow-400 shadow-orange-500/40 animate-pulse'
                    }`}>
                      {liveState === 'SPEAKING' ? (
                        <Volume2 className="h-4 w-4" />
                      ) : liveState === 'THINKING' ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Mic className="h-4 w-4" />
                      )}
                    </div>
                  </div>

                  {/* State Label & Live Waveform Animation */}
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-xs sm:text-sm text-stone-900 dark:text-stone-100 flex items-center gap-1.5">
                        {liveState === 'SPEAKING' ? (
                          <span className="text-emerald-700 dark:text-emerald-400">VoiceIQ Speaking...</span>
                        ) : liveState === 'THINKING' ? (
                          <span className="text-amber-700 dark:text-amber-400">Thinking (Gemini 2.5 Flash)...</span>
                        ) : liveState === 'TRANSCRIBING' ? (
                          <span className="text-orange-700 dark:text-orange-400">Transcribing (Gnani Prisma)...</span>
                        ) : (
                          <span className="text-orange-700 dark:text-orange-400">Listening to your voice...</span>
                        )}
                      </h4>
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold bg-orange-500/15 text-orange-700 dark:text-orange-400 border border-orange-500/30">
                        Live Call
                      </span>
                    </div>

                    {/* Dynamic soundwave animation */}
                    <div className="flex items-center gap-1 mt-1.5 h-5">
                      {[45, 80, 100, 65, 95, 50, 85, 60, 90, 55, 75, 40].map((baseHeight, i) => {
                        const dynamicScale = liveState === 'SPEAKING'
                          ? Math.max(4, (Math.sin(Date.now() / 150 + i) + 1.2) * 8)
                          : liveState === 'LISTENING'
                          ? Math.max(4, Math.min(20, (liveVolume * 140 * (baseHeight / 100)) + 4))
                          : 4;
                        return (
                          <span
                            key={i}
                            className={`w-1 rounded-full transition-all duration-75 ${
                              liveState === 'SPEAKING'
                                ? 'bg-gradient-to-t from-emerald-600 to-teal-400'
                                : 'bg-gradient-to-t from-orange-500 via-amber-400 to-yellow-400'
                            }`}
                            style={{ height: `${dynamicScale}px` }}
                          />
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Action Controls: Interrupt or End Call */}
                <div className="flex items-center gap-1.5 shrink-0">
                  {liveState === 'SPEAKING' && (
                    <button
                      onClick={handleBargeIn}
                      className="px-2.5 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500 text-orange-900 dark:text-amber-200 hover:text-white border border-amber-500/40 text-xs font-bold transition-all cursor-pointer flex items-center gap-1"
                      title="Interrupt speaking"
                    >
                      <MicOff className="h-3 w-3" />
                      <span>Interrupt</span>
                    </button>
                  )}
                  <button
                    onClick={stopLiveCall}
                    className="px-2.5 py-1 rounded-lg bg-red-500/15 hover:bg-red-500 text-red-700 dark:text-red-300 hover:text-white border border-red-500/30 text-xs font-bold transition-all cursor-pointer"
                    title="Stop Live Voice Mode"
                  >
                    End Voice
                  </button>
                </div>
              </div>

              {/* Live Partial Speech Transcript Bubble */}
              {livePartialTranscript && (
                <div className="mt-2 pt-2 border-t border-amber-200/50 dark:border-stone-800 text-xs text-stone-700 dark:text-stone-300 flex items-center gap-1.5">
                  <span className="text-[10px] uppercase font-bold text-orange-600 dark:text-amber-400">Heard:</span>
                  <span className="italic font-medium">"{livePartialTranscript}"</span>
                </div>
              )}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Floating Scroll to Latest Button */}
        {isUserScrolledUp && (
          <button
            onClick={() => {
              setIsUserScrolledUp(false);
              scrollToBottom('smooth');
            }}
            className="absolute bottom-20 left-1/2 -translate-x-1/2 z-30 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-lg shadow-orange-500/35 text-xs font-bold flex items-center gap-1.5 hover:scale-105 active:scale-95 transition-all cursor-pointer animate-in fade-in"
          >
            <span>Scroll to latest</span>
            <ArrowDown className="h-3.5 w-3.5 animate-bounce" />
          </button>
        )}

        {/* Recording State Overlay with Neural Waveforms */}
        {isRecording && (
          <div className="p-3 bg-gradient-to-r from-orange-500/15 via-amber-500/10 to-orange-500/15 dark:from-[#1c0f06] dark:via-[#221308] dark:to-[#1c0f06] border-t border-orange-500/40 flex items-center justify-between typo-body shrink-0">
            <div className="flex items-center gap-3 text-orange-600 dark:text-orange-400">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-orange-500" />
              </span>
              <span className="font-bold text-stone-900 dark:text-white typo-nav">Listening ({recordingSeconds}s)...</span>

              {/* Live Audio Waveform animation */}
              <div className="hidden sm:flex items-center gap-1 h-5 px-2 bg-orange-500/15 rounded-md border border-orange-500/20">
                <span className="w-0.5 bg-orange-500 rounded-full animate-bounce h-2" style={{ animationDelay: '0.05s' }} />
                <span className="w-0.5 bg-orange-600 rounded-full animate-bounce h-4" style={{ animationDelay: '0.15s' }} />
                <span className="w-0.5 bg-amber-500 rounded-full animate-bounce h-5" style={{ animationDelay: '0.25s' }} />
                <span className="w-0.5 bg-orange-500 rounded-full animate-bounce h-3" style={{ animationDelay: '0.1s' }} />
                <span className="w-0.5 bg-amber-400 rounded-full animate-bounce h-4.5" style={{ animationDelay: '0.3s' }} />
                <span className="w-0.5 bg-orange-600 rounded-full animate-bounce h-2" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={cancelRecording}
                className="typo-button px-2.5 py-1 rounded-lg bg-stone-100 dark:bg-[#14100c] text-stone-700 dark:text-stone-300 border border-amber-200/80 dark:border-stone-800 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={stopRecording}
                className="typo-button px-3 py-1 rounded-lg bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold flex items-center gap-1 shadow-md shadow-orange-500/30 cursor-pointer"
              >
                <MicOff className="h-3.5 w-3.5" />
                <span>Done</span>
              </button>
            </div>
          </div>
        )}

        {/* Quick Suggestions when conversation is fresh */}
        {messages.length <= 1 && !isRecording && (
          <div className="px-3.5 py-2 bg-amber-50/50 dark:bg-[#0c0a09] border-t border-amber-200/60 dark:border-stone-800 flex items-center gap-1.5 overflow-x-auto shrink-0 chat-scrollbar">
            {(QUICK_SUGGESTIONS[activeLanguage] || QUICK_SUGGESTIONS['en-IN']).map((chip) => (
              <button
                key={chip}
                onClick={() => handleSendMessage(chip)}
                disabled={isProcessing}
                className="typo-button text-[11px] whitespace-nowrap px-2.5 py-1 rounded-full bg-white dark:bg-[#14100c] hover:bg-orange-50 dark:hover:bg-orange-950/30 border border-amber-200/80 dark:border-stone-800 hover:border-orange-500/50 text-stone-700 dark:text-stone-300 hover:text-orange-600 dark:hover:text-amber-300 transition-all cursor-pointer font-medium"
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="p-2.5 sm:p-3 bg-white dark:bg-[#0c0a09] border-t border-amber-200/80 dark:border-stone-800 flex items-center gap-1.5 sm:gap-2 shrink-0">
          {/* Push to talk button */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
            className={`h-9 w-9 sm:h-10 sm:w-10 rounded-xl transition-all shadow-md cursor-pointer shrink-0 flex items-center justify-center ${
              isRecording
                ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white animate-pulse shadow-orange-600/50'
                : 'bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white hover:scale-105 active:scale-95 shadow-orange-500/25'
            }`}
            title={isRecording ? 'Stop Recording' : 'Hold or Click to Speak'}
          >
            <Mic className="h-4 w-4" />
          </button>

          {/* Real-Time Continuous Voice Assistant Button (Yellow Brain Icon) */}
          <button
            onClick={isLiveMode ? stopLiveCall : startLiveCall}
            className={`h-9 w-9 sm:h-10 sm:w-10 rounded-xl border transition-all cursor-pointer flex items-center justify-center shrink-0 relative ${
              isLiveMode
                ? 'bg-gradient-to-tr from-orange-500 via-amber-500 to-yellow-400 text-stone-950 border-amber-300 shadow-lg shadow-orange-500/35 animate-pulse'
                : 'bg-[#181512] hover:bg-[#231e19] text-amber-400 hover:text-amber-300 border border-amber-500/30 shadow-sm'
            }`}
            title={isLiveMode ? 'End Real-Time Voice Assistant' : 'Start Real-Time Voice Assistant (Hands-Free)'}
          >
            {isLiveMode ? (
              <span className="material-symbols-outlined text-[18px] sm:text-[20px] font-bold text-stone-950">graphic_eq</span>
            ) : (
              <span className="material-symbols-outlined text-[18px] sm:text-[20px] font-bold text-amber-400">neurology</span>
            )}
            {isLiveMode && (
              <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500 border border-white" />
              </span>
            )}
          </button>

          {/* Audio File Upload Button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isProcessing || isRecording}
            className="h-9 w-9 sm:h-10 sm:w-10 rounded-xl bg-stone-100 dark:bg-[#14100c] hover:bg-amber-50 dark:hover:bg-[#1c140c] text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white border border-amber-200/80 dark:border-stone-800 transition-colors cursor-pointer shrink-0 flex items-center justify-center"
            title="Upload audio recording to transcribe"
          >
            <Upload className="h-4 w-4" />
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept="audio/*"
            className="hidden"
          />

          {/* Text Input */}
          <input
            type="text"
            placeholder={INPUT_PLACEHOLDERS[activeLanguage] || INPUT_PLACEHOLDERS['en-IN']}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(inputQuery)}
            disabled={isRecording || isProcessing}
            className="typo-nav flex-1 min-w-0 bg-stone-50 dark:bg-[#14100c] border border-amber-200/80 dark:border-stone-800 rounded-xl px-3 py-2 text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-500 outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500/30 text-xs sm:text-sm"
          />

          {/* Send */}
          <button
            onClick={() => handleSendMessage(inputQuery)}
            disabled={!inputQuery.trim() || isProcessing}
            className="h-9 w-9 sm:h-10 sm:w-10 rounded-xl bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-400 hover:from-orange-600 hover:to-amber-500 disabled:opacity-40 text-white dark:text-stone-950 font-bold transition-all shadow-md shadow-orange-500/25 cursor-pointer shrink-0 flex items-center justify-center"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </>
  );
};
