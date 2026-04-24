import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ChatBar from '../Components/ChatBar';

function Home() {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Auto scroll to bottom
  const messagesEndRef = useRef(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

      // ดึงข้อมูล User จาก LocalStorage 
      let storedUser = {};
      try {
        const userString = localStorage.getItem('user');
        if (userString) {
          storedUser = JSON.parse(userString);
        }
      } catch (e) {
        console.error('Parse ข้อมูล User พังว่ะ:', e);
      }

      // เตรียมข้อมูล User ส่งให้ API
      const currentUser = {
        name: storedUser.name || 'ผู้ใช้งาน',
        weight: Number(storedUser.weight) || 0,
        height: Number(storedUser.height) || 0,
        age: Number(storedUser.age) || 0,
        gender: storedUser.gender || 'none',
        dietaryPreference: storedUser.dietaryPreference || 'none',
        foodAllergies: Array.isArray(storedUser.foodAllergies) ? storedUser.foodAllergies : [],
      };

      const response = await axios.post(
        'http://localhost:8000/api/chat', // เช็ก Port ด้วยนะจารย์
        {
          message: userMsg.content,
          user: currentUser,
          chat_history: currentMessages,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const aiReply = response.data.reply;
      setMessages([...currentMessages, { role: 'assistant', content: aiReply }]);
    } catch (error) {
      console.error('AI Error:', error);
      setMessages([...currentMessages, { role: 'assistant', content: 'ขออภัยครับ ระบบขัดข้องชั่วคราว ลองใหม่อีกครั้งนะครับ' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const isChatActive = messages.length > 0;

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#131314] text-gray-800 dark:text-[#e3e3e3] transition-colors duration-300 relative overflow-hidden">
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
                className={`flex msg-enter ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`text-[15px] leading-relaxed transition-all duration-300 ${
                    msg.role === 'user'
                      ? 'px-5 py-3.5 max-w-[80%] bg-blue-600 text-white rounded-[24px] shadow-sm'
                      : 'max-w-[95%] py-1 text-gray-800 dark:text-gray-200'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    // 🌟 ส่วนที่อัปเกรด Markdown เต็มรูปแบบ 🌟
                    <div className="space-y-4 w-full overflow-hidden">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          strong: ({ node, ...props }) => <strong className="font-semibold text-blue-700 dark:text-blue-400" {...props} />,
                          em: ({ node, ...props }) => <em className="italic text-gray-800 dark:text-gray-300" {...props} />,
                          ul: ({ node, ...props }) => <ul className="list-disc pl-6 space-y-1 marker:text-blue-500/70 my-3" {...props} />,
                          ol: ({ node, ...props }) => <ol className="list-decimal pl-6 space-y-1 marker:text-blue-500/70 font-medium my-3" {...props} />,
                          li: ({ node, ...props }) => <li className="pl-1 text-gray-700 dark:text-gray-300 font-normal leading-relaxed" {...props} />,
                          p: ({ node, ...props }) => <p className="mb-3 last:mb-0 leading-relaxed" {...props} />,
                          a: ({ node, ...props }) => <a className="text-blue-600 dark:text-blue-400 hover:underline break-words" target="_blank" rel="noopener noreferrer" {...props} />,
                          blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 py-1 italic text-gray-600 dark:text-gray-400 my-4 bg-gray-50 dark:bg-gray-800/50 rounded-r-lg" {...props} />,
                          
                          // จัดฟอร์แมตตาราง
                          table: ({ node, ...props }) => (
                            <div className="overflow-x-auto my-4 rounded-lg border border-gray-200 dark:border-gray-700">
                              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700" {...props} />
                            </div>
                          ),
                          thead: ({ node, ...props }) => <thead className="bg-gray-50 dark:bg-gray-800" {...props} />,
                          th: ({ node, ...props }) => <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100" {...props} />,
                          td: ({ node, ...props }) => <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 border-t border-gray-200 dark:border-gray-700" {...props} />,
                          
                          // จัดฟอร์แมตโค้ด
                          code({ node, inline, className, children, ...props }) {
                            const match = /language-(\w+)/.exec(className || '');
                            return !inline && match ? (
                              <div className="rounded-lg overflow-hidden my-4 bg-[#1E1E1E] shadow-sm border border-gray-700 max-w-full">
                                <div className="flex items-center px-4 py-1.5 bg-gray-800 border-b border-gray-700">
                                  <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">{match[1]}</span>
                                </div>
                                <div className="overflow-x-auto">
                                  <SyntaxHighlighter
                                    {...props}
                                    children={String(children).replace(/\n$/, '')}
                                    style={vscDarkPlus}
                                    language={match[1]}
                                    PreTag="div"
                                    className="!m-0 !bg-transparent text-sm"
                                    showLineNumbers={true}
                                  />
                                </div>
                              </div>
                            ) : (
                              <code {...props} className="bg-gray-100 dark:bg-gray-800 text-pink-600 dark:text-pink-400 px-1.5 py-0.5 rounded-md font-mono text-[0.9em] border border-gray-200 dark:border-gray-700 break-words">
                                {children}
                              </code>
                            );
                          },
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