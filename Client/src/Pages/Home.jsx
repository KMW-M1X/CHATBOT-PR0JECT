import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import ChatBar from '../Components/ChatBar'; 

function Home() {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState([]); 
  const [isLoading, setIsLoading] = useState(false); 
  
  // Auto scroll to bottom
  const messagesEndRef = useRef(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!inputText.trim()) return;

    const userMsg = { role: 'user', content: inputText };
    const currentMessages = [...messages, userMsg];
    setMessages(currentMessages);
    setInputText(''); 
    setIsLoading(true); 

    try {
      const token = localStorage.getItem('token') || '';
      const response = await axios.post(
        'http://localhost:5000/api/chat', 
        {
          message: userMsg.content,
          chat_history: currentMessages 
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      const aiReply = response.data.reply;
      setMessages([...currentMessages, { role: 'assistant', content: aiReply }]);

    } catch (error) {
      console.error("AI Error:", error);
      setMessages([...currentMessages, { role: 'assistant', content: 'ขออภัยครับ ระบบขัดข้องชั่วคราว ลองใหม่อีกครั้งนะครับ' }]);
    } finally {
      setIsLoading(false); 
    }
  };

  const isChatActive = messages.length > 0;

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#131314] text-gray-800 dark:text-[#e3e3e3]  transition-colors duration-300 relative overflow-hidden">
      
      {/* Inline styles for animation */}
      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .msg-enter {
          animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>

      <div className="flex-1 overflow-y-auto px-4 pb-40 z-0 scrollbar-none">
        {isChatActive && (
          <div className="max-w-3xl mx-auto py-8 space-y-6">
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`flex msg-enter ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div 
                  className={`text-[15px] leading-relaxed transition-all duration-300 ${
                    msg.role === 'user' 
                      ? 'px-5 py-3.5 max-w-[80%] bg-blue-600 text-white rounded-[24px]  shadow-sm' 
                      : 'max-w-[95%] py-1 text-gray-800 dark:text-gray-200'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    // Wrap ReactMarkdown in a div to apply classes
                    <div className="space-y-4">
                      <ReactMarkdown 
                        components={{
                          strong: ({node, ...props}) => <strong className="font-semibold text-blue-700 dark:text-blue-400" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-6 space-y-2 marker:text-blue-500/70" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal pl-6 space-y-2 marker:text-blue-500/70 font-medium" {...props} />,
                          li: ({node, ...props}) => <li className="pl-1 text-gray-700 dark:text-gray-300 font-normal" {...props} />,
                          p: ({node, ...props}) => <p className="mb-2 last:mb-0 leading-loose" {...props} />
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {/* Typing Indicator */}
            {isLoading && (
              <div className="flex justify-start msg-enter">
                 <div className="py-3 px-2 flex gap-1.5 items-center h-8">
                    <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                 </div>
              </div>
            )}
            
            {/* Scroll target */}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <ChatBar 
        inputText={inputText}
        setInputText={setInputText}
        handleSend={handleSend}
        isChatActive={isChatActive}
      />

    </div>
  );
}

export default Home;