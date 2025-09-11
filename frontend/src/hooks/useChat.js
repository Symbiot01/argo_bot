// // File: src/hooks/useChat.js
// 'use client';
// import { jwtDecode } from 'jwt-decode';
// import { useState } from 'react';

// export const useChat = (session) => {
//   const [messages, setMessages] = useState([]);
//   const [isThinking, setIsThinking] = useState(false);
//   const [chatId, setChatId] = useState(null);

//   // This is your defined fallback object.
//   const apiErrorFallback = {
//     sender: 'ai',
//     text: "The API is currently unavailable. Please try again later. This is a fallback message.",
//     imageUrl: null,
//   };

//   const processQueryWithPipeline = async (currentChatId, text) => {
//     try {
//       const response = await fetch('/api/chat/pipeline', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//           'Authorization': `Bearer ${session.accessToken}`,
//         },
//         body: JSON.stringify({
//           user_input: text,
//           chat_id: currentChatId,
//           user_id: jwtDecode(session.accessToken),
//           include_visualization: true,
//         }),
//       });

//       if (!response.ok) {
//         throw new Error(`Pipeline API Error: ${response.statusText}`);
//       }

//       const data = await response.json();
//       setMessages(prev => [
//         ...prev,
//         {
//           sender: 'ai',
//           text: data.response,
//           imageUrl: data.visualization_created ? data.visualization_url : null,
//         },
//       ]);
//     } catch (error) {
//       console.error("Failed to process pipeline query:", error);
//       // CORRECTED: Use the structured fallback object on failure.
//       setMessages(prev => [...prev, apiErrorFallback]);
//     }
//   };

//   const sendMessage = async (text) => {
//     setMessages(prev => [...prev, { sender: 'user', text }]);
//     setIsThinking(true);

//     try {
//       if (!chatId) {
//         // --- FIRST MESSAGE LOGIC ---

//         // 1. Get user data from sessionStorage
//         const storedSessionString = sessionStorage.getItem('user-session');
//         if (!storedSessionString) {
//           throw new Error("Session not found in storage. Please log in again.");
//         }
//         const storedSession = JSON.parse(storedSessionString);
//         const userId = storedSession.user.name; // Get the userid (username)
//         console.log("Creating new chat for user:", userId);
//         console.log(session.accessToken);
//         console.log(jwtDecode(session.accessToken));
//         console.log("New chat description:", text);

//         // 2. Create a new chat using the retrieved userid        
//         const newChatRes = await fetch('/api/chat/new', {
//           method: 'POST',
//           headers: {
//             'Content-Type': 'application/json',
//             'Authorization': `Bearer ${session.accessToken}`,
//           },
//           body: JSON.stringify({
//             userid: userId,
//             description: text,
//           }),
//         });
//         if(newChatRes.ok) console.log("New chat created successfully.");
//         if (!newChatRes.ok) throw new Error('Failed to create new chat.');

//         const newChatData = await newChatRes.json();
//         const newChatToken = newChatData.chat_token;
//         setChatId(newChatToken);
//         await processQueryWithPipeline(newChatToken, text);
//       } else {
//         await processQueryWithPipeline(chatId, text);
//       }
//     } catch (error) {
//       console.error("Failed to send message:", error);
//       // CORRECTED: Use the structured fallback object on failure.
//       setMessages(prev => [...prev, apiErrorFallback]);
//     } finally {
//       setIsThinking(false);
//     }
//   };

//   return { messages, isThinking, sendMessage };
// };

'use client';
import { useState } from 'react';

export const useChat = (session) => {
  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);

  // --- NEW, ENHANCED FALLBACK OBJECT ---
  const apiErrorFallback = {
    sender: 'ai',
    // 1. Markdown formatted text for a richer display
    text: `### 🚨 API Connection Error\n\nI was unable to connect to the backend services. Please check the server status and try your request again in a few moments.\n\n**Possible Actions:**\n* Verify your internet connection.\n* Check the official [Service Status Page](https://status.example.com).\n* If the issue persists, please contact support.\n\n*This is a fallback message.*`,
    // 2. A placeholder image to visually indicate an error
    imageUrl: 'https://placehold.co/3000x1400/f87171/ffffff?text=Service+Unavailable',
  };

  const sendMessage = async (text) => {
    setMessages(prev => [...prev, { sender: 'user', text }]);
    setIsThinking(true);

    try {
      const tempChatId = "temp-chat-session-123";
      
      // 3. CRITICAL FIX: The user ID from the session is required by the backend.
      const tempUserId = session.user.name; 

      const response = await fetch('/api/chat/pipeline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 4. CRITICAL FIX: The Authorization header is required for protected routes.
          'Authorization': `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify({
          user_input: text,
          chat_id: tempChatId,
          user_id: tempUserId, // Added user_id back in
          include_visualization: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("API Error Details:", errorData);
        throw new Error(`Pipeline API Error: ${response.statusText}`);
      }

      const data = await response.json();
      setMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          text: data.response,
          imageUrl: data.visualization_created ? data.visualization_url : null,
        },
      ]);

    } catch (error) {
      console.error("Failed to send message:", error);
      // The enhanced fallback object will be used here on any error
      setMessages(prev => [...prev, apiErrorFallback]);
    } finally {
      setIsThinking(false);
    }
  };

  return { messages, isThinking, sendMessage };
};