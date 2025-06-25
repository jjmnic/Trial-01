import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Send, Bot, User, BarChart3, FileText, Loader2 } from 'lucide-react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'Hello! I\'m your NIC Water & Sanitation Assistant. I can help you with information about Jal Jeevan Mission, Swachh Bharat Mission, DDWS programs, and provide data visualizations from scheme databases. How can I assist you today?',
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const scrollAreaRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: inputMessage,
      timestamp: new Date()
    }

    setMessages(prevMessages => [...prevMessages, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const resp = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: inputMessage } )
      })

      if (!resp.ok) {
        throw new Error(`HTTP error! status: ${resp.status}`)
      }

      const data = await resp.json()

      let assistantMessage = {
          id: Date.now() + 1,
          sender: 'bot',
          text: data.answer || 'Sorry, I could not get a clear answer.',
          timestamp: new Date(),
          visualization: data.visualization || null,
          type: data.type || 'text'
      };

      setMessages(prevMessages => [...prevMessages, assistantMessage])

    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'bot',
        text: 'Sorry, I\'m having trouble connecting to the server or processing your request. Please make sure the backend is running and try again.',
        timestamp: new Date()
      }
      setMessages(prevMessages => [...prevMessages, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm py-4 px-6 flex items-center justify-center">
        <div className="flex items-center space-x-3">
          <Bot className="h-8 w-8 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">NIC Water & Sanitation Assistant</h1>
        </div>
      </header>

      <div className="flex-1 overflow-hidden flex flex-col items-center p-6">
        <Card className="w-full max-w-3xl h-full flex flex-col">
          <CardHeader className="flex flex-col items-center text-center pb-4">
            <CardTitle className="text-xl font-semibold text-gray-800 dark:text-gray-200">Your intelligent assistant for Jal Jeevan Mission, Swachh Bharat Mission, and DDWS information</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden p-0">
            <ScrollArea className="h-full p-4" viewportRef={scrollAreaRef}>
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`flex items-start space-x-3 max-w-[70%] p-3 rounded-lg shadow-md ${message.sender === 'user'
                          ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-900 dark:bg-gray-700 dark:text-gray-100'}`}
                    >
                      {message.sender === 'bot' && <Bot className="h-5 w-5 flex-shrink-0" />}
                      {message.sender === 'user' && <User className="h-5 w-5 flex-shrink-0" />}
                      <div className="flex-1">
                        {message.text && <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>}
                        {message.visualization && (
                            <div className="visualization-container mt-3">
                                <img 
                                  src={message.visualization} 
                                  alt="Data Visualization" 
                                  className="max-w-full h-auto rounded-lg border border-gray-300 shadow-sm"
                                  style={{ maxHeight: '400px', objectFit: 'contain' }}
                                />
                            </div>
                        )}
                        {message.type && message.type !== 'text' && (
                          <Badge
                            className={`mt-2 ${message.type === 'knowledge' ? 'bg-green-500' : 
                              message.type === 'visualization' ? 'bg-purple-500' : 'bg-blue-500'}
                                text-white px-2 py-1 rounded-full text-xs font-medium`}
                          >
                            {message.type === 'knowledge' ? (
                              <FileText className="h-3 w-3 mr-1" />
                            ) : (
                              <BarChart3 className="h-3 w-3 mr-1" />
                            )}
                            {message.type === 'knowledge' ? 'Knowledge' : 
                             message.type === 'visualization' ? 'Visualization' : 'Data'}
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs mt-auto ml-2 opacity-75">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
          </CardContent>
          <CardContent className="p-4 border-t bg-white dark:bg-gray-800">
            <div className="flex gap-2">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about water & sanitation programs, or request data visualizations..."
                className="flex-1"
                disabled={isLoading}
              />
              <Button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-6 text-sm text-gray-600 dark:text-gray-400">
          <p>
            Powered by NIC's in-house APIs | For official information, visit{' '}
            <a
              href="https://jalshakti-ddws.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              jalshakti-ddws.gov.in
            </a>
          </p>
        </div>
      </div>
    </div>
   )
}

export default App

