import React, { useState, useRef } from "react";
import { chatAPI } from "../services/api"; // ✅ your axios API

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage.trim(),
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);
    setError(null);

    try {
      // ✅ Use your axios-based chatAPI
      const { data } = await chatAPI.sendMessage(userMessage.text);

      const aiMessage = {
        id: Date.now() + 1,
        text: data.message,
        sender: "ai",
        timestamp: new Date(),
        error: data.error,
      };

      setMessages((prev) => [...prev, aiMessage]);

      if (data.error) {
        setError(data.message);
      }
    } catch (err) {
      console.error("Chat error:", err);

      const errorMessage = {
        id: Date.now() + 1,
        text: "⚠️ Unable to connect to the server. Please try again.",
        sender: "ai",
        timestamp: new Date(),
        error: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
      setError(errorMessage.text);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !isLoading) {
      sendMessage();
    }
  };

  return (
    <div className="chat-container">

      {/* Messages */}
      <div className="messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message ${
              msg.sender === "user" ? "user" : "ai"
            } ${msg.error ? "error" : ""}`}
          >
            <p>{msg.text}</p>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="chat-input">
        <input
          type="text"
          ref={inputRef}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Type your message..."
        />

        <button onClick={sendMessage} disabled={isLoading}>
          {isLoading ? "Sending..." : "Send"}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}
    </div>
  );
};

export default Chat;
